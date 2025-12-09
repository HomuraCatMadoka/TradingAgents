"""
CoinGecko API integration.

Provides access to cryptocurrency market data including prices, market caps,
volume, and other metrics.
API Documentation: https://www.coingecko.com/en/api/documentation

Features:
- Token prices (current and historical)
- Market data (market cap, volume, price changes)
- Token search
- Multi-currency support
- Free and Pro API support
"""

import time
import logging
from typing import Dict, List, Optional, Any
import requests

logger = logging.getLogger(__name__)


class CoinGeckoAPI:
    """CoinGecko API client."""

    FREE_API_URL = "https://api.coingecko.com/api/v3"
    PRO_API_URL = "https://pro-api.coingecko.com/api/v3"

    def __init__(
        self,
        api_key: Optional[str] = None,
        use_pro: bool = False,
        cache_ttl: int = 300,
    ):
        """
        Initialize CoinGecko API client.

        Args:
            api_key: CoinGecko Pro API key (optional)
            use_pro: Whether to use Pro API (requires API key)
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
        """
        self.api_key = api_key
        self.use_pro = use_pro and api_key is not None
        self.base_url = self.PRO_API_URL if self.use_pro else self.FREE_API_URL
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

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """
        Make HTTP request to CoinGecko API.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        url = f"{self.base_url}/{endpoint}"

        # Add API key to headers if using Pro
        headers = {}
        if self.use_pro and self.api_key:
            headers["x-cg-pro-api-key"] = self.api_key

        # Generate cache key
        cache_key = f"coingecko:{endpoint}:{params}"
        cached_data = self._get_cached(cache_key)
        if cached_data is not None:
            return cached_data

        try:
            logger.info(f"Fetching CoinGecko data: {endpoint}")
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Cache the response
            self._set_cache(cache_key, data)

            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"CoinGecko API request failed: {e}")
            raise

    def ping(self) -> Dict:
        """Check API server status."""
        return self._make_request("ping")

    def get_token_price(
        self,
        token_ids: List[str],
        vs_currencies: List[str] = ["usd"],
        include_market_cap: bool = False,
        include_24h_vol: bool = False,
        include_24h_change: bool = False,
    ) -> Dict:
        """
        Get current token prices.

        Args:
            token_ids: List of CoinGecko token IDs (e.g., ['bitcoin', 'ethereum'])
            vs_currencies: List of currencies (e.g., ['usd', 'eur'])
            include_market_cap: Include market cap
            include_24h_vol: Include 24h volume
            include_24h_change: Include 24h price change

        Returns:
            Dictionary mapping token IDs to price data

        Example:
            >>> api = CoinGeckoAPI()
            >>> prices = api.get_token_price(['ethereum'], include_24h_change=True)
            >>> print(prices['ethereum']['usd'])
        """
        params = {
            "ids": ",".join(token_ids),
            "vs_currencies": ",".join(vs_currencies),
            "include_market_cap": str(include_market_cap).lower(),
            "include_24hr_vol": str(include_24h_vol).lower(),
            "include_24hr_change": str(include_24h_change).lower(),
        }
        return self._make_request("simple/price", params)

    def get_token_market_data(
        self,
        token_id: str,
        localization: bool = False,
        tickers: bool = False,
        market_data: bool = True,
        community_data: bool = False,
        developer_data: bool = False,
    ) -> Dict:
        """
        Get comprehensive market data for a token.

        Args:
            token_id: CoinGecko token ID
            localization: Include localized language fields
            tickers: Include ticker data
            market_data: Include market data (prices, volume, market cap)
            community_data: Include community stats
            developer_data: Include developer stats

        Returns:
            Comprehensive token data

        Example:
            >>> api = CoinGeckoAPI()
            >>> data = api.get_token_market_data('ethereum')
            >>> print(data['market_data']['current_price']['usd'])
        """
        params = {
            "localization": str(localization).lower(),
            "tickers": str(tickers).lower(),
            "market_data": str(market_data).lower(),
            "community_data": str(community_data).lower(),
            "developer_data": str(developer_data).lower(),
        }
        return self._make_request(f"coins/{token_id}", params)

    def search_tokens(self, query: str) -> Dict:
        """
        Search for tokens by name or symbol.

        Args:
            query: Search query (token name or symbol)

        Returns:
            Search results with coins, exchanges, categories

        Example:
            >>> api = CoinGeckoAPI()
            >>> results = api.search_tokens('ethereum')
            >>> print(results['coins'][0]['name'])
        """
        params = {"query": query}
        return self._make_request("search", params)

    def get_token_market_chart(
        self,
        token_id: str,
        vs_currency: str = "usd",
        days: int = 7,
        interval: Optional[str] = None,
    ) -> Dict:
        """
        Get historical market data (price, market cap, volume).

        Args:
            token_id: CoinGecko token ID
            vs_currency: Currency (default: usd)
            days: Number of days (1, 7, 14, 30, 90, 180, 365, max)
            interval: Data interval (daily, hourly) - auto if None

        Returns:
            Historical data with prices, market_caps, total_volumes

        Example:
            >>> api = CoinGeckoAPI()
            >>> chart = api.get_token_market_chart('ethereum', days=7)
            >>> prices = chart['prices']  # List of [timestamp, price]
        """
        params = {
            "vs_currency": vs_currency,
            "days": days,
        }
        if interval:
            params["interval"] = interval

        return self._make_request(f"coins/{token_id}/market_chart", params)

    def get_trending_tokens(self) -> Dict:
        """
        Get trending tokens (top 7).

        Returns:
            Trending tokens data
        """
        return self._make_request("search/trending")

    def get_global_defi_data(self) -> Dict:
        """
        Get global DeFi data.

        Returns:
            DeFi market cap, volume, dominance
        """
        return self._make_request("global/decentralized_finance_defi")

    def get_token_contract_data(
        self,
        chain: str,
        contract_address: str,
    ) -> Dict:
        """
        Get token data by contract address.

        Args:
            chain: Platform ID (e.g., 'ethereum', 'arbitrum-one', 'optimistic-ethereum')
            contract_address: Token contract address

        Returns:
            Token data

        Example:
            >>> api = CoinGeckoAPI()
            >>> # USDC on Ethereum
            >>> data = api.get_token_contract_data('ethereum', '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48')
        """
        return self._make_request(f"coins/{chain}/contract/{contract_address}")


# Global instance
_api_instance: Optional[CoinGeckoAPI] = None


def get_api_instance(
    api_key: Optional[str] = None,
    use_pro: bool = False,
) -> CoinGeckoAPI:
    """Get or create global API instance."""
    global _api_instance
    if _api_instance is None:
        _api_instance = CoinGeckoAPI(api_key=api_key, use_pro=use_pro)
    return _api_instance


# Convenience functions


def get_token_price(
    token_id: str,
    vs_currency: str = "usd",
    include_24h_change: bool = True,
) -> Dict:
    """
    Get current token price.

    Args:
        token_id: CoinGecko token ID
        vs_currency: Currency (default: usd)
        include_24h_change: Include 24h price change

    Returns:
        Price data dictionary
    """
    api = get_api_instance()
    result = api.get_token_price(
        [token_id],
        [vs_currency],
        include_market_cap=True,
        include_24h_vol=True,
        include_24h_change=include_24h_change,
    )
    return result.get(token_id, {})


def get_token_market_data(token_id: str) -> Dict:
    """
    Get comprehensive market data for a token.

    Args:
        token_id: CoinGecko token ID

    Returns:
        Market data dictionary
    """
    api = get_api_instance()
    return api.get_token_market_data(token_id)


def search_tokens(query: str) -> List[Dict]:
    """
    Search for tokens.

    Args:
        query: Search query

    Returns:
        List of matching tokens
    """
    api = get_api_instance()
    result = api.search_tokens(query)
    return result.get("coins", [])


def format_token_price(token_id: str, price_data: Dict) -> str:
    """
    Format token price data into readable string.

    Args:
        token_id: Token ID
        price_data: Price data from get_token_price

    Returns:
        Formatted markdown string
    """
    if not price_data:
        return f"## {token_id.title()}\n\n**Error**: Price data not available"

    price = price_data.get("usd", 0)
    market_cap = price_data.get("usd_market_cap", 0)
    volume = price_data.get("usd_24h_vol", 0)
    change_24h = price_data.get("usd_24h_change", 0)

    # Format numbers
    price_str = f"${price:,.2f}" if price < 1000 else f"${price:,.0f}"

    if market_cap >= 1e9:
        mcap_str = f"${market_cap/1e9:.2f}B"
    elif market_cap >= 1e6:
        mcap_str = f"${market_cap/1e6:.2f}M"
    else:
        mcap_str = f"${market_cap:,.0f}" if market_cap else "N/A"

    if volume >= 1e9:
        vol_str = f"${volume/1e9:.2f}B"
    elif volume >= 1e6:
        vol_str = f"${volume/1e6:.2f}M"
    else:
        vol_str = f"${volume:,.0f}" if volume else "N/A"

    change_icon = "📈" if change_24h >= 0 else "📉"
    change_str = f"{change_icon} {change_24h:+.2f}%" if change_24h else "N/A"

    return f"""## {token_id.title()}

