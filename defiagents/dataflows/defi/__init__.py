"""
DeFi data sources integration module.

This module provides integrations with various DeFi data providers:
- DeFi Llama: Protocol TVL, APY, and general DeFi metrics
- The Graph: On-chain data via GraphQL subgraphs
- CoinGecko: Token prices and market data
- On-chain RPC: Direct blockchain data access via Web3.py
- Curve Finance: Official API for Curve pools and APY
- Yearn Finance: yDaemon API for vault data and APY
- Beefy Finance: Official API for yield optimizer vaults
- GMX: Official API for perpetual trading and GLP data
- PancakeSwap: Official API for BNB Chain DEX data

Usage:
    from defiagents.dataflows.defi import (
        get_protocol_tvl,
        get_token_price,
        get_uniswap_pools,
        get_block_number,
        get_curve_pools,
        get_yearn_vaults,
        get_beefy_vaults,
        get_gmx_stats,
        get_pancake_pairs,
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

# Curve Finance API
from .curve_api import (
    CurveAPI,
    get_curve_client,
    get_curve_pools,
    get_curve_pool_apy,
    format_curve_pool,
)

# Yearn Finance API
from .yearn_api import (
    YearnAPI,
    get_yearn_client,
    get_yearn_vaults,
    get_yearn_vault_apy,
    format_yearn_vault,
)

# Beefy Finance API
from .beefy_api import (
    BeefyAPI,
    get_beefy_client,
    get_beefy_vaults,
    get_beefy_vault_apy,
    format_beefy_vault,
)

# GMX API
from .gmx_api import (
    GMXAPI,
    get_gmx_client,
    get_gmx_glp_data,
    get_gmx_stats,
    format_gmx_data,
)

# PancakeSwap API
from .pancakeswap_api import (
    PancakeSwapAPI,
    get_pancakeswap_client,
    get_pancake_pairs,
    get_pancake_token_price,
    format_pancake_pair,
    format_pancake_summary,
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
    # Curve Finance
    "CurveAPI",
    "get_curve_client",
    "get_curve_pools",
    "get_curve_pool_apy",
    "format_curve_pool",
    # Yearn Finance
    "YearnAPI",
    "get_yearn_client",
    "get_yearn_vaults",
    "get_yearn_vault_apy",
    "format_yearn_vault",
    # Beefy Finance
    "BeefyAPI",
    "get_beefy_client",
    "get_beefy_vaults",
    "get_beefy_vault_apy",
    "format_beefy_vault",
    # GMX
    "GMXAPI",
    "get_gmx_client",
    "get_gmx_glp_data",
    "get_gmx_stats",
    "format_gmx_data",
    # PancakeSwap
    "PancakeSwapAPI",
    "get_pancakeswap_client",
    "get_pancake_pairs",
    "get_pancake_token_price",
    "format_pancake_pair",
    "format_pancake_summary",
]
