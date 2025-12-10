"""
Messari Subgraph Gateway 客户端。

特性：
- 从本地 deployment.json 加载 deployment ID（协议 + 链 → deployment_id）
- 内置 1 小时 TTL 内存缓存
- 统一错误分类：API 错误 / 限流 / 未找到
- 提供常用查询：TVL、借贷市场、DEX 池、协议聚合指标
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

from defiagents.dataflows.defi import messari_schemas as schemas

logger = logging.getLogger(__name__)


class MessariAPIError(Exception):
    """Messari API 通用错误。"""


class MessariRateLimitError(MessariAPIError):
    """API 429 限流错误。"""


class MessariNotFoundError(MessariAPIError):
    """资源不存在或未找到 deployment。"""


DEFAULT_ENDPOINT = "https://gateway.thegraph.com/api"
DEFAULT_CACHE_TTL = 3600  # 1 hour


def _normalize_chain(chain: str) -> str:
    chain_lc = (chain or "").strip().lower()
    if chain_lc in {"mainnet", "ethereum"}:
        return "ethereum"
    if chain_lc in {"matic", "polygon"}:
        return "polygon"
    return chain_lc


class MessariClient:
    """
    Messari Subgraph Gateway 客户端。

    参考 defiagents/dataflows/defi/the_graph.py 的缓存模式。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_ttl: int = DEFAULT_CACHE_TTL,
        deployment_json_path: Optional[str] = None,
        endpoint: str = DEFAULT_ENDPOINT,
    ):
        self.api_key = api_key or ""
        self.cache_ttl = cache_ttl
        self.endpoint = endpoint.rstrip("/")
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._deployments = self._load_deployments(deployment_json_path)

    # ========== Public APIs ==========

    def get_protocol_tvl(self, protocol_slug: str, chain: str = "ethereum") -> float:
        """获取协议 TVL。"""
        cache_key = self._build_cache_key(protocol_slug, chain, "tvl")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        schema_type, deployment_id = self._get_deployment_id(protocol_slug, chain)
        query, variables = schemas.build_tvl_query(schema_type, protocol_slug)
        data = self._query_api(deployment_id, query, variables)

        protocol_node = data.get("lendingProtocol") or data.get("dexAmmProtocol") or {}
        tvl = schemas.parse_tvl(protocol_node)
        self._set_cache(cache_key, tvl)
        return tvl

    def get_lending_markets(
        self, protocol_slug: str, chain: str = "ethereum"
    ) -> List[Dict[str, Any]]:
        """获取借贷市场列表。仅适用于 lending schema。"""
        cache_key = self._build_cache_key(protocol_slug, chain, "lending_markets")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        schema_type, deployment_id = self._get_deployment_id(protocol_slug, chain)
        if schema_type != schemas.LENDING_SCHEMA:
            raise MessariNotFoundError(f"协议 {protocol_slug} 非 lending schema，无法获取借贷市场")

        query, variables = schemas.build_lending_markets_query(protocol_slug)
        data = self._query_api(deployment_id, query, variables)
        protocol_node = data.get("lendingProtocol") or {}
        markets = schemas.parse_lending_markets(protocol_node)
        self._set_cache(cache_key, markets)
        return markets

    def get_dex_pools(
        self, protocol_slug: str, chain: str = "ethereum"
    ) -> List[Dict[str, Any]]:
        """获取 DEX 池子列表。仅适用于 dex-amm schema。"""
        cache_key = self._build_cache_key(protocol_slug, chain, "dex_pools")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        schema_type, deployment_id = self._get_deployment_id(protocol_slug, chain)
        if schema_type != schemas.DEX_AMM_SCHEMA:
            raise MessariNotFoundError(f"协议 {protocol_slug} 非 dex-amm schema，无法获取池子")

        query, variables = schemas.build_dex_pools_query(protocol_slug)
        data = self._query_api(deployment_id, query, variables)
        protocol_node = data.get("dexAmmProtocol") or {}
        pools = schemas.parse_dex_pools(protocol_node)
        self._set_cache(cache_key, pools)
        return pools

    def get_protocol_metrics(
        self, protocol_slug: str, chain: str = "ethereum"
    ) -> Dict[str, Any]:
        """获取协议聚合指标。"""
        cache_key = self._build_cache_key(protocol_slug, chain, "metrics")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        schema_type, deployment_id = self._get_deployment_id(protocol_slug, chain)
        query, variables = schemas.build_protocol_metrics_query(schema_type, protocol_slug)
        data = self._query_api(deployment_id, query, variables)

        protocol_node = data.get("lendingProtocol") or data.get("dexAmmProtocol") or {}
        metrics = schemas.parse_protocol_metrics(protocol_node)
        self._set_cache(cache_key, metrics)
        return metrics

    # ========== Internal helpers ==========

    def _get_cached(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if not entry:
            return None
        data, ts = entry
        if time.time() - ts < self.cache_ttl:
            logger.debug("Messari cache 命中: %s", key)
            return data
        logger.debug("Messari cache 过期: %s", key)
        self._cache.pop(key, None)
        return None

    def _set_cache(self, key: str, data: Any):
        self._cache[key] = (data, time.time())

    def _build_cache_key(self, protocol: str, chain: str, method: str) -> str:
        return f"messari:{protocol}:{_normalize_chain(chain)}:{method}"

    def _get_deployment_id(self, protocol_slug: str, chain: str) -> Tuple[str, str]:
        normalized_chain = _normalize_chain(chain)
        protocol_entry = self._deployments.get(protocol_slug)
        if not protocol_entry:
            raise MessariNotFoundError(f"未找到协议 {protocol_slug} 的 deployment 信息")

        deployment = protocol_entry["deployments"].get(normalized_chain)
        if not deployment:
            raise MessariNotFoundError(
                f"协议 {protocol_slug} 不支持链 {normalized_chain}"
            )

        return protocol_entry["schema"], deployment["deployment_id"]

    def _query_api(self, deployment_id: str, query: str, variables: Dict[str, Any]) -> Dict:
        url = f"{self.endpoint}/{deployment_id}"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        payload = {"query": query, "variables": variables}
        try:
            logger.info("Messari 请求: %s", url)
            response = requests.post(url, headers=headers, json=payload, timeout=10)
        except requests.RequestException as exc:
            raise MessariAPIError(f"网络错误: {exc}") from exc

        if response.status_code == 429:
            raise MessariRateLimitError("Messari API 限流 (429)")
        if response.status_code == 404:
            raise MessariNotFoundError("Messari API 返回 404")
        if not response.ok:
            raise MessariAPIError(f"Messari API 错误: {response.status_code}")

        try:
            data = response.json()
        except ValueError as exc:
            raise MessariAPIError("Messari API 返回非 JSON 响应") from exc

        if data.get("errors"):
            raise MessariAPIError(f"Messari GraphQL 错误: {data['errors']}")

        return data.get("data") or {}

    def _load_deployments(self, deployment_json_path: Optional[str]) -> Dict[str, Dict[str, Any]]:
        """
        加载 deployment.json，返回格式：
        { protocol_slug: {schema: str, deployments: {chain: {deployment_id}} } }
        """
        path = Path(deployment_json_path) if deployment_json_path else self._default_deployment_path()
        if not path.exists():
            raise MessariNotFoundError(f"deployment.json 不存在: {path}")

        try:
            with path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as exc:  # noqa: BLE001
            raise MessariAPIError(f"读取 deployment.json 失败: {exc}") from exc

        deployments: Dict[str, Dict[str, Any]] = {}
        for protocol_slug, meta in raw.items():
            schema_type = schemas.normalize_schema(meta.get("schema", ""))
            deployments[protocol_slug] = {"schema": schema_type, "deployments": {}}
            for dep_name, dep_info in (meta.get("deployments") or {}).items():
                chain = _normalize_chain(dep_info.get("network", ""))
                services = dep_info.get("services") or {}
                decentralized = services.get("decentralized-network") or {}
                deployment_id = decentralized.get("query-id")
                if not deployment_id or not chain:
                    continue
                deployments[protocol_slug]["deployments"][chain] = {
                    "deployment_id": deployment_id,
                    "name": dep_name,
                }
        return deployments

    def _default_deployment_path(self) -> Path:
        # 默认指向仓库根目录下的 subgraph/deployment/deployment.json
        current_dir = Path(__file__).resolve().parent
        return current_dir.parent.parent.parent / "subgraph" / "deployment" / "deployment.json"


# 便捷函数
_client_instance: Optional[MessariClient] = None


def get_client_instance() -> MessariClient:
    global _client_instance
    if _client_instance is None:
        api_key = ""
        try:
            from defiagents.dataflows.config import get_config

            config = get_config()
            api_key = config.get("messari", {}).get("api_key", "")
        except Exception as exc:  # noqa: BLE001
            logger.warning("加载 messari 配置失败，将使用默认设置: %s", exc)
        _client_instance = MessariClient(api_key=api_key)
    return _client_instance


def get_protocol_tvl(protocol_slug: str, chain: str = "ethereum") -> float:
    return get_client_instance().get_protocol_tvl(protocol_slug, chain)


def get_lending_markets(protocol_slug: str, chain: str = "ethereum") -> List[Dict[str, Any]]:
    return get_client_instance().get_lending_markets(protocol_slug, chain)


def get_dex_pools(protocol_slug: str, chain: str = "ethereum") -> List[Dict[str, Any]]:
    return get_client_instance().get_dex_pools(protocol_slug, chain)


def get_protocol_metrics(protocol_slug: str, chain: str = "ethereum") -> Dict[str, Any]:
    return get_client_instance().get_protocol_metrics(protocol_slug, chain)
