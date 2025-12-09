"""
Curve Finance Official API Integration

Official API documentation is limited, but the API provides more accurate and real-time
data compared to The Graph subgraphs for Curve.

API Base URL: https://api.curve.fi/api
Main endpoints:
- /getPools/{chain} - Get all pools for a chain
- /getVolume/{chain}/{poolAddress} - Get volume data
- /getSubgraphData/{chain} - Get subgraph-like data

Note: Curve's official API is recommended over The Graph subgraphs for accuracy.
"""

from typing import Dict, List, Optional, Any
import requests
from functools import lru_cache
import time


class CurveAPI:
    """Client for Curve Finance official API"""

    BASE_URL = "https://api.curve.fi/api"

    # Chain name mappings (Curve uses different chain names)
    CHAIN_MAPPINGS = {
        "ethereum": "ethereum",
        "arbitrum": "arbitrum",
        "optimism": "optimism",
        "polygon": "polygon",
        "avalanche": "avalanche",
        "fantom": "fantom",
        "xdai": "xdai",
        "gnosis": "xdai",  # Curve uses "xdai" for Gnosis Chain
    }

    def __init__(self, timeout: int = 30):
        """
        Initialize Curve API client.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes cache

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """
        Make HTTP request to Curve API with caching.

        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters

        Returns:
            Parsed JSON response
        """
        cache_key = f"{endpoint}:{str(params)}"
        now = time.time()

        # Check cache
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if now - cached_time < self._cache_ttl:
                return cached_data

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            # Cache the result
            self._cache[cache_key] = (data, now)
            return data

        except requests.exceptions.RequestException as e:
            raise Exception(f"Curve API request failed: {e}")

    def get_pools(self, chain: str = "ethereum") -> Dict[str, Any]:
        """
        Get all Curve pools on a specific chain.

        Args:
            chain: Blockchain name (ethereum, arbitrum, optimism, polygon, etc.)

        Returns:
            Dictionary with pool data structure:
            {
                "success": bool,
                "data": {
                    "poolData": [
                        {
                            "id": str,
                            "address": str,
                            "name": str,
                            "symbol": str,
                            "coins": [...],
                            "tvl": float,
                            "tvlUSD": float,
                            "virtualPrice": float,
                            "baseApr": float,
                            "crvApr": float,
                            ...
                        }
                    ],
                    "tvl": float,
                    "tvlAll": float
                }
            }
        """
        curve_chain = self.CHAIN_MAPPINGS.get(chain.lower(), chain)
        return self._make_request(f"getPools/{curve_chain}")

    def get_pool_stats(self, chain: str = "ethereum") -> Dict[str, Any]:
        """
        Get pool statistics including APY data.

        Args:
            chain: Blockchain name

        Returns:
            Pool statistics with APY calculations
        """
        curve_chain = self.CHAIN_MAPPINGS.get(chain.lower(), chain)
        return self._make_request(f"getSubgraphData/{curve_chain}")

    def get_volume(self, chain: str, pool_address: str) -> Dict[str, Any]:
        """
        Get volume data for a specific pool.

        Args:
            chain: Blockchain name
            pool_address: Pool contract address

        Returns:
            Volume data for the pool
        """
        curve_chain = self.CHAIN_MAPPINGS.get(chain.lower(), chain)
        return self._make_request(f"getVolume/{curve_chain}/{pool_address}")

    def get_pool_by_address(self, chain: str, pool_address: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed data for a specific pool by address.

        Args:
            chain: Blockchain name
            pool_address: Pool contract address

        Returns:
            Pool data if found, None otherwise
        """
        pools_data = self.get_pools(chain)

        if not pools_data.get("success") or "data" not in pools_data:
            return None

        pool_address_lower = pool_address.lower()
        pool_list = pools_data["data"].get("poolData", [])

        for pool in pool_list:
            if pool.get("address", "").lower() == pool_address_lower:
                return pool

        return None

    def get_top_pools(self, chain: str = "ethereum", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top pools by TVL on a specific chain.

        Args:
            chain: Blockchain name
            limit: Maximum number of pools to return

        Returns:
            List of top pools sorted by TVL
        """
        pools_data = self.get_pools(chain)

        if not pools_data.get("success") or "data" not in pools_data:
            return []

        pool_list = pools_data["data"].get("poolData", [])

        # Sort by TVL in USD
        sorted_pools = sorted(
            pool_list,
            key=lambda x: x.get("tvlUSD", 0) or x.get("usdTotal", 0),
            reverse=True
        )

        return sorted_pools[:limit]

    def get_total_tvl(self, chain: str = "ethereum") -> float:
        """
        Get total TVL across all Curve pools on a chain.

        Args:
            chain: Blockchain name

        Returns:
            Total TVL in USD
        """
        pools_data = self.get_pools(chain)

        if not pools_data.get("success") or "data" not in pools_data:
            return 0.0

        return pools_data["data"].get("tvlAll", 0.0) or pools_data["data"].get("tvl", 0.0)


# Convenience functions
@lru_cache(maxsize=32)
def get_curve_client() -> CurveAPI:
    """Get a cached Curve API client instance."""
    return CurveAPI()


def get_curve_pools(chain: str = "ethereum", limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get Curve pools on a specific chain.

    Args:
        chain: Blockchain name (ethereum, arbitrum, optimism, polygon, etc.)
        limit: Optional limit on number of pools to return (top by TVL)

    Returns:
        List of pool data dictionaries

    Example:
        >>> pools = get_curve_pools("ethereum", limit=5)
        >>> for pool in pools:
        ...     print(f"{pool['name']}: ${pool['tvlUSD']:,.2f}")
    """
    client = get_curve_client()

    if limit:
        return client.get_top_pools(chain, limit)
    else:
        pools_data = client.get_pools(chain)
        if pools_data.get("success") and "data" in pools_data:
            return pools_data["data"].get("poolData", [])
        return []


def get_curve_pool_apy(chain: str, pool_address: str) -> Dict[str, float]:
    """
    Get APY breakdown for a specific Curve pool.

    Args:
        chain: Blockchain name
        pool_address: Pool contract address

    Returns:
        Dictionary with APY components:
        {
            "base_apy": float,  # Base trading fee APY
            "crv_apy": float,   # CRV rewards APY
            "total_apy": float  # Total APY (base + rewards)
        }

    Example:
        >>> apy = get_curve_pool_apy("ethereum", "0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7")
        >>> print(f"Base APY: {apy['base_apy']:.2f}%")
        >>> print(f"CRV APY: {apy['crv_apy']:.2f}%")
        >>> print(f"Total APY: {apy['total_apy']:.2f}%")
    """
    client = get_curve_client()
    pool = client.get_pool_by_address(chain, pool_address)

    if not pool:
        return {"base_apy": 0.0, "crv_apy": 0.0, "total_apy": 0.0}

    base_apy = pool.get("baseApr", 0.0) or pool.get("apy", 0.0)
    crv_apy = pool.get("crvApr", 0.0) or pool.get("gaugeRewards", {}).get("apy", 0.0)

    return {
        "base_apy": base_apy,
        "crv_apy": crv_apy,
        "total_apy": base_apy + crv_apy
    }


def format_curve_pool(pool: Dict[str, Any]) -> str:
    """
    Format a Curve pool data into human-readable string.

    Args:
        pool: Pool data dictionary from Curve API

    Returns:
        Formatted string with pool information
    """
    name = pool.get("name", "Unknown Pool")
    symbol = pool.get("symbol", "")
    tvl = pool.get("tvlUSD", 0) or pool.get("usdTotal", 0)
    base_apy = pool.get("baseApr", 0.0) or pool.get("apy", 0.0)
    crv_apy = pool.get("crvApr", 0.0)
    total_apy = base_apy + crv_apy

    coins = pool.get("coins", [])
    coin_symbols = [c.get("symbol", "?") for c in coins] if coins else []

    return f"""**{name}** ({symbol})
- **Tokens**: {' + '.join(coin_symbols)}
- **TVL**: ${tvl:,.2f}
- **Base APY**: {base_apy:.2f}% (trading fees)
- **CRV APY**: {crv_apy:.2f}% (rewards)
- **Total APY**: {total_apy:.2f}%
- **Address**: `{pool.get('address', 'N/A')}`"""


if __name__ == "__main__":
    # Example usage
    print("Testing Curve Finance API...")

    try:
        client = CurveAPI()

        # Test getting pools
        print("\n1. Top 5 Curve pools on Ethereum:")
        top_pools = client.get_top_pools("ethereum", limit=5)
        for i, pool in enumerate(top_pools, 1):
            print(f"\n{i}. {format_curve_pool(pool)}")

        # Test getting total TVL
        print(f"\n2. Total Curve TVL on Ethereum:")
        total_tvl = client.get_total_tvl("ethereum")
        print(f"${total_tvl:,.2f}")

        print("\n✅ Curve API test successful!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
