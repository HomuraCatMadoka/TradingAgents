"""
DeFi Llama API integration.

Provides access to DeFi protocol data including TVL, APY, and general metrics.
API Documentation: https://defillama.com/docs/api

Features:
- Protocol TVL and historical data
- Multi-chain support
- Yield/APY data
- Completely free, no API key required
"""

import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def _normalize_tvl(tvl_value: Any) -> float:
    """
    Normalize TVL value to float.

    Handles cases where TVL is:
    - float/int: return as is
    - list: return sum or first element
    - dict: extract 'tvl' field recursively
    - None: return 0

    Args:
        tvl_value: TVL value from API (can be number, list, dict, or None)

    Returns:
        Normalized TVL as float
    """
    if tvl_value is None:
        return 0.0

    if isinstance(tvl_value, (int, float)):
        return float(tvl_value)

    if isinstance(tvl_value, list):
        if not tvl_value:
            return 0.0
        # If list of numbers, sum them (multi-chain TVL)
        if isinstance(tvl_value[0], (int, float)):
            return float(sum(tvl_value))
        # If list of dicts with historical data (date + totalLiquidityUSD)
        if isinstance(tvl_value[0], dict) and 'totalLiquidityUSD' in tvl_value[0]:
            # Return the latest (last) value
            return float(tvl_value[-1].get('totalLiquidityUSD', 0))
        # If list of dicts, sum their tvl fields recursively
        return sum(_normalize_tvl(item.get('tvl', 0)) for item in tvl_value if isinstance(item, dict))

    if isinstance(tvl_value, dict):
        # Recursively handle dict's tvl field
        return _normalize_tvl(tvl_value.get('tvl', 0))

    # Fallback: try to convert to float
    try:
        return float(tvl_value)
    except (ValueError, TypeError):
        logger.warning(f"Unexpected TVL type: {type(tvl_value)}, value: {tvl_value}")
        return 0.0


