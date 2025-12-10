import time
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Sequence

from core.exceptions import DataSourceError, NotFoundError, ValidationError
from defiagents.dataflows.defi.coingecko import get_token_market_data, get_token_price
from defiagents.dataflows.defi.defillama import _normalize_tvl, get_all_protocols, get_protocol_info
from defiagents.dataflows.defi.the_graph import get_uniswap_pool_by_id, get_uniswap_pools


def _iso_timestamp(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


class DeFiDataService:
    """Synchronous DeFi data access with simple in-memory caching."""

    def __init__(
        self,
        *,
        get_protocols: Optional[Callable[[], Sequence[Dict[str, Any]]]] = None,
        get_protocol_detail: Optional[Callable[[str], Dict[str, Any]]] = None,
        fallback_protocol_detail: Optional[Callable[[str], Dict[str, Any]]] = None,
        fallback_protocols: Optional[Callable[[], Sequence[Dict[str, Any]]]] = None,
        get_uniswap_pools_fn: Optional[Callable[..., List[Dict[str, Any]]]] = None,
        get_uniswap_pool_fn: Optional[Callable[[str], Optional[Dict[str, Any]]]] = None,
        token_market_data_fn: Optional[Callable[[str], Dict[str, Any]]] = None,
        token_price_fn: Optional[Callable[[str], Dict[str, Any]]] = None,
        now: Callable[[], float] = time.time,
    ) -> None:
        self._get_protocols = get_protocols or get_all_protocols
        self._get_protocol_detail = get_protocol_detail or get_protocol_info
        self._fallback_protocol_detail = fallback_protocol_detail
        self._fallback_protocols = fallback_protocols
        self._get_uniswap_pools = get_uniswap_pools_fn or get_uniswap_pools
        self._get_uniswap_pool = get_uniswap_pool_fn or get_uniswap_pool_by_id
        self._get_token_market_data = token_market_data_fn or get_token_market_data
        self._get_token_price = token_price_fn or get_token_price
        self._now = now

    def clear_cache(self) -> None:
        self._cached_list_protocols.cache_clear()
        self._cached_protocol_detail.cache_clear()
        self._cached_protocol_history.cache_clear()
        self._cached_market_data.cache_clear()
        self._cached_protocol_pools.cache_clear()
        self._cached_pool_detail.cache_clear()

    def list_protocols(self, search: Optional[str] = None, chain: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        if limit <= 0:
            raise ValidationError("limit", "must be positive")
        return self._cached_list_protocols(search or "", chain or "", limit)

    @lru_cache(maxsize=256)
    def _cached_list_protocols(self, search: str, chain: str, limit: int) -> List[Dict[str, Any]]:
        protocols = self._fetch_protocols()
        filtered = self._filter_protocols(protocols, search or None, chain or None)
        return filtered[:limit]

    def get_protocol_detail(self, slug: str) -> Dict[str, Any]:
        if not slug:
            raise ValidationError("slug", "must not be empty")
        return self._cached_protocol_detail(slug)

    @lru_cache(maxsize=256)
    def _cached_protocol_detail(self, slug: str) -> Dict[str, Any]:
        raw = self._load_protocol(slug)
        return self._normalize_protocol_detail(raw, slug)

    def get_protocol_history(self, slug: str, days: int) -> List[Dict[str, Any]]:
        if days <= 0:
            raise ValidationError("period", "must be greater than zero")
        return self._cached_protocol_history(slug, days)

    @lru_cache(maxsize=256)
    def _cached_protocol_history(self, slug: str, days: int) -> List[Dict[str, Any]]:
        raw = self._load_protocol(slug)
        history_raw = raw.get("tvl") or raw.get("history") or raw.get("tvlHistory") or []
        return self._normalize_history(history_raw, days)

    def get_market_data(self, token_id: str) -> Dict[str, Any]:
        if not token_id:
            raise ValidationError("token_id", "must not be empty")
        return self._cached_market_data(token_id)

    @lru_cache(maxsize=256)
    def _cached_market_data(self, token_id: str) -> Dict[str, Any]:
        try:
            market_data = self._get_token_market_data(token_id)
        except Exception as exc:
            fallback = self._safe_price(token_id)
            if fallback is None:
                raise DataSourceError("CoinGecko", str(exc)) from exc
            return self._normalize_market_data(token_id, {}, fallback)

        fallback_price = None
        if not market_data or not market_data.get("market_data"):
            fallback_price = self._safe_price(token_id)

        return self._normalize_market_data(token_id, market_data or {}, fallback_price)

    def get_protocol_pools(self, slug: str, chain: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        if not slug.startswith("uniswap"):
            raise NotFoundError("Pools", slug)
        if limit <= 0:
            raise ValidationError("limit", "must be positive")
        return self._cached_protocol_pools(slug, chain or "", limit)

    @lru_cache(maxsize=128)
    def _cached_protocol_pools(self, slug: str, chain: str, limit: int) -> List[Dict[str, Any]]:
        try:
            pools = self._get_uniswap_pools(limit=limit)
        except Exception as exc:
            raise DataSourceError("The Graph", str(exc)) from exc
        return [self._normalize_pool_summary(pool) for pool in pools]

    def get_pool_detail(self, slug: str, pool_id: str) -> Dict[str, Any]:
        if not slug.startswith("uniswap"):
            raise NotFoundError("Pool", pool_id)
        return self._cached_pool_detail(pool_id)

    @lru_cache(maxsize=256)
    def _cached_pool_detail(self, pool_id: str) -> Dict[str, Any]:
        try:
            pool = self._get_uniswap_pool(pool_id)
        except Exception as exc:
            raise DataSourceError("The Graph", str(exc)) from exc

        if not pool:
            raise NotFoundError("Pool", pool_id)

        return self._normalize_pool_detail(pool)

    @staticmethod
    def parse_period(period: Optional[str], default_days: int = 30) -> int:
        if period is None:
            return default_days
        if isinstance(period, int):
            value = period
        else:
            trimmed = period.strip().lower()
            if trimmed.endswith("d"):
                trimmed = trimmed[:-1]
            if not trimmed.isdigit():
                raise ValidationError("period", "must be a positive day value like 7d or 30")
            value = int(trimmed)
        if value <= 0:
            raise ValidationError("period", "must be greater than zero")
        return value

    def _fetch_protocols(self) -> Sequence[Dict[str, Any]]:
        return self._with_fallback(self._get_protocols, self._fallback_protocols, "DeFi Llama", "The Graph")

    def _load_protocol(self, slug: str) -> Dict[str, Any]:
        return self._with_fallback(
            lambda: self._get_protocol_detail(slug),
            (lambda: self._fallback_protocol_detail(slug)) if self._fallback_protocol_detail else None,
            "DeFi Llama",
            "The Graph",
        )

    def _filter_protocols(
        self, protocols: Sequence[Dict[str, Any]], search: Optional[str], chain: Optional[str]
    ) -> List[Dict[str, Any]]:
        needle = search.lower() if search else None
        chain_filter = chain.lower() if chain else None
        items: List[Dict[str, Any]] = []

        for item in protocols:
            slug = item.get("slug") or (item.get("name") or "").lower().replace(" ", "-")
            name = item.get("name") or slug
            symbol = item.get("symbol")
            chains = item.get("chains") or []

            if needle and needle not in name.lower() and needle not in slug.lower():
                if symbol is None or needle not in str(symbol).lower():
                    continue
            if chain_filter and not any(str(c).lower() == chain_filter for c in chains):
                continue

            items.append(
                {
                    "slug": slug,
                    "name": name,
                    "symbol": symbol,
                    "category": item.get("category"),
                    "chains": chains,
                    "tvl": _normalize_tvl(item.get("tvl", 0)),
                }
            )

        items.sort(key=lambda entry: entry.get("tvl", 0) or 0, reverse=True)
        return items

    def _normalize_protocol_detail(self, raw: Dict[str, Any], slug: str) -> Dict[str, Any]:
        if not raw:
            raise DataSourceError("DeFi Llama", "empty protocol response")

        chain_tvls = {
            chain: _normalize_tvl(value) for chain, value in (raw.get("chainTvls") or {}).items()
        }

        return {
            "slug": slug,
            "name": raw.get("name") or slug,
            "symbol": raw.get("symbol") or raw.get("tokenSymbol"),
            "category": raw.get("category"),
            "chains": raw.get("chains") or [],
            "tvl": _normalize_tvl(raw.get("tvl", 0)),
            "chain_tvls": chain_tvls,
            "audits": raw.get("audits"),
            "url": raw.get("url") or raw.get("website"),
            "description": raw.get("description"),
            "last_updated": _iso_timestamp(self._now()),
        }

    def _normalize_history(self, history_raw: Sequence[Any], days: int) -> List[Dict[str, Any]]:
        cutoff = self._now() - days * 86400 if days else None
        normalized: List[Dict[str, Any]] = []

        for entry in history_raw:
            if not isinstance(entry, dict):
                continue
            ts = entry.get("date") or entry.get("timestamp")
            tvl_value = entry.get("totalLiquidityUSD") or entry.get("tvl")
            if ts is None or tvl_value is None:
                continue
            if cutoff and ts < cutoff:
                continue
            normalized.append({"timestamp": _iso_timestamp(float(ts)), "tvl": _normalize_tvl(tvl_value)})

        if not normalized:
            raise DataSourceError("DeFi Llama", "no historical data")

        normalized.sort(key=lambda row: row["timestamp"])
        return normalized

    def _normalize_market_data(
        self, token_id: str, market_data: Dict[str, Any], fallback_price: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        md = market_data.get("market_data", {}) if isinstance(market_data, dict) else {}
        price = (md.get("current_price") or {}).get("usd")
        market_cap = (md.get("market_cap") or {}).get("usd")
        volume = (md.get("total_volume") or {}).get("usd")
        change = md.get("price_change_percentage_24h")

        if price is None and fallback_price:
            price = fallback_price.get("usd")
            market_cap = fallback_price.get("usd_market_cap")
            volume = fallback_price.get("usd_24h_vol")
            change = fallback_price.get("usd_24h_change")

        if price is None:
            raise DataSourceError("CoinGecko", "missing price data")

        return {
            "id": market_data.get("id", token_id) if isinstance(market_data, dict) else token_id,
            "symbol": market_data.get("symbol") if isinstance(market_data, dict) else None,
            "name": market_data.get("name") if isinstance(market_data, dict) else None,
            "price": float(price),
            "market_cap": float(market_cap) if market_cap is not None else None,
            "volume_24h": float(volume) if volume is not None else None,
            "change_24h": float(change) if change is not None else None,
            "last_updated": market_data.get("last_updated") if isinstance(market_data, dict) else None,
        }

    def _normalize_pool_summary(self, pool: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": pool.get("id"),
            "token0": (pool.get("token0") or {}).get("symbol"),
            "token1": (pool.get("token1") or {}).get("symbol"),
            "tvl": _normalize_tvl(pool.get("totalValueLockedUSD", 0)),
            "volume": _normalize_tvl(pool.get("volumeUSD", 0)),
            "fee_tier": pool.get("feeTier"),
        }

    def _normalize_pool_detail(self, pool: Dict[str, Any]) -> Dict[str, Any]:
        day_data = pool.get("poolDayData") or []
        history = [
            {
                "date": _iso_timestamp(float(row["date"])),
                "tvl": _normalize_tvl(row.get("tvlUSD")),
                "volume": _normalize_tvl(row.get("volumeUSD")),
                "fees": _normalize_tvl(row.get("feesUSD")),
            }
            for row in day_data
            if "date" in row
        ]
        return {
            "id": pool.get("id"),
            "token0": pool.get("token0"),
            "token1": pool.get("token1"),
            "tvl": _normalize_tvl(pool.get("totalValueLockedUSD", 0)),
            "volume": _normalize_tvl(pool.get("volumeUSD", 0)),
            "fee_tier": pool.get("feeTier"),
            "history": history,
        }

    def _with_fallback(
        self,
        primary: Callable[[], Any],
        fallback: Optional[Callable[[], Any]],
        primary_source: str,
        fallback_source: str,
    ) -> Any:
        try:
            return primary()
        except Exception as primary_error:
            if not fallback:
                raise DataSourceError(primary_source, str(primary_error)) from primary_error
            try:
                return fallback()
            except Exception as fallback_error:
                message = f"{primary_source} failed ({primary_error}); {fallback_source} failed ({fallback_error})"
                raise DataSourceError(fallback_source, message) from fallback_error

    def _safe_price(self, token_id: str) -> Optional[Dict[str, Any]]:
        try:
            return self._get_token_price(token_id)
        except Exception:
            return None
