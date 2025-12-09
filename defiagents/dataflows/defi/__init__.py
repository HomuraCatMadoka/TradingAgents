"""
DeFi data sources integration module.

This module provides integrations with various DeFi data providers:
- DeFi Llama: Protocol TVL, APY, and general DeFi metrics
- The Graph: On-chain data via GraphQL subgraphs
- CoinGecko: Token prices and market data
- On-chain RPC: Direct blockchain data access via Web3.py

Usage:
    from defiagents.dataflows.defi import (
        get_protocol_tvl,
        get_token_price,
        get_uniswap_pools,
        get_block_number,
    )
"""

# DeFi Llama API
from .defillama import (
    DefiLlamaAPI,
    get_protocol_tvl,
    get_protocol_info,
    get_all_protocols,
    get_chains_tvl,
    format_protocol_summary,
)

# The Graph subgraphs
from .the_graph import (
    TheGraphClient,
    query_subgraph,
    get_uniswap_pools,
    get_uniswap_pool_by_id,
    get_aave_reserves,
    get_aave_reserve_by_symbol,
    format_uniswap_pool,
    format_aave_reserve,
)

# On-chain data (Web3.py)
from .onchain import (
    OnChainClient,
    get_contract_data,
    get_token_balance,
    get_block_number,
    format_gas_price,
    format_token_balance,
)

# CoinGecko API
from .coingecko import (
    CoinGeckoAPI,
    get_token_price,
    get_token_market_data,
    search_tokens,
    format_token_price,
    format_market_data,
)

__all__ = [
    # DeFi Llama
    "DefiLlamaAPI",
    "get_protocol_tvl",
    "get_protocol_info",
    "get_all_protocols",
    "get_chains_tvl",
    "format_protocol_summary",
    # The Graph
    "TheGraphClient",
    "query_subgraph",
    "get_uniswap_pools",
    "get_uniswap_pool_by_id",
    "get_aave_reserves",
    "get_aave_reserve_by_symbol",
    "format_uniswap_pool",
    "format_aave_reserve",
    # On-chain
    "OnChainClient",
    "get_contract_data",
    "get_token_balance",
    "get_block_number",
    "format_gas_price",
    "format_token_balance",
    # CoinGecko
    "CoinGeckoAPI",
    "get_token_price",
    "get_token_market_data",
    "search_tokens",
    "format_token_price",
    "format_market_data",
]
