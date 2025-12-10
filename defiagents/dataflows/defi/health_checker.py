"""
Health checks for external DeFi data sources with TTL caching.

Checks run in parallel with a 5s timeout per source and are cached for
5-minute windows via an LRU keyed by the window id. Results are returned
as a mapping of source name to {source: status, latency: ms}.
"""

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, wait
from functools import lru_cache
from typing import Callable, Dict, Any

import requests

from defiagents.dataflows.defi.coingecko import CoinGeckoAPI

CHECK_TIMEOUT = 5  # seconds per data source
CACHE_TTL_SECONDS = 300  # 5 minutes

_DEFILLAMA_HEALTH_URL = "https://api.llama.fi/protocols"
_THE_GRAPH_HEALTH_URL = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
_THE_GRAPH_HEALTH_QUERY = "query Health { pools(first: 1) { id } }"

_ALLOWED_STATUSES = {"online", "offline", "degraded"}


def _normalize_status(status: str) -> str:
    """Ensure status is one of the allowed values."""
    if status in _ALLOWED_STATUSES:
        return status
    return "degraded"


def _current_window_id(now: float | None = None) -> int:
    """Return the current cache window id (5 minute buckets)."""
    ts = now if now is not None else time.time()
    return int(ts // CACHE_TTL_SECONDS)


def _check_defillama() -> str:
    """Check DeFi Llama by hitting the /protocols endpoint."""
    response = requests.get(_DEFILLAMA_HEALTH_URL, timeout=CHECK_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, list) and data:
        return "online"
    return "degraded"


def _check_the_graph() -> str:
    """Check The Graph via a lightweight pool query."""
    response = requests.post(
        _THE_GRAPH_HEALTH_URL,
        json={"query": _THE_GRAPH_HEALTH_QUERY},
        timeout=CHECK_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    pools = data.get("data", {}).get("pools")
    if isinstance(pools, list):
        return "online" if pools else "degraded"
    return "degraded"


def _check_coingecko() -> str:
    """Check CoinGecko using the existing ping method."""
    api = CoinGeckoAPI()
    data = api.ping()
    return "online" if data else "degraded"


def _check_gemini_configuration() -> str:
    """Check Gemini configuration by verifying the API key is set."""
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    return "online" if api_key else "offline"


DEFAULT_CHECKERS: Dict[str, Callable[[], str]] = {
    "defillama": _check_defillama,
    "the_graph": _check_the_graph,
    "coingecko": _check_coingecko,
    "gemini": _check_gemini_configuration,
}


def _execute_check(check_fn: Callable[[], str]) -> tuple[str, int]:
    """Run a single check and return status with latency in ms."""
    start = time.perf_counter()
    try:
        status = _normalize_status(check_fn())
    except Exception:
        status = "offline"
    latency = int((time.perf_counter() - start) * 1000)
    return status, latency


def _run_checks(checkers: Dict[str, Callable[[], str]] | None = None) -> Dict[str, Dict[str, Any]]:
    """Run all checks in parallel with per-source timeout."""
    checks = checkers or DEFAULT_CHECKERS
    results: Dict[str, Dict[str, Any]] = {}
    timeout_latency = int(CHECK_TIMEOUT * 1000)

    with ThreadPoolExecutor(max_workers=len(checks)) as executor:
        future_map = {executor.submit(_execute_check, fn): name for name, fn in checks.items()}
        done, not_done = wait(future_map.keys(), timeout=CHECK_TIMEOUT)

        for future in done:
            status, latency = future.result()
            results[future_map[future]] = {"source": status, "latency": latency}

        for future in not_done:
            future.cancel()
            results[future_map[future]] = {"source": "offline", "latency": timeout_latency}

    return results


@lru_cache(maxsize=1)
def _cached_health(window_id: int) -> Dict[str, Dict[str, Any]]:
    """Cached health results keyed by window id."""
    return _run_checks()


def clear_health_cache() -> None:
    """Clear the cached health results."""
    _cached_health.cache_clear()


def get_health_status(force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Get health status for all data sources.

    Args:
        force_refresh: If True, bypass cache and recompute.

    Returns:
        Mapping of source name to status/latency.
    """
    if force_refresh:
        clear_health_cache()
    return _cached_health(_current_window_id())


def get_system_health(force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    """Alias for get_health_status kept for backwards compatibility."""
    return get_health_status(force_refresh=force_refresh)


__all__ = [
    "get_health_status",
    "get_system_health",
    "clear_health_cache",
    "_check_defillama",
    "_check_the_graph",
    "_check_coingecko",
    "_check_gemini_configuration",
]
