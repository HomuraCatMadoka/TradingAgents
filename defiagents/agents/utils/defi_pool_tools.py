"""
DeFi Liquidity Pool Analysis Tools.

Provides LangChain tools for analyzing DEX pools, lending markets,
and yield opportunities.
"""

import logging
from langchain_core.tools import tool
from typing import Optional

logger = logging.getLogger(__name__)


def _get_subgraph_id(protocol: str, chain: str) -> str:
    """
    Get correct subgraph deployment ID from config.

    Args:
        protocol: Protocol name ('uniswap_v3', 'aave_v3')
        chain: Chain name ('ethereum', 'arbitrum', etc.)

    Returns:
        Deployment ID string
    """
    try:
        from defiagents.dataflows.config import get_config
        config = get_config()
        subgraph_key = f"{protocol}_{chain}"
        return config.get("the_graph", {}).get("subgraphs", {}).get(subgraph_key, "")
    except Exception as e:
        logger.error(f"Error getting subgraph ID for {protocol}/{chain}: {e}")
        return ""



@tool
def get_uniswap_top_pools(chain: str = "ethereum", limit: int = 10) -> str:
    """
    Get top Uniswap V3 pools by TVL.

    Args:
        chain: Blockchain network ('ethereum', 'arbitrum', 'optimism', 'base', 'polygon')
        limit: Number of pools to return (default: 10, max: 50)

    Returns:
        Formatted list of top pools with TVL, volume, and fee tiers

    Example:
        get_uniswap_top_pools(chain='arbitrum', limit=5)
    """
    try:
        from defiagents.dataflows.defi import get_uniswap_pools, format_uniswap_pool

        # Get subgraph deployment ID from config
        subgraph_id = _get_subgraph_id("uniswap_v3", chain.lower())

        if not subgraph_id:
            return f"❌ Uniswap V3 subgraph not configured for {chain}"

        pools = get_uniswap_pools(
            subgraph_id=subgraph_id,
            limit=min(limit, 50),
            order_by="totalValueLockedUSD"
        )

        result = f"## Top {len(pools)} Uniswap V3 Pools on {chain.title()}\n\n"

        for i, pool in enumerate(pools, 1):
            token0 = pool.get('token0', {})
            token1 = pool.get('token1', {})
            tvl = pool.get('totalValueLockedUSD', 0)
            volume = pool.get('volumeUSD', 0)
            fee_tier = pool.get('feeTier', 0)

            tvl_str = f"${float(tvl):,.0f}" if tvl else "N/A"
            volume_str = f"${float(volume):,.0f}" if volume else "N/A"
            fee_pct = int(fee_tier) / 10000 if fee_tier else 0

            result += f"### {i}. {token0.get('symbol')}/{token1.get('symbol')}\n"
            result += f"- **Fee Tier**: {fee_pct}%\n"
            result += f"- **TVL**: {tvl_str}\n"
            result += f"- **Volume**: {volume_str}\n"
            result += f"- **Pool ID**: `{pool.get('id')}`\n\n"

        return result
    except Exception as e:
        logger.error(f"Error getting Uniswap pools: {e}")
        return f"Error: Unable to fetch Uniswap pools. {str(e)}"


@tool
def get_uniswap_pool_details(pool_address: str, chain: str = "ethereum") -> str:
    """
    Get detailed information about a specific Uniswap V3 pool including 7-day history.

    Args:
        pool_address: Pool contract address
        chain: Blockchain network

    Returns:
        Detailed pool data with historical metrics

    Example:
        get_uniswap_pool_details('0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640')
    """
    try:
        from defiagents.dataflows.defi import get_uniswap_pool_by_id, format_uniswap_pool

        # Get subgraph deployment ID from config
        subgraph_id = _get_subgraph_id("uniswap_v3", chain.lower())

        if not subgraph_id:
            return f"❌ Uniswap V3 subgraph not configured for {chain}"

        pool = get_uniswap_pool_by_id(pool_address, subgraph_id=subgraph_id)

        if not pool:
            return f"Pool {pool_address} not found on {chain}"

        # Format basic pool info
        result = format_uniswap_pool(pool)

        # Add historical data
        pool_day_data = pool.get('poolDayData', [])
        if pool_day_data:
            result += "\n## 7-Day Historical Data\n\n"
            for day in pool_day_data:
                date = day.get('date', 0)
                volume = day.get('volumeUSD', 0)
                tvl = day.get('tvlUSD', 0)
                fees = day.get('feesUSD', 0)

                volume_str = f"${float(volume):,.0f}" if volume else "N/A"
                tvl_str = f"${float(tvl):,.0f}" if tvl else "N/A"
                fees_str = f"${float(fees):,.0f}" if fees else "N/A"

                result += f"- **Date**: {date} | Volume: {volume_str} | TVL: {tvl_str} | Fees: {fees_str}\n"

        return result
    except Exception as e:
        logger.error(f"Error getting pool details: {e}")
        return f"Error: Unable to fetch pool details. {str(e)}"


