"""
PancakeSwap Official API Integration

PancakeSwap is the leading DEX on BNB Chain with multi-chain support.

API Base URL: https://api.pancakeswap.info/api/v2
Chains: BNB Chain, Ethereum, Arbitrum, Base

Key features:
- Token prices
- Liquidity pool data
- Trading volume
- Farm APR data

Note: PancakeSwap API focuses on V2 AMM data. For V3, consider using The Graph.
"""

from typing import Dict, List, Optional, Any
import requests
from functools import lru_cache
import time


class PancakeSwapAPI:
    """Client for PancakeSwap official API"""

    BASE_URL = "https://api.pancakeswap.info/api/v2"

    def __init__(self, timeout: int = 30):
        """
        Initialize PancakeSwap API client.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes cache

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """
        Make HTTP request to PancakeSwap API with caching.

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
            raise Exception(f"PancakeSwap API request failed: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """
        Get PancakeSwap summary statistics.

        Returns:
            Dictionary with protocol stats:
            {
                "updated_at": int,
                "data": {
                    "total_volume_24h": float,
                    "total_liquidity": float,
                    "total_pairs": int
                }
            }
        """
        return self._make_request("summary")

    def get_tokens(self) -> Dict[str, Any]:
        """
        Get all tokens listed on PancakeSwap.

        Returns:
            Dictionary mapping token addresses to token data:
            {
                "0x...": {
                    "name": str,
                    "symbol": str,
                    "price": str,
                    "price_BNB": str
                }
            }
        """
        return self._make_request("tokens")

    def get_token(self, token_address: str) -> Dict[str, Any]:
        """
        Get data for a specific token.

        Args:
            token_address: Token contract address

        Returns:
            Token data dictionary
        """
        return self._make_request(f"tokens/{token_address}")

    def get_pairs(self) -> Dict[str, Any]:
        """
        Get all liquidity pairs on PancakeSwap.

        Returns:
            Dictionary mapping pair addresses to pair data:
            {
                "0x...": {
                    "pair_address": str,
                    "base_name": str,
                    "base_symbol": str,
                    "quote_name": str,
                    "quote_symbol": str,
                    "price": str,
                    "base_volume": str,
                    "quote_volume": str,
                    "liquidity": str
                }
            }
        """
        return self._make_request("pairs")

    def get_pair(self, pair_address: str) -> Dict[str, Any]:
        """
        Get data for a specific liquidity pair.

        Args:
            pair_address: Pair contract address

        Returns:
            Pair data dictionary
        """
        return self._make_request(f"pairs/{pair_address}")

    def get_top_pairs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top liquidity pairs by volume or liquidity.

        Args:
            limit: Maximum number of pairs to return

        Returns:
            List of top pair data dictionaries
        """
        pairs_data = self.get_pairs()

        if not pairs_data or "data" not in pairs_data:
            return []

        pairs_list = []
        for pair_addr, pair_data in pairs_data["data"].items():
            pair_data["pair_address"] = pair_addr
            pairs_list.append(pair_data)

        # Sort by liquidity
        sorted_pairs = sorted(
            pairs_list,
            key=lambda x: float(x.get("liquidity", 0)),
            reverse=True
        )

        return sorted_pairs[:limit]

    def get_token_price(self, token_address: str) -> float:
        """
        Get current price for a token in USD.

        Args:
            token_address: Token contract address

        Returns:
            Token price in USD
        """
        token_data = self.get_token(token_address)

        if not token_data or "data" not in token_data:
            return 0.0

        price_str = token_data["data"].get("price", "0")
        try:
            return float(price_str)
        except ValueError:
            return 0.0

    def get_total_tvl(self) -> float:
        """
        Get total TVL (liquidity) across PancakeSwap.

        Returns:
            Total TVL in USD
        """
        summary = self.get_summary()

        if not summary or "data" not in summary:
            return 0.0

        return summary["data"].get("total_liquidity", 0.0)


# Convenience functions
@lru_cache(maxsize=16)
def get_pancakeswap_client() -> PancakeSwapAPI:
    """Get a cached PancakeSwap API client instance."""
    return PancakeSwapAPI()


def get_pancake_pairs(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get top PancakeSwap liquidity pairs.

    Args:
        limit: Maximum number of pairs to return

    Returns:
        List of pair data dictionaries

    Example:
        >>> pairs = get_pancake_pairs(5)
        >>> for pair in pairs:
        ...     print(f"{pair['base_symbol']}/{pair['quote_symbol']}: ${pair['liquidity']}")
    """
    client = get_pancakeswap_client()
    return client.get_top_pairs(limit)


def get_pancake_token_price(token_address: str) -> float:
    """
    Get token price from PancakeSwap.

    Args:
        token_address: Token contract address

    Returns:
        Token price in USD

    Example:
        >>> price = get_pancake_token_price("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
        >>> print(f"Price: ${price:.2f}")
    """
    client = get_pancakeswap_client()
    return client.get_token_price(token_address)


def format_pancake_pair(pair: Dict[str, Any]) -> str:
    """
    Format a PancakeSwap pair data into human-readable string.

    Args:
        pair: Pair data dictionary from PancakeSwap API

    Returns:
        Formatted string with pair information
    """
    base_symbol = pair.get("base_symbol", "?")
    quote_symbol = pair.get("quote_symbol", "?")
    price = pair.get("price", "0")
    liquidity = pair.get("liquidity", "0")
    base_volume = pair.get("base_volume", "0")

    try:
        price_float = float(price)
        liquidity_float = float(liquidity)
        volume_float = float(base_volume)
    except ValueError:
        price_float = 0.0
        liquidity_float = 0.0
        volume_float = 0.0

    return f"""**{base_symbol}/{quote_symbol}**
- **Price**: ${price_float:.6f}
- **Liquidity**: ${liquidity_float:,.2f}
- **24h Volume**: ${volume_float:,.2f}
- **Address**: `{pair.get('pair_address', 'N/A')}`"""


def format_pancake_summary() -> str:
    """
    Format PancakeSwap protocol summary.

    Returns:
        Formatted string with protocol statistics
    """
    try:
        client = get_pancakeswap_client()
        summary = client.get_summary()

        if not summary or "data" not in summary:
            return "Unable to fetch PancakeSwap summary"

        data = summary["data"]
        total_volume = data.get("total_volume_24h", 0)
        total_liquidity = data.get("total_liquidity", 0)
        total_pairs = data.get("total_pairs", 0)

        return f"""**PancakeSwap Protocol Summary**
- **24h Volume**: ${total_volume:,.2f}
- **Total Liquidity**: ${total_liquidity:,.2f}
- **Total Pairs**: {total_pairs:,}"""

    except Exception as e:
        return f"Error fetching PancakeSwap summary: {e}"


if __name__ == "__main__":
    # Example usage
    print("Testing PancakeSwap API...")

    try:
        client = PancakeSwapAPI()

        # Test getting summary
        print("\n1. PancakeSwap Summary:")
        print(format_pancake_summary())

        # Test getting top pairs
        print("\n2. Top 5 PancakeSwap pairs:")
        top_pairs = client.get_top_pairs(limit=5)
        for i, pair in enumerate(top_pairs, 1):
            print(f"\n{i}. {format_pancake_pair(pair)}")

        print("\n✅ PancakeSwap API test successful!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
