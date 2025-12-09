"""
DeFi Market Data Tools.

Provides LangChain tools for accessing cryptocurrency prices,
market caps, volume, and market trends.
"""

import logging
from langchain_core.tools import tool
from typing import Optional

logger = logging.getLogger(__name__)


@tool
def get_crypto_price(token_id: str) -> str:
    """
    Get current price and 24h change for a cryptocurrency.

    Args:
        token_id: CoinGecko token ID (e.g., 'ethereum', 'bitcoin', 'aave', 'uniswap')

    Returns:
        Current price, 24h change, market cap, and volume

    Example:
        get_crypto_price('ethereum')
    """
    try:
        from defiagents.dataflows.defi import get_token_price, format_token_price

        price_data = get_token_price(token_id, include_24h_change=True)
        return format_token_price(token_id, price_data)
    except Exception as e:
        logger.error(f"Error getting crypto price: {e}")
        return f"Error: Unable to fetch price for '{token_id}'. {str(e)}"


@tool
def get_crypto_market_data(token_id: str) -> str:
    """
    Get comprehensive market data for a cryptocurrency.

    Args:
        token_id: CoinGecko token ID

    Returns:
        Detailed market data including price, market cap, volume,
        price changes (24h, 7d, 30d), ATH, and supply metrics

    Example:
        get_crypto_market_data('bitcoin')
    """
    try:
        from defiagents.dataflows.defi import get_token_market_data, format_market_data

        market_data = get_token_market_data(token_id)
        return format_market_data(market_data)
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        return f"Error: Unable to fetch market data for '{token_id}'. {str(e)}"


@tool
def search_crypto_tokens(query: str) -> str:
    """
    Search for cryptocurrency tokens by name or symbol.

    Args:
        query: Search term (e.g., 'USDC', 'Uniswap', 'Aave')

    Returns:
        List of matching tokens with their IDs and symbols

    Example:
        search_crypto_tokens('USDC')
    """
    try:
        from defiagents.dataflows.defi import search_tokens

        results = search_tokens(query)

        if not results:
            return f"No tokens found matching '{query}'"

        result_text = f"## Search Results for '{query}'\n\n"
        result_text += f"Found {len(results)} matches:\n\n"

        for i, token in enumerate(results[:10], 1):  # Top 10 results
            name = token.get('name', 'Unknown')
            symbol = token.get('symbol', '').upper()
            token_id = token.get('id', '')
            market_cap_rank = token.get('market_cap_rank', 'N/A')

            result_text += f"{i}. **{name}** ({symbol})\n"
            result_text += f"   - ID: `{token_id}`\n"
            result_text += f"   - Market Cap Rank: #{market_cap_rank}\n\n"

        return result_text
    except Exception as e:
        logger.error(f"Error searching tokens: {e}")
        return f"Error: Unable to search tokens. {str(e)}"


@tool
def compare_token_prices(token_ids: str) -> str:
    """
    Compare prices of multiple cryptocurrencies.

    Args:
        token_ids: Comma-separated CoinGecko token IDs (e.g., 'ethereum,bitcoin,solana')

    Returns:
        Side-by-side price comparison

    Example:
        compare_token_prices('ethereum,bitcoin,cardano')
    """
    try:
        from defiagents.dataflows.defi.coingecko import get_api_instance

        api = get_api_instance()
        ids = [tid.strip() for tid in token_ids.split(',')]

        prices = api.get_token_price(
            ids,
            ['usd'],
            include_market_cap=True,
            include_24h_vol=True,
            include_24h_change=True
        )

        result = f"## Price Comparison\n\n"
        result += f"Comparing {len(ids)} tokens: {', '.join(ids)}\n\n"

        for token_id in ids:
            if token_id not in prices:
                result += f"### {token_id.title()}\n"
                result += "- **Status**: Data not available\n\n"
                continue

            data = prices[token_id]
            price = data.get('usd', 0)
            market_cap = data.get('usd_market_cap', 0)
            volume = data.get('usd_24h_vol', 0)
            change = data.get('usd_24h_change', 0)

            price_str = f"${price:,.2f}" if price < 1000 else f"${price:,.0f}"

            if market_cap >= 1e9:
                mcap_str = f"${market_cap/1e9:.2f}B"
            elif market_cap >= 1e6:
                mcap_str = f"${market_cap/1e6:.2f}M"
            else:
                mcap_str = f"${market_cap:,.0f}"

            if volume >= 1e9:
                vol_str = f"${volume/1e9:.2f}B"
            elif volume >= 1e6:
                vol_str = f"${volume/1e6:.2f}M"
            else:
                vol_str = f"${volume:,.0f}"

            change_icon = "📈" if change >= 0 else "📉"

            result += f"### {token_id.title()}\n"
            result += f"- **Price**: {price_str}\n"
            result += f"- **24h Change**: {change_icon} {change:+.2f}%\n"
            result += f"- **Market Cap**: {mcap_str}\n"
            result += f"- **24h Volume**: {vol_str}\n\n"

        return result
    except Exception as e:
        logger.error(f"Error comparing prices: {e}")
        return f"Error: Unable to compare token prices. {str(e)}"


