"""
DeFi Wallet Analysis Tools.

Provides LangChain tools for analyzing wallet holdings, balances,
and on-chain activity.
"""

import logging
from langchain_core.tools import tool
from typing import Optional

logger = logging.getLogger(__name__)


@tool
def get_native_balance(wallet_address: str, chain: str = "ethereum") -> str:
    """
    Get native token balance (ETH, etc.) for a wallet.

    Args:
        wallet_address: Wallet address (0x...)
        chain: Blockchain network ('ethereum', 'arbitrum', 'optimism', 'base', 'polygon')

    Returns:
        Native token balance in human-readable format

    Example:
        get_native_balance('0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb', chain='ethereum')
    """
    try:
        from defiagents.dataflows.defi.onchain import get_client_instance

        client = get_client_instance()
        balance_wei = client.get_balance(chain, wallet_address)

        if balance_wei is None:
            return f"Error: Unable to fetch balance for {wallet_address} on {chain}"

        # Convert wei to native token (e.g., ETH)
        balance = balance_wei / 1e18

        # Get token symbol
        token_symbols = {
            "ethereum": "ETH",
            "arbitrum": "ETH",
            "optimism": "ETH",
            "base": "ETH",
            "polygon": "MATIC",
            "bsc": "BNB",
            "avalanche": "AVAX",
        }
        token_symbol = token_symbols.get(chain.lower(), "TOKEN")

        result = f"## Native Balance on {chain.title()}\n\n"
        result += f"**Wallet**: `{wallet_address}`\n"
        result += f"**Balance**: {balance:.6f} {token_symbol}\n"
        result += f"**Value (Wei)**: {balance_wei:,}\n"

        return result
    except Exception as e:
        logger.error(f"Error getting native balance: {e}")
        return f"Error: Unable to fetch native balance. {str(e)}"


@tool
def get_erc20_balance(wallet_address: str, token_address: str, chain: str = "ethereum") -> str:
    """
    Get ERC20 token balance for a wallet.

    Args:
        wallet_address: Wallet address
        token_address: ERC20 token contract address
        chain: Blockchain network

    Returns:
        Token balance adjusted for decimals

    Example:
        get_erc20_balance(
            '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
            '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',  # USDC
            chain='ethereum'
        )
    """
    try:
        from defiagents.dataflows.defi.onchain import get_client_instance

        client = get_client_instance()

        # Get token info
        token_info = client.get_token_info(chain, token_address)
        if not token_info:
            return f"Error: Unable to fetch token info for {token_address}"

        # Get balance
        raw_balance = client.get_token_balance(chain, token_address, wallet_address)
        if raw_balance is None:
            return f"Error: Unable to fetch balance"

        # Adjust for decimals
        decimals = token_info['decimals']
        balance = raw_balance / (10 ** decimals)

        result = f"## {token_info['name']} ({token_info['symbol']}) Balance\n\n"
        result += f"**Wallet**: `{wallet_address}`\n"
        result += f"**Chain**: {chain.title()}\n"
        result += f"**Balance**: {balance:,.6f} {token_info['symbol']}\n"
        result += f"**Token Contract**: `{token_address}`\n"

        return result
    except Exception as e:
        logger.error(f"Error getting ERC20 balance: {e}")
        return f"Error: Unable to fetch ERC20 balance. {str(e)}"


@tool
def get_token_info(token_address: str, chain: str = "ethereum") -> str:
    """
    Get information about an ERC20 token (name, symbol, decimals, total supply).

    Args:
        token_address: Token contract address
        chain: Blockchain network

    Returns:
        Token information

    Example:
        get_token_info('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', chain='ethereum')  # USDC
    """
    try:
        from defiagents.dataflows.defi.onchain import get_client_instance

        client = get_client_instance()
        token_info = client.get_token_info(chain, token_address)

        if not token_info:
            return f"Error: Unable to fetch token info for {token_address} on {chain}"

        decimals = token_info['decimals']
        total_supply = token_info['total_supply'] / (10 ** decimals)

        result = f"## {token_info['name']} ({token_info['symbol']})\n\n"
        result += f"**Chain**: {chain.title()}\n"
        result += f"**Contract Address**: `{token_address}`\n"
        result += f"**Decimals**: {decimals}\n"
        result += f"**Total Supply**: {total_supply:,.2f} {token_info['symbol']}\n"

        return result
    except Exception as e:
        logger.error(f"Error getting token info: {e}")
        return f"Error: Unable to fetch token info. {str(e)}"