class DefiLlamaAPI:
    """DeFi Llama API client."""

    BASE_URL = "https://api.llama.fi"
    COINS_URL = "https://coins.llama.fi"
    YIELDS_URL = "https://yields.llama.fi"

    def __init__(self, cache_ttl: int = 3600):
        """
        Initialize DeFi Llama API client.

        Args:
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, tuple[Any, float]] = {}

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached data if not expired."""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for key: {key}")
                return data
            else:
                logger.debug(f"Cache expired for key: {key}")
                del self._cache[key]
        return None

    def _set_cache(self, key: str, data: Any):
        """Cache data with timestamp."""
        self._cache[key] = (data, time.time())
        logger.debug(f"Cached data for key: {key}")

    def _make_request(self, endpoint: str, base_url: str = None) -> Dict:
        """
        Make HTTP request to DeFi Llama API.

        Args:
            endpoint: API endpoint path
            base_url: Base URL (default: self.BASE_URL)

        Returns:
            JSON response as dictionary

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        url = f"{base_url or self.BASE_URL}/{endpoint}"
        cache_key = f"defillama:{url}"

        # Check cache
        cached_data = self._get_cached(cache_key)
        if cached_data is not None:
            return cached_data

        try:
            logger.info(f"Fetching DeFi Llama data: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Cache the response
            self._set_cache(cache_key, data)

            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"DeFi Llama API request failed: {e}")
            raise

    def get_protocol(self, slug: str) -> Dict:
        """
        Get detailed information about a specific protocol.

        Args:
            slug: Protocol slug (e.g., 'uniswap-v3', 'aave-v3')

        Returns:
            Protocol data including TVL, chains, and metadata

        Example:
            >>> api = DefiLlamaAPI()
            >>> data = api.get_protocol('uniswap-v3')
            >>> print(data['name'], data['tvl'])
        """
        return self._make_request(f"protocol/{slug}")

    def get_all_protocols(self) -> List[Dict]:
        """
        Get list of all protocols with basic info.

        Returns:
            List of protocols with name, slug, tvl, chains, etc.
        """
        return self._make_request("protocols")

    def get_tvl(self, slug: str) -> float:
        """
        Get current TVL for a protocol.

        Args:
            slug: Protocol slug

        Returns:
            Current TVL in USD
        """
        data = self.get_protocol(slug)
        tvl_value = data.get('tvl', 0.0)
        return _normalize_tvl(tvl_value)

    def get_historical_tvl(self, slug: str) -> List[Dict]:
        """
        Get historical TVL data for a protocol.

        Args:
            slug: Protocol slug

        Returns:
            List of {date: timestamp, tvl: float} dictionaries
        """
        data = self.get_protocol(slug)
        return data.get('tvl', [])

    def get_chains_tvl(self) -> List[Dict]:
        """
        Get TVL for all chains.

        Returns:
            List of chains with name, tvl, tokenSymbol, etc.
        """
        return self._make_request("chains")

    def get_chain_tvl(self, chain: str) -> Dict:
        """
        Get historical TVL for a specific chain.

        Args:
            chain: Chain name (e.g., 'Ethereum', 'Arbitrum')

        Returns:
            Historical TVL data
        """
        return self._make_request(f"v2/historicalChainTvl/{chain}")

    def get_token_price(self, chain: str, token_address: str) -> Dict:
        """
        Get current token price.

        Args:
            chain: Chain name (e.g., 'ethereum', 'arbitrum')
            token_address: Token contract address

        Returns:
            Price data including price, decimals, symbol, timestamp
        """
        coin_id = f"{chain}:{token_address}"
        data = self._make_request(
            f"prices/current/{coin_id}",
            base_url=self.COINS_URL
        )
        return data.get('coins', {}).get(coin_id, {})

    def get_yields_pools(self) -> List[Dict]:
        """
        Get all yield pools with APY data.

        Returns:
            List of yield pools with apy, tvl, project, chain, etc.
        """
        return self._make_request("pools", base_url=self.YIELDS_URL)

    def get_protocol_yields(self, protocol: str) -> List[Dict]:
        """
        Get yield pools for a specific protocol.

        Args:
            protocol: Protocol name

        Returns:
            List of yield pools for the protocol
        """
        all_pools = self.get_yields_pools()
        return [
            pool for pool in all_pools
            if pool.get('project', '').lower() == protocol.lower()
        ]


# Global instance with default settings
_api_instance: Optional[DefiLlamaAPI] = None


def get_api_instance(cache_ttl: int = 3600) -> DefiLlamaAPI:
    """Get or create global API instance."""
    global _api_instance
    if _api_instance is None:
        _api_instance = DefiLlamaAPI(cache_ttl=cache_ttl)
    return _api_instance


# Convenience functions


def get_protocol_tvl(slug: str) -> float:
    """
    Get current TVL for a protocol.

    Args:
        slug: Protocol slug (e.g., 'uniswap-v3')

    Returns:
        Current TVL in USD
    """
    api = get_api_instance()
    return api.get_tvl(slug)


def get_protocol_info(slug: str) -> Dict:
    """
    Get detailed information about a protocol.

    Args:
        slug: Protocol slug

    Returns:
        Protocol data dictionary
    """
    api = get_api_instance()
    return api.get_protocol(slug)


def get_all_protocols() -> List[Dict]:
    """
    Get list of all protocols.

    Returns:
        List of protocol dictionaries
    """
    api = get_api_instance()
    return api.get_all_protocols()


def get_chains_tvl() -> List[Dict]:
    """
    Get TVL for all chains.

    Returns:
        List of chain dictionaries with TVL data
    """
    api = get_api_instance()
    return api.get_chains_tvl()


def format_protocol_summary(protocol_data: Dict) -> str:
    """
    Format protocol data into a readable summary.

    Args:
        protocol_data: Protocol data from get_protocol_info()

    Returns:
        Formatted markdown string
    """
    name = protocol_data.get('name', 'Unknown')
    tvl = _normalize_tvl(protocol_data.get('tvl', 0))
    chains = protocol_data.get('chains', [])
    category = protocol_data.get('category', 'Unknown')
    description = protocol_data.get('description', 'No description available')

    # Format TVL
    if tvl >= 1e9:
        tvl_str = f"${tvl/1e9:.2f}B"
    elif tvl >= 1e6:
        tvl_str = f"${tvl/1e6:.2f}M"
    else:
        tvl_str = f"${tvl:,.0f}"

    # Build markdown summary
    summary = f"""# {name}

**Category**: {category}
**Total Value Locked (TVL)**: {tvl_str}
**Supported Chains**: {', '.join(chains) if chains else 'N/A'}

## Description
{description}

## Chain-specific TVL
"""

    # Add chain-specific TVL if available
    chain_tvls = protocol_data.get('chainTvls', {})
    if chain_tvls:
        for chain, chain_tvl in chain_tvls.items():
            normalized_tvl = _normalize_tvl(chain_tvl)
            if normalized_tvl > 0:
                if normalized_tvl >= 1e9:
                    tvl_display = f"${normalized_tvl/1e9:.2f}B"
                elif normalized_tvl >= 1e6:
                    tvl_display = f"${normalized_tvl/1e6:.2f}M"
                else:
                    tvl_display = f"${normalized_tvl:,.0f}"
                summary += f"- **{chain}**: {tvl_display}\n"

    return summary


if __name__ == "__main__":
    # Example usage
    import sys

    logging.basicConfig(level=logging.INFO)

    # Test with Uniswap V3
    print("Testing DeFi Llama API with Uniswap V3...\n")

    try:
        info = get_protocol_info('uniswap-v3')
        print(format_protocol_summary(info))

        print("\n" + "="*60 + "\n")

        # Test with Aave V3
        print("Testing with Aave V3...\n")
        info = get_protocol_info('aave-v3')
        print(format_protocol_summary(info))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
