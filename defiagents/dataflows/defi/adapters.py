"""
多源数据格式适配器。

提供 Messari / DeFi Llama / The Graph 的统一格式转换，避免上层逻辑处理异构字段。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from defiagents.dataflows.interface import DataSourceType
from defiagents.dataflows.defi.defillama import _normalize_tvl as _defillama_normalize_tvl

logger = logging.getLogger(__name__)


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _first_present(data: Dict[str, Any], keys: List[str]) -> Any:
    for key in keys:
        if key in data and data.get(key) is not None:
            return data.get(key)
    return None


def _extract_symbol(token: Any) -> str:
    if isinstance(token, dict):
        return str(token.get("symbol") or token.get("name") or token.get("id") or "")
    if token is None:
        return ""
    return str(token)


def _pick_rate(rates: Any, side: str) -> float:
    for rate in rates or []:
        if not isinstance(rate, dict):
            continue
        if rate.get("side", "").upper() == side.upper():
            return _to_float(rate.get("rate"))
    return 0.0


class DataAdapter:
    """统一数据格式转换入口。"""

    @staticmethod
    def normalize_tvl(data: Any, source: DataSourceType) -> float:
        if source == DataSourceType.MESSARI:
            if isinstance(data, (int, float)):
                return float(data)
            if isinstance(data, dict):
                node = data.get("protocol") if "protocol" in data else data
                if "totalValueLockedUSD" in node:
                    return _to_float(node.get("totalValueLockedUSD"))
            return _to_float(data)

        if source == DataSourceType.DEFILLAMA:
            return _to_float(_defillama_normalize_tvl(data))

        if source == DataSourceType.THE_GRAPH:
            if isinstance(data, dict):
                snapshots = data.get("financialsDailySnapshots") or data.get("snapshots") or []
                if snapshots:
                    return _to_float((snapshots[-1] or {}).get("totalValueLockedUSD"))
                candidate = _first_present(
                    data, ["totalValueLockedUSD", "tvl", "tvlUSD", "tvlUsd"]
                )
                return _to_float(candidate)
            return _to_float(data)

        return _to_float(data)

    @staticmethod
    def normalize_lending_markets(data: Any, source: DataSourceType) -> List[Dict[str, Any]]:
        if isinstance(data, dict):
            markets = data.get("markets") or data.get("lendingMarkets") or []
        elif isinstance(data, list):
            markets = data
        else:
            markets = []

        normalized: List[Dict[str, Any]] = []
        for market in markets:
            if not isinstance(market, dict):
                continue

            rates = market.get("rates") or []
            supply_rate = _pick_rate(rates, "LENDER")
            borrow_rate = _pick_rate(rates, "BORROWER")

            # 兼容直接字段形式
            if supply_rate == 0.0:
                supply_rate = _to_float(_first_present(market, ["supply_rate", "supplyRate"]))
            if borrow_rate == 0.0:
                borrow_rate = _to_float(_first_present(market, ["borrow_rate", "borrowRate"]))

            input_token = _first_present(market, ["input_token", "inputToken", "asset"])
            normalized.append(
                {
                    "id": _first_present(market, ["id", "marketId"]) or "",
                    "asset": _extract_symbol(input_token),
                    "tvl_usd": _to_float(
                        _first_present(
                            market,
                            ["tvl_usd", "totalValueLockedUSD", "tvlUSD", "totalLiquidityUSD"],
                        )
                    ),
                    "total_deposit_usd": _to_float(
                        _first_present(market, ["total_deposit_usd", "totalDepositBalanceUSD"])
                    ),
                    "total_borrow_usd": _to_float(
                        _first_present(market, ["total_borrow_usd", "totalBorrowBalanceUSD"])
                    ),
                    "supply_rate": supply_rate,
                    "borrow_rate": borrow_rate,
                }
            )
        return normalized

    @staticmethod
    def normalize_dex_pools(data: Any, source: DataSourceType) -> List[Dict[str, Any]]:
        if isinstance(data, dict):
            pools = data.get("pools") or []
        elif isinstance(data, list):
            pools = data
        else:
            pools = []

        normalized: List[Dict[str, Any]] = []
        for pool in pools:
            if not isinstance(pool, dict):
                continue

            raw_tokens = _first_present(pool, ["input_tokens", "inputTokens", "tokens"]) or []
            token_symbols = []
            for token in raw_tokens:
                if isinstance(token, dict) and "token" in token:
                    token_symbols.append(_extract_symbol(token.get("token")))
                else:
                    token_symbols.append(_extract_symbol(token))

            # Graph 常见 token0/token1
            for key in ("token0", "token1"):
                if key in pool:
                    token_symbols.append(_extract_symbol(pool.get(key)))

            normalized.append(
                {
                    "id": _first_present(pool, ["id", "poolId"]) or "",
                    "name": _first_present(pool, ["name"]) or "",
                    "tvl_usd": _to_float(
                        _first_present(
                            pool,
                            [
                                "tvl_usd",
                                "totalValueLockedUSD",
                                "tvlUSD",
                                "tvlUsd",
                                "totalLiquidityUSD",
                            ],
                        )
                    ),
                    "volume_usd": _to_float(
                        _first_present(pool, ["cumulativeVolumeUSD", "volumeUSD", "volume_usd"])
                    ),
                    "fees_usd": _to_float(
                        _first_present(pool, ["feesUSD", "totalFeesUSD", "fees_usd"])
                    ),
                    "token_symbols": [sym for sym in token_symbols if sym],
                }
            )

        return normalized