@tool
def get_wallet_portfolio(wallet_address: str, chain: str = "ethereum") -> str:
    """
    Get a simple portfolio overview for a wallet (native + common tokens).

    Args:
        wallet_address: Wallet address
        chain: Blockchain network

    Returns:
        Portfolio summary with native and major token balances

    Example:
        get_wallet_portfolio('0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb', chain='arbitrum')
    """
    try:
        from defiagents.dataflows.defi.onchain import get_client_instance

        client = get_client_instance()

        result = f"## Wallet Portfolio on {chain.title()}\n\n"
        result += f"**Address**: `{wallet_address}`\n\n"

        # Get native balance
        balance_wei = client.get_balance(chain, wallet_address)
        if balance_wei is not None:
            balance = balance_wei / 1e18
            token_symbols = {
                "ethereum": "ETH",
                "arbitrum": "ETH",
                "optimism": "ETH",
                "base": "ETH",
                "polygon": "MATIC",
            }
            token_symbol = token_symbols.get(chain.lower(), "TOKEN")
            result += f"### Native Token\n"
            result += f"- **{token_symbol}**: {balance:.6f}\n\n"

        # Common token addresses per chain
        common_tokens = {
            "ethereum": {
                "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            },
            "arbitrum": {
                "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
                "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
                "ARB": "0x912CE59144191C1204E64559FE8253a0e49E6548",
            },
            "optimism": {
                "USDC": "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85",
                "USDT": "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",
                "OP": "0x4200000000000000000000000000000000000042",
            },
        }

        tokens = common_tokens.get(chain.lower(), {})
        if tokens:
            result += "### ERC20 Tokens\n"
            for symbol, address in tokens.items():
                try:
                    token_info = client.get_token_info(chain, address)
                    if token_info:
                        raw_balance = client.get_token_balance(chain, address, wallet_address)
                        if raw_balance is not None and raw_balance > 0:
                            balance = raw_balance / (10 ** token_info['decimals'])
                            result += f"- **{symbol}**: {balance:,.6f}\n"
                except:
                    pass

        return result
    except Exception as e:
        logger.error(f"Error getting wallet portfolio: {e}")
        return f"Error: Unable to fetch wallet portfolio. {str(e)}"


@tool
def get_current_block(chain: str = "ethereum") -> str:
    """
    Get current block number for a chain.

    Args:
        chain: Blockchain network

    Returns:
        Current block number

    Example:
        get_current_block(chain='arbitrum')
    """
    try:
        from defiagents.dataflows.defi.onchain import get_client_instance

        client = get_client_instance()
        block_number = client.get_block_number(chain)

        if block_number is None:
            return f"Error: Unable to fetch block number for {chain}"

        result = f"## {chain.title()} Current Block\n\n"
        result += f"**Block Number**: {block_number:,}\n"

        return result
    except Exception as e:
        logger.error(f"Error getting current block: {e}")
        return f"Error: Unable to fetch current block. {str(e)}"


@tool
def get_gas_price(chain: str = "ethereum") -> str:
    """
    Get current gas price for a chain.

    Args:
        chain: Blockchain network

    Returns:
        Current gas price in Gwei

    Example:
        get_gas_price(chain='ethereum')
    """
    try:
        from defiagents.dataflows.defi.onchain import get_client_instance, format_gas_price

        client = get_client_instance()
        gas_price_wei = client.get_gas_price(chain)

        if gas_price_wei is None:
            return f"Error: Unable to fetch gas price for {chain}"

        return format_gas_price(chain, gas_price_wei)
    except Exception as e:
        logger.error(f"Error getting gas price: {e}")
        return f"Error: Unable to fetch gas price. {str(e)}"


# Tool list for easy registration
WALLET_TOOLS = [
    get_native_balance,
    get_erc20_balance,
    get_token_info,
    get_wallet_portfolio,
    get_current_block,
    get_gas_price,
]