**Price**: {price_str}
**24h Change**: {change_str}
**Market Cap**: {mcap_str}
**24h Volume**: {vol_str}
"""


def format_market_data(market_data_response: Dict) -> str:
    """
    Format comprehensive market data into readable string.

    Args:
        market_data_response: Response from get_token_market_data

    Returns:
        Formatted markdown string
    """
    name = market_data_response.get("name", "Unknown")
    symbol = market_data_response.get("symbol", "").upper()

    market_data = market_data_response.get("market_data", {})
    if not market_data:
        return f"## {name} ({symbol})\n\n**Error**: Market data not available"

    current_price = market_data.get("current_price", {})
    price_usd = current_price.get("usd", 0)

    market_cap = market_data.get("market_cap", {}).get("usd", 0)
    total_volume = market_data.get("total_volume", {}).get("usd", 0)

    price_change_24h = market_data.get("price_change_percentage_24h", 0)
    price_change_7d = market_data.get("price_change_percentage_7d", 0)
    price_change_30d = market_data.get("price_change_percentage_30d", 0)

    ath = market_data.get("ath", {}).get("usd", 0)
    ath_change = market_data.get("ath_change_percentage", {}).get("usd", 0)

    circulating_supply = market_data.get("circulating_supply", 0)
    total_supply = market_data.get("total_supply", 0)

    # Format numbers
    price_str = f"${price_usd:,.2f}" if price_usd < 1000 else f"${price_usd:,.0f}"
    mcap_str = f"${market_cap/1e9:.2f}B" if market_cap >= 1e9 else f"${market_cap/1e6:.2f}M"
    vol_str = f"${total_volume/1e9:.2f}B" if total_volume >= 1e9 else f"${total_volume/1e6:.2f}M"
    ath_str = f"${ath:,.2f}" if ath < 1000 else f"${ath:,.0f}"

    return f"""## {name} ({symbol})