@tool
def get_aave_lending_markets(chain: str = "ethereum", limit: int = 20) -> str:
    """
    Get Aave V3 lending markets (reserves) with current rates.

    Args:
        chain: Blockchain network ('ethereum', 'arbitrum', 'optimism', 'polygon', 'base')
        limit: Number of markets to return (default: 20, max: 50)

    Returns:
        Formatted list of lending markets with deposit/borrow APY

    Example:
        get_aave_lending_markets(chain='arbitrum', limit=10)
    """
    try:
        from defiagents.dataflows.defi import get_aave_reserves

        # Get subgraph deployment ID from config
        subgraph_id = _get_subgraph_id("aave_v3", chain.lower())

        if not subgraph_id:
            return f"❌ Aave V3 subgraph not configured for {chain}"

        reserves = get_aave_reserves(subgraph_id=subgraph_id, limit=min(limit, 50))

        result = f"## Aave V3 Lending Markets on {chain.title()}\n\n"
        result += f"Found {len(reserves)} assets\n\n"

        # Convert rates from Ray (27 decimals) to percentage
        def ray_to_percent(ray_value):
            if not ray_value:
                return 0.0
            return float(ray_value) / 1e27 * 100

        for reserve in reserves:
            symbol = reserve.get('symbol', 'Unknown')
            name = reserve.get('name', 'Unknown')

            deposit_apy = ray_to_percent(reserve.get('liquidityRate'))
            borrow_apy = ray_to_percent(reserve.get('variableBorrowRate'))
            utilization = ray_to_percent(reserve.get('utilizationRate'))

            total_liquidity = reserve.get('totalLiquidity', 0)
            available = reserve.get('availableLiquidity', 0)

            result += f"### {symbol} ({name})\n"
            result += f"- **Deposit APY**: {deposit_apy:.2f}%\n"
            result += f"- **Borrow APY**: {borrow_apy:.2f}%\n"
            result += f"- **Utilization**: {utilization:.2f}%\n"
            result += f"- **Total Liquidity**: {float(total_liquidity):,.0f} {symbol}\n"
            result += f"- **Available**: {float(available):,.0f} {symbol}\n\n"

        return result
    except Exception as e:
        logger.error(f"Error getting Aave markets: {e}")
        return f"Error: Unable to fetch Aave lending markets. {str(e)}"


@tool
def get_aave_asset_details(asset_symbol: str, chain: str = "ethereum") -> str:
    """
    Get detailed information about a specific Aave V3 asset.

    Args:
        asset_symbol: Asset symbol (e.g., 'USDC', 'ETH', 'WBTC')
        chain: Blockchain network

    Returns:
        Detailed asset data including rates, liquidity, and risk parameters

    Example:
        get_aave_asset_details('USDC', chain='arbitrum')
    """
    try:
        from defiagents.dataflows.defi import get_aave_reserve_by_symbol, format_aave_reserve

        # Get subgraph deployment ID from config
        subgraph_id = _get_subgraph_id("aave_v3", chain.lower())

        if not subgraph_id:
            return f"❌ Aave V3 subgraph not configured for {chain}"

        reserve = get_aave_reserve_by_symbol(asset_symbol, subgraph_id=subgraph_id)

        if not reserve:
            return f"Asset {asset_symbol} not found on {chain} Aave V3"

        result = format_aave_reserve(reserve)

        # Add risk parameters
        ltv = reserve.get('baseLTVasCollateral', 0)
        liquidation_threshold = reserve.get('liquidationThreshold', 0)
        liquidation_bonus = reserve.get('liquidationBonus', 0)

        result += "\n## Risk Parameters\n"
        result += f"- **Loan-to-Value (LTV)**: {float(ltv)/100:.2f}%\n"
        result += f"- **Liquidation Threshold**: {float(liquidation_threshold)/100:.2f}%\n"
        result += f"- **Liquidation Bonus**: {float(liquidation_bonus)/100:.2f}%\n"

        return result
    except Exception as e:
        logger.error(f"Error getting Aave asset details: {e}")
        return f"Error: Unable to fetch Aave asset details. {str(e)}"


@tool
def compare_yield_opportunities(asset_symbol: str) -> str:
    """
    Compare yield opportunities across different protocols for a specific asset.

    Args:
        asset_symbol: Asset symbol to compare (e.g., 'USDC', 'ETH', 'USDT')

    Returns:
        Comparison of APYs across different protocols and chains

    Example:
        compare_yield_opportunities('USDC')
    """
    try:
        from defiagents.dataflows.defi import get_aave_reserve_by_symbol

        result = f"## Yield Opportunities for {asset_symbol}\n\n"

        chains = ["ethereum", "arbitrum", "optimism", "polygon", "base"]
        opportunities = []

        def ray_to_percent(ray_value):
            if not ray_value:
                return 0.0
            return float(ray_value) / 1e27 * 100

        for chain in chains:
            try:
                # Get subgraph deployment ID from config
                subgraph_id = _get_subgraph_id("aave_v3", chain)

                if not subgraph_id:
                    continue  # Skip if not configured

                reserve = get_aave_reserve_by_symbol(asset_symbol, subgraph_id=subgraph_id)

                if reserve:
                    deposit_apy = ray_to_percent(reserve.get('liquidityRate'))
                    opportunities.append({
                        'protocol': 'Aave V3',
                        'chain': chain.title(),
                        'apy': deposit_apy,
                        'type': 'Lending'
                    })
            except:
                pass

        # Sort by APY
        opportunities = sorted(opportunities, key=lambda x: x['apy'], reverse=True)

        if not opportunities:
            return f"No yield opportunities found for {asset_symbol}"

        result += "### Top Opportunities (Sorted by APY)\n\n"
        for opp in opportunities:
            result += f"- **{opp['protocol']}** on **{opp['chain']}**: {opp['apy']:.2f}% APY ({opp['type']})\n"

        return result
    except Exception as e:
        logger.error(f"Error comparing yield opportunities: {e}")
        return f"Error: Unable to compare yield opportunities. {str(e)}"


# Tool list for easy registration
POOL_TOOLS = [
    get_uniswap_top_pools,
    get_uniswap_pool_details,
    get_aave_lending_markets,
    get_aave_asset_details,
    compare_yield_opportunities,
]
