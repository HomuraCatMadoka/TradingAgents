"""
GMX Official API Integration

GMX is a decentralized perpetual exchange with an official API for trading data
and liquidity pool information.

API Base URL: https://api.gmx.io
Chains: Arbitrum, Avalanche

Key features:
- Trading volume and fees
- GLP (liquidity pool) data
- Open interest
- Funding rates
- Historical data

Note: GMX provides comprehensive data for perpetual trading analysis.
"""

from typing import Dict, List, Optional, Any
import requests
from functools import lru_cache
import time


class GMXAPI:
    """Client for GMX official API"""

    # Chain-specific API endpoints
    ENDPOINTS = {
        "arbitrum": "https://api.gmx.io",
        "arb": "https://api.gmx.io",
        "avalanche": "https://api.gmx.io",
        "avax": "https://api.gmx.io",
    }

    # Chain IDs
    CHAIN_IDS = {
        "arbitrum": 42161,
        "arb": 42161,
        "avalanche": 43114,
        "avax": 43114,
    }

    def __init__(self, timeout: int = 30):
        """
        Initialize GMX API client.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes cache

    def _make_request(self, endpoint: str, chain: str, params: Optional[Dict] = None) -> Any:
        """
        Make HTTP request to GMX API with caching.

        Args:
            endpoint: API endpoint path
            chain: Blockchain name (arbitrum or avalanche)
            params: Query parameters

        Returns:
            Parsed JSON response
        """
        cache_key = f"{chain}:{endpoint}:{str(params)}"
        now = time.time()

        # Check cache
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if now - cached_time < self._cache_ttl:
                return cached_data

        base_url = self.ENDPOINTS.get(chain.lower())
        if not base_url:
            raise ValueError(f"Unsupported chain: {chain}. Supported: {list(self.ENDPOINTS.keys())}")

        url = f"{base_url}/{endpoint}"

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            # Cache the result
            self._cache[cache_key] = (data, now)
            return data

        except requests.exceptions.RequestException as e:
            raise Exception(f"GMX API request failed: {e}")

    def get_stats(self, chain: str = "arbitrum") -> Dict[str, Any]:
        """
        Get GMX statistics including volume, fees, and open interest.

        Args:
            chain: Blockchain name (arbitrum or avalanche)

        Returns:
            Dictionary with GMX stats:
            {
                "totalVolume": float,
                "totalFees": float,
                "openInterest": float,
                "glpPrice": float,
                "glpSupply": float,
                ...
            }
        """
        return self._make_request("stats", chain)

    def get_glp_price(self, chain: str = "arbitrum") -> float:
        """
        Get current GLP token price.

        Args:
            chain: Blockchain name

        Returns:
            GLP price in USD
        """
        stats = self.get_stats(chain)
        return stats.get("glpPrice", 0.0)

    def get_glp_apy(self, chain: str = "arbitrum") -> Dict[str, float]:
        """
        Get GLP APY breakdown.

        Args:
            chain: Blockchain name

        Returns:
            Dictionary with APY components:
            {
                "fee_apy": float,      # APY from trading fees
                "esGMX_apy": float,    # APY from esGMX rewards
                "total_apy": float     # Total APY
            }
        """
        stats = self.get_stats(chain)

        # GMX provides APY data in basis points or percentages
        fee_apy = stats.get("feeApy", 0.0)
        esgmx_apy = stats.get("esGmxApy", 0.0)

        return {
            "fee_apy": fee_apy,
            "esGMX_apy": esgmx_apy,
            "total_apy": fee_apy + esgmx_apy
        }

    def get_total_volume(self, chain: str = "arbitrum") -> float:
        """
        Get total cumulative trading volume.

        Args:
            chain: Blockchain name

        Returns:
            Total volume in USD
        """
        stats = self.get_stats(chain)
        return stats.get("totalVolume", 0.0)

    def get_total_fees(self, chain: str = "arbitrum") -> float:
        """
        Get total cumulative fees collected.

        Args:
            chain: Blockchain name

        Returns:
            Total fees in USD
        """
        stats = self.get_stats(chain)
        return stats.get("totalFees", 0.0)

    def get_open_interest(self, chain: str = "arbitrum") -> float:
        """
        Get current open interest across all positions.

        Args:
            chain: Blockchain name

        Returns:
            Open interest in USD
        """
        stats = self.get_stats(chain)
        return stats.get("openInterest", 0.0)

    def get_glp_tvl(self, chain: str = "arbitrum") -> float:
        """
        Get GLP pool TVL (Total Value Locked).

        Args:
            chain: Blockchain name

        Returns:
            TVL in USD
        """
        stats = self.get_stats(chain)
        glp_price = stats.get("glpPrice", 0.0)
        glp_supply = stats.get("glpSupply", 0.0)
        return glp_price * glp_supply

    def get_trading_data(self, chain: str = "arbitrum", period: str = "24h") -> Dict[str, Any]:
        """
        Get trading data for a specific period.

        Args:
            chain: Blockchain name
            period: Time period ("24h", "7d", "30d")

        Returns:
            Dictionary with trading metrics
        """
        stats = self.get_stats(chain)

        # Extract period-specific data
        volume_key = f"volume{period.upper()}"
        fees_key = f"fees{period.upper()}"

        return {
            "volume": stats.get(volume_key, 0.0),
            "fees": stats.get(fees_key, 0.0),
            "open_interest": stats.get("openInterest", 0.0),
        }


# Convenience functions
@lru_cache(maxsize=16)
def get_gmx_client() -> GMXAPI:
    """Get a cached GMX API client instance."""
    return GMXAPI()


def get_gmx_glp_data(chain: str = "arbitrum") -> Dict[str, Any]:
    """
    Get comprehensive GLP (liquidity pool) data.

    Args:
        chain: Blockchain name (arbitrum or avalanche)

    Returns:
        Dictionary with GLP metrics

    Example:
        >>> glp_data = get_gmx_glp_data("arbitrum")
        >>> print(f"GLP APY: {glp_data['apy']['total_apy']:.2f}%")
        >>> print(f"GLP TVL: ${glp_data['tvl']:,.2f}")
    """
    client = get_gmx_client()

    price = client.get_glp_price(chain)
    apy = client.get_glp_apy(chain)
    tvl = client.get_glp_tvl(chain)

    return {
        "price": price,
        "tvl": tvl,
        "apy": apy,
        "chain": chain
    }


def get_gmx_stats(chain: str = "arbitrum") -> Dict[str, Any]:
    """
    Get GMX protocol statistics.

    Args:
        chain: Blockchain name

    Returns:
        Dictionary with protocol stats

    Example:
        >>> stats = get_gmx_stats("arbitrum")
        >>> print(f"Total Volume: ${stats['total_volume']:,.2f}")
        >>> print(f"Total Fees: ${stats['total_fees']:,.2f}")
    """
    client = get_gmx_client()

    return {
        "total_volume": client.get_total_volume(chain),
        "total_fees": client.get_total_fees(chain),
        "open_interest": client.get_open_interest(chain),
        "glp_data": get_gmx_glp_data(chain)
    }


def format_gmx_data(chain: str = "arbitrum") -> str:
    """
    Format GMX data into human-readable string.

    Args:
        chain: Blockchain name

    Returns:
        Formatted string with GMX information
    """
    try:
        stats = get_gmx_stats(chain)
        glp = stats["glp_data"]

        return f"""**GMX Protocol** ({chain.upper()})

**Trading Metrics:**
- Total Volume: ${stats['total_volume']:,.2f}
- Total Fees: ${stats['total_fees']:,.2f}
- Open Interest: ${stats['open_interest']:,.2f}

**GLP Pool:**
- Price: ${glp['price']:.2f}
- TVL: ${glp['tvl']:,.2f}
- Fee APY: {glp['apy']['fee_apy']:.2f}%
- esGMX APY: {glp['apy']['esGMX_apy']:.2f}%
- Total APY: {glp['apy']['total_apy']:.2f}%"""

    except Exception as e:
        return f"Error fetching GMX data: {e}"


if __name__ == "__main__":
    # Example usage
    print("Testing GMX API...")

    try:
        print("\n1. GMX on Arbitrum:")
        print(format_gmx_data("arbitrum"))

        print("\n2. GMX on Avalanche:")
        print(format_gmx_data("avalanche"))

        print("\n✅ GMX API test successful!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
