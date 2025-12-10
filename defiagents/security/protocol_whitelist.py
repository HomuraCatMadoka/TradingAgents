from __future__ import annotations

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Dict, List, Literal, Optional, TypedDict

from defiagents.dataflows.defi import coingecko, the_graph
from defiagents.dataflows.defi.defillama import _normalize_tvl, get_protocol_info
from defiagents.protocol_registry import PROTOCOL_REGISTRY, get_protocol
from defiagents.security.intent_extractor import IntentExtractor

logger = logging.getLogger(__name__)


class ProtocolMetrics(TypedDict, total=False):
    """协议评估指标"""

    tvl: Optional[float]
    audit_count: Optional[int]
    age_days: Optional[int]
    on_hardcoded_list: bool


class WhitelistResult(TypedDict):
    """白名单验证结果"""

    status: Literal["trusted", "unverified", "suspicious"]
    protocol_slug: str
    metrics: ProtocolMetrics
    confidence_score: float
    data_sources: List[str]
    reason: str


class ProtocolWhitelist:
    """协议白名单验证器"""

    CACHE_TTL_SECONDS = 300
    CACHE_SIZE = 256
    DATA_SOURCE_TIMEOUT = 10
    SCORE_RULES = {
        "tvl_threshold": 100_000_000,
        "audit_threshold": 2,
        "age_threshold_days": 180,
        "min_score_for_trusted": 3,
    }
    HARDCODED_WHITELIST = {
        "aave-v3",
        "uniswap-v3",
        "compound-v3",
        "makerdao",
        "curve-dex",
        "lido",
        "rocket-pool",
        "yearn-finance",
        "balancer",
        "sushiswap",
        "pancakeswap",
        "frax",
        "gmx",
        "pendle",
        "beefy",
    }

    def __init__(
        self,
        trusted_protocols: Optional[List[str]] = None,
        cache_ttl: Optional[int] = None,
    ) -> None:
        self.cache_ttl = cache_ttl or self.CACHE_TTL_SECONDS
        self.trusted_protocols = set(self.HARDCODED_WHITELIST)
        if trusted_protocols:
            self.trusted_protocols.update(p.lower() for p in trusted_protocols)

        # Data source callables (allow monkeypatching for tests)
        self._defillama_get_protocol = get_protocol_info
        self._coingecko_get_market_data = coingecko.get_token_market_data
        self._graph_query = the_graph.query_subgraph

        # Reuse existing normalization map
        self._alias_map = IntentExtractor().protocol_map

    def _current_window(self) -> int:
        return int(time.time() // self.cache_ttl)

    @classmethod
    def clear_cache(cls) -> None:
        cls._cached_check.cache_clear()  # type: ignore[attr-defined]

    @lru_cache(maxsize=CACHE_SIZE)
    def _cached_check(
        self,
        slug: str,
        chain: Optional[str],
        window: int,
    ) -> WhitelistResult:
        return self._check_uncached(slug, chain)

    def check(self, slug_or_name: Optional[str], chain: Optional[str] = None) -> WhitelistResult:
        """验证协议可信度"""
        if not slug_or_name or not str(slug_or_name).strip():
            metrics: ProtocolMetrics = {
                "tvl": None,
                "audit_count": None,
                "age_days": None,
                "on_hardcoded_list": False,
            }
            return {
                "status": "unverified",
                "protocol_slug": "",
                "metrics": metrics,
                "confidence_score": 0.0,
                "data_sources": [],
                "reason": "empty protocol name",
            }

        slug = self._normalize_slug(slug_or_name)
        return self._cached_check(slug, chain, self._current_window())

    def is_trusted(self, slug_or_name: str, chain: Optional[str] = None) -> bool:
        """快捷判断是否可信"""
        return self.check(slug_or_name, chain)["status"] == "trusted"

    def _check_uncached(self, slug: str, chain: Optional[str]) -> WhitelistResult:
        on_whitelist = slug in self.trusted_protocols
        base_metrics: ProtocolMetrics = {
            "tvl": None,
            "audit_count": None,
            "age_days": None,
            "on_hardcoded_list": on_whitelist,
        }

        if on_whitelist:
            return {
                "status": "trusted",
                "protocol_slug": slug,
                "metrics": base_metrics,
                "confidence_score": 1.0,
                "data_sources": [],
                "reason": "hardcoded whitelist",
            }

        metrics, data_sources = self._fetch_metrics_parallel(slug, chain)
        metrics["on_hardcoded_list"] = on_whitelist

        if not data_sources:
            return {
                "status": "unverified",
                "protocol_slug": slug,
                "metrics": metrics,
                "confidence_score": 0.0,
                "data_sources": [],
                "reason": "all data sources failed",
            }

        status = self._compute_trust_level(metrics)
        confidence = self._compute_confidence(metrics, data_sources)
        reason = self._build_reason(status, metrics)

        return {
            "status": status,
            "protocol_slug": slug,
            "metrics": metrics,
            "confidence_score": confidence,
            "data_sources": data_sources,
            "reason": reason,
        }

    def _normalize_slug(self, slug_or_name: str) -> str:
        text = slug_or_name.strip().lower()
        cleaned = re.sub(r"[^a-z0-9\s_-]", " ", text)
        cleaned = re.sub(r"[\s_]+", "-", cleaned).strip("-")

        alias = self._alias_map.get(cleaned) or self._alias_map.get(text)
        if alias:
            return alias

        compact = cleaned.replace("-", "")
        for key, value in self._alias_map.items():
            if key.replace("-", "") == compact:
                return value

        if cleaned in PROTOCOL_REGISTRY or cleaned in self.trusted_protocols:
            return cleaned

        config = get_protocol(cleaned)
        if config:
            return config.slug

        for slug, cfg in PROTOCOL_REGISTRY.items():
            if cfg.name.lower().replace(" ", "-") == cleaned:
                return slug

        return cleaned

    def _fetch_metrics_parallel(
        self,
        slug: str,
        chain: Optional[str],
    ) -> tuple[ProtocolMetrics, List[str]]:
        metrics: ProtocolMetrics = {
            "tvl": None,
            "audit_count": None,
            "age_days": None,
            "on_hardcoded_list": False,
        }
        results: Dict[str, Any] = {}
        data_sources: List[str] = []

        defillama_future = None
        coingecko_future = None
        graph_future = None

        with ThreadPoolExecutor(max_workers=3) as executor:
            defillama_future = executor.submit(self._fetch_from_defillama, slug)
            coingecko_future = executor.submit(self._fetch_from_coingecko, slug)
            subgraph_id = self._get_subgraph_id(slug, chain)
            if subgraph_id:
                graph_future = executor.submit(self._fetch_from_the_graph, subgraph_id)

            futures = {
                defillama_future: "defillama",
                coingecko_future: "coingecko",
            }
            if graph_future:
                futures[graph_future] = "the_graph"

            try:
                for future in as_completed(futures, timeout=self.DATA_SOURCE_TIMEOUT):
                    source = futures[future]
                    try:
                        results[source] = future.result(timeout=self.DATA_SOURCE_TIMEOUT)
                    except TimeoutError:
                        logger.warning("Data source %s timed out", source)
                    except Exception as exc:  # pragma: no cover - logged for debugging
                        logger.warning("Data source %s failed: %s", source, exc)
            except TimeoutError:
                logger.warning("Timed out waiting for data sources")

            for future in futures:
                if not future.done():
                    future.cancel()

        # Priority: DeFi Llama > CoinGecko > The Graph
        if isinstance(results.get("defillama"), dict):
            data_sources.append("defillama")
            llama = results["defillama"]
            metrics["tvl"] = llama.get("tvl", metrics["tvl"])
            metrics["audit_count"] = llama.get("audit_count", metrics["audit_count"])
            metrics["age_days"] = llama.get("age_days", metrics["age_days"])

        if isinstance(results.get("coingecko"), dict):
            data_sources.append("coingecko")
            cg = results["coingecko"]
            metrics["tvl"] = metrics["tvl"] if metrics["tvl"] is not None else cg.get("tvl")
            metrics["audit_count"] = metrics["audit_count"] or cg.get("audit_count")
            metrics["age_days"] = metrics["age_days"] or cg.get("age_days")

        if results.get("the_graph"):
            data_sources.append("the_graph")

        return metrics, data_sources

    def _fetch_from_defillama(self, slug: str) -> Dict[str, Any]:
        data = self._defillama_get_protocol(slug)
        tvl = _normalize_tvl(data.get("tvl", 0))

        audits = data.get("audit_count", data.get("audits"))
        audit_count = 0
        if isinstance(audits, int):
            audit_count = audits
        elif isinstance(audits, list):
            audit_count = len(audits)

        listed_at = data.get("listedAt") or data.get("createdAt")
        age_days = self._age_from_timestamp(listed_at)

        return {"tvl": tvl, "audit_count": audit_count, "age_days": age_days}

    def _fetch_from_coingecko(self, slug: str) -> Dict[str, Any]:
        data = self._coingecko_get_market_data(slug)
        market_data = data.get("market_data", {})
        tvl = None
        if isinstance(market_data, dict):
            market_cap = market_data.get("market_cap", {})
            if isinstance(market_cap, dict):
                tvl = market_cap.get("usd")

        audit_count = data.get("audit_count")

        genesis_date = data.get("genesis_date")
        age_days = self._age_from_date(genesis_date)

        return {"tvl": tvl, "audit_count": audit_count, "age_days": age_days}

    def _fetch_from_the_graph(self, subgraph_id: str) -> bool:
        query = "query Health { _meta { block { number } } }"
        result = self._graph_query(subgraph_id, query)
        return bool(result)

    def _get_subgraph_id(self, slug: str, chain: Optional[str]) -> Optional[str]:
        config = get_protocol(slug)
        if not config:
            return None
        if chain and chain in config.subgraphs:
            return config.subgraphs[chain]
        if config.subgraphs:
            return next(iter(config.subgraphs.values()))
        return None

    def _age_from_timestamp(self, ts: Any) -> Optional[int]:
        if not ts:
            return None
        try:
            now = time.time()
            return max(0, int((now - float(ts)) / 86400))
        except (ValueError, TypeError):
            return None

    def _age_from_date(self, date_str: Any) -> Optional[int]:
        if not date_str:
            return None
        try:
            dt = datetime.strptime(str(date_str), "%Y-%m-%d").replace(tzinfo=timezone.utc)
            return max(0, int((datetime.now(timezone.utc) - dt).total_seconds() / 86400))
        except Exception:
            return None

    def _compute_trust_level(self, metrics: ProtocolMetrics) -> Literal["trusted", "unverified", "suspicious"]:
        tvl = metrics.get("tvl") or 0
        audit_count = metrics.get("audit_count") or 0
        age_days = metrics.get("age_days") or 0
        score = 0

        if tvl >= self.SCORE_RULES["tvl_threshold"]:
            score += 1
        if audit_count >= self.SCORE_RULES["audit_threshold"]:
            score += 1
        if age_days >= self.SCORE_RULES["age_threshold_days"]:
            score += 1
        if metrics.get("on_hardcoded_list"):
            score += 1

        if tvl and tvl < 10_000_000:
            return "suspicious"
        if score >= self.SCORE_RULES["min_score_for_trusted"]:
            return "trusted"
        if score >= 1:
            return "unverified"
        return "suspicious"

    def _compute_confidence(self, metrics: ProtocolMetrics, sources: List[str]) -> float:
        base = len(sources) / 3
        if metrics.get("on_hardcoded_list"):
            base += 0.5
        return round(min(1.0, max(0.0, base)), 2)

    def _build_reason(self, status: str, metrics: ProtocolMetrics) -> str:
        tvl = metrics.get("tvl")
        audit_count = metrics.get("audit_count")
        age_days = metrics.get("age_days")
        whitelist_flag = metrics.get("on_hardcoded_list", False)

        parts = [f"status={status}"]
        if tvl is not None:
            parts.append(f"tvl={tvl:,.0f}")
        if audit_count is not None:
            parts.append(f"audits={audit_count}")
        if age_days is not None:
            parts.append(f"age_days={age_days}")
        if whitelist_flag:
            parts.append("hardcoded=true")
        return "; ".join(parts)


__all__ = ["ProtocolWhitelist", "ProtocolMetrics", "WhitelistResult"]