@tool
def get_trending_tokens() -> str:
    """
    Get currently trending cryptocurrencies (top 7).

    Returns:
        List of trending tokens

    Example:
        get_trending_tokens()
    """
    try:
        from defiagents.dataflows.defi.coingecko import get_api_instance

        api = get_api_instance()
        trending = api.get_trending_tokens()

        coins = trending.get('coins', [])

        result = "## Trending Cryptocurrencies\n\n"

        for i, item in enumerate(coins, 1):
            coin = item.get('item', {})
            name = coin.get('name', 'Unknown')
            symbol = coin.get('symbol', '').upper()
            market_cap_rank = coin.get('market_cap_rank', 'N/A')
            price_btc = coin.get('price_btc', 0)

            result += f"{i}. **{name}** ({symbol})\n"
            result += f"   - Market Cap Rank: #{market_cap_rank}\n"
            result += f"   - Price (BTC): {price_btc:.8f} BTC\n\n"

        return result
    except Exception as e:
        logger.error(f"Error getting trending tokens: {e}")
        return f"Error: Unable to fetch trending tokens. {str(e)}"


@tool
def get_global_defi_metrics() -> str:
    """
    Get global DeFi market metrics (market cap, volume, dominance).

    Returns:
        Global DeFi statistics

    Example:
        get_global_defi_metrics()
    """
    try:
        from defiagents.dataflows.defi.coingecko import get_api_instance

        api = get_api_instance()
        data = api.get_global_defi_data()

        defi_market_cap = data.get('defi_market_cap', 0)
        eth_market_cap = data.get('eth_market_cap', 0)
        defi_to_eth_ratio = data.get('defi_to_eth_ratio', 0)
        trading_volume_24h = data.get('trading_volume_24h', 0)
        defi_dominance = data.get('defi_dominance', 0)

        result = "## Global DeFi Metrics\n\n"

        if defi_market_cap >= 1e9:
            mcap_str = f"${defi_market_cap/1e9:.2f}B"
        else:
            mcap_str = f"${defi_market_cap/1e6:.2f}M"

        if eth_market_cap >= 1e9:
            eth_mcap_str = f"${eth_market_cap/1e9:.2f}B"
        else:
            eth_mcap_str = f"${eth_market_cap/1e6:.2f}M"

        if trading_volume_24h >= 1e9:
            vol_str = f"${trading_volume_24h/1e9:.2f}B"
        else:
            vol_str = f"${trading_volume_24h/1e6:.2f}M"

        result += f"**DeFi Market Cap**: {mcap_str}\n"
        result += f"**ETH Market Cap**: {eth_mcap_str}\n"
        result += f"**DeFi/ETH Ratio**: {defi_to_eth_ratio:.2f}%\n"
        result += f"**24h Trading Volume**: {vol_str}\n"
        result += f"**DeFi Dominance**: {defi_dominance:.2f}%\n"

        return result
    except Exception as e:
        logger.error(f"Error getting global DeFi metrics: {e}")
        return f"Error: Unable to fetch global DeFi metrics. {str(e)}"


@tool
def get_token_by_contract(contract_address: str, chain: str = "ethereum") -> str:
    """
    Get token data by contract address.

    Args:
        contract_address: Token contract address
        chain: Platform ID (e.g., 'ethereum', 'arbitrum-one', 'optimistic-ethereum', 'polygon-pos')

    Returns:
        Token information including price and market data

    Example:
        get_token_by_contract('0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', chain='ethereum')
    """
    try:
        from defiagents.dataflows.defi.coingecko import get_api_instance

        # Map common chain names to CoinGecko platform IDs
        chain_map = {
            "ethereum": "ethereum",
            "arbitrum": "arbitrum-one",
            "optimism": "optimistic-ethereum",
            "polygon": "polygon-pos",
            "base": "base",
            "bsc": "binance-smart-chain",
            "avalanche": "avalanche",
        }

        platform_id = chain_map.get(chain.lower(), chain)

        api = get_api_instance()
        data = api.get_token_contract_data(platform_id, contract_address)

        name = data.get('name', 'Unknown')
        symbol = data.get('symbol', '').upper()
        token_id = data.get('id', '')

        market_data = data.get('market_data', {})
        price = market_data.get('current_price', {}).get('usd', 0)
        market_cap = market_data.get('market_cap', {}).get('usd', 0)
        volume = market_data.get('total_volume', {}).get('usd', 0)

        result = f"## {name} ({symbol})\n\n"
        result += f"**Token ID**: `{token_id}`\n"
        result += f"**Contract**: `{contract_address}`\n"
        result += f"**Chain**: {chain.title()}\n\n"

        if price:
            result += f"**Price**: ${price:,.6f}\n"
        if market_cap:
            mcap_str = f"${market_cap/1e9:.2f}B" if market_cap >= 1e9 else f"${market_cap/1e6:.2f}M"
            result += f"**Market Cap**: {mcap_str}\n"
        if volume:
            vol_str = f"${volume/1e9:.2f}B" if volume >= 1e9 else f"${volume/1e6:.2f}M"
            result += f"**24h Volume**: {vol_str}\n"

        return result
    except Exception as e:
        logger.error(f"Error getting token by contract: {e}")
        return f"Error: Unable to fetch token data by contract. {str(e)}"


# Tool list for easy registration
MARKET_TOOLS = [
    get_crypto_price,
    get_crypto_market_data,
    search_crypto_tokens,
    compare_token_prices,
    get_trending_tokens,
    get_global_defi_metrics,
    get_token_by_contract,
]