### Price Information
**Current Price**: {price_str}
**24h Change**: {price_change_24h:+.2f}%
**7d Change**: {price_change_7d:+.2f}%
**30d Change**: {price_change_30d:+.2f}%

### Market Metrics
**Market Cap**: {mcap_str}
**24h Volume**: {vol_str}
**All-Time High**: {ath_str} ({ath_change:+.2f}% from ATH)

### Supply
**Circulating Supply**: {circulating_supply:,.0f} {symbol}
**Total Supply**: {total_supply:,.0f} {symbol if total_supply else 'N/A'}
"""


if __name__ == "__main__":
    # Example usage
    import sys

    logging.basicConfig(level=logging.INFO)

    print("Testing CoinGecko API...\n")

    try:
        # Test simple price
        print("=== Ethereum Price ===\n")
        price_data = get_token_price("ethereum")
        print(format_token_price("ethereum", price_data))

        print("\n" + "="*60 + "\n")

        # Test comprehensive market data
        print("=== Bitcoin Market Data ===\n")
        market_data = get_token_market_data("bitcoin")
        print(format_market_data(market_data))

        print("\n" + "="*60 + "\n")

        # Test token search
        print("=== Search for 'USDC' ===\n")
        results = search_tokens("USDC")
        for token in results[:3]:
            print(f"- {token.get('name')} ({token.get('symbol')}) [ID: {token.get('id')}]")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
