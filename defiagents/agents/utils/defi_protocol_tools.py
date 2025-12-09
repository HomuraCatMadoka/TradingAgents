"""
DeFi Protocol Analysis Tools.

Provides LangChain tools for analyzing DeFi protocols including TVL,
yield rates, risk metrics, and protocol fundamentals.
"""

import logging
from langchain_core.tools import tool
from typing import Optional

logger = logging.getLogger(__name__)


@tool
def get_protocol_overview(protocol_slug: str) -> str:
    """
    Get comprehensive overview of a DeFi protocol including TVL, chains, and category.

    Args:
        protocol_slug: Protocol identifier (e.g., 'aave-v3', 'uniswap-v3', 'lido')

    Returns:
        Formatted protocol overview with TVL, supported chains, and description

    Example:
        get_protocol_overview('aave-v3')
    """
    try:
        from defiagents.dataflows.defi import get_protocol_info, format_protocol_summary

        protocol_data = get_protocol_info(protocol_slug)
        return format_protocol_summary(protocol_data)
    except Exception as e:
        logger.error(f"Error getting protocol overview: {e}")
        return f"Error: Unable to fetch protocol data for '{protocol_slug}'. {str(e)}"


@tool
def get_protocol_tvl(protocol_slug: str) -> str:
    """
    Get current Total Value Locked (TVL) for a specific DeFi protocol.

    Args:
        protocol_slug: Protocol identifier (e.g., 'aave-v3', 'curve', 'gmx')

    Returns:
        Current TVL value formatted in billions or millions

    Example:
        get_protocol_tvl('lido')
    """
    try:
        from defiagents.dataflows.defi import get_protocol_tvl as fetch_tvl

        tvl = fetch_tvl(protocol_slug)

        if tvl >= 1e9:
            tvl_str = f"${tvl/1e9:.2f}B"
        elif tvl >= 1e6:
            tvl_str = f"${tvl/1e6:.2f}M"
        else:
            tvl_str = f"${tvl:,.0f}"

        return f"**{protocol_slug}** current TVL: {tvl_str}"
    except Exception as e:
        logger.error(f"Error getting protocol TVL: {e}")
        return f"Error: Unable to fetch TVL for '{protocol_slug}'. {str(e)}"


@tool
def get_all_defi_protocols(limit: int = 50) -> str:
    """
    Get list of top DeFi protocols by TVL.

    Args:
        limit: Number of protocols to return (default: 50, max: 100)

    Returns:
        Formatted list of protocols with TVL and categories

    Example:
        get_all_defi_protocols(limit=20)
    """
    try:
        from defiagents.dataflows.defi import get_all_protocols

        protocols = get_all_protocols()

        # Sort by TVL and limit
        sorted_protocols = sorted(
            protocols,
            key=lambda x: x.get('tvl', 0),
            reverse=True
        )[:min(limit, 100)]

        result = f"## Top {len(sorted_protocols)} DeFi Protocols by TVL\n\n"

        for i, protocol in enumerate(sorted_protocols, 1):
            name = protocol.get('name', 'Unknown')
            slug = protocol.get('slug', '')
            tvl = protocol.get('tvl', 0)
            category = protocol.get('category', 'Unknown')
            chains = protocol.get('chains', [])

            if tvl >= 1e9:
                tvl_str = f"${tvl/1e9:.2f}B"
            elif tvl >= 1e6:
                tvl_str = f"${tvl/1e6:.2f}M"
            else:
                tvl_str = f"${tvl:,.0f}"

            chain_str = ", ".join(chains[:3])
            if len(chains) > 3:
                chain_str += f" +{len(chains) - 3} more"

            result += f"{i}. **{name}** (`{slug}`)\n"
            result += f"   - TVL: {tvl_str}\n"
            result += f"   - Category: {category}\n"
            result += f"   - Chains: {chain_str}\n\n"

        return result
    except Exception as e:
        logger.error(f"Error getting all protocols: {e}")
        return f"Error: Unable to fetch protocol list. {str(e)}"


@tool
def get_chain_tvl_overview() -> str:
    """
    Get TVL overview across all blockchain networks.

    Returns:
        Formatted list of chains with their total TVL

    Example:
        get_chain_tvl_overview()
    """
    try:
        from defiagents.dataflows.defi import get_chains_tvl

        chains = get_chains_tvl()

        result = "## Blockchain TVL Overview\n\n"

        for chain in chains[:15]:  # Top 15 chains
            name = chain.get('name', 'Unknown')
            tvl = chain.get('tvl', 0)
            token_symbol = chain.get('tokenSymbol', '')

            if tvl >= 1e9:
                tvl_str = f"${tvl/1e9:.2f}B"
            elif tvl >= 1e6:
                tvl_str = f"${tvl/1e6:.2f}M"
            else:
                tvl_str = f"${tvl:,.0f}"

            result += f"- **{name}** ({token_symbol}): {tvl_str}\n"

        return result
    except Exception as e:
        logger.error(f"Error getting chain TVL: {e}")
        return f"Error: Unable to fetch chain TVL data. {str(e)}"


@tool
def compare_protocols(protocol_slugs: str) -> str:
    """
    Compare multiple DeFi protocols side-by-side.

    Args:
        protocol_slugs: Comma-separated protocol identifiers (e.g., 'aave-v3,compound-v3,radiant')

    Returns:
        Comparison table with TVL, categories, and chains

    Example:
        compare_protocols('aave-v3,compound-v3,morpho')
    """
    try:
        from defiagents.dataflows.defi import get_protocol_info

        slugs = [s.strip() for s in protocol_slugs.split(',')]

        result = f"## Protocol Comparison\n\n"
        result += f"Comparing {len(slugs)} protocols: {', '.join(slugs)}\n\n"

        for slug in slugs:
            try:
                data = get_protocol_info(slug)
                name = data.get('name', slug)
                tvl = data.get('tvl', 0)
                category = data.get('category', 'Unknown')
                chains = data.get('chains', [])

                if tvl >= 1e9:
                    tvl_str = f"${tvl/1e9:.2f}B"
                elif tvl >= 1e6:
                    tvl_str = f"${tvl/1e6:.2f}M"
                else:
                    tvl_str = f"${tvl:,.0f}"

                result += f"### {name}\n"
                result += f"- **Slug**: `{slug}`\n"
                result += f"- **TVL**: {tvl_str}\n"
                result += f"- **Category**: {category}\n"
                result += f"- **Chains**: {', '.join(chains)}\n\n"

            except Exception as e:
                result += f"### {slug}\n"
                result += f"- **Error**: Could not fetch data ({str(e)})\n\n"

        return result
    except Exception as e:
        logger.error(f"Error comparing protocols: {e}")
        return f"Error: Unable to compare protocols. {str(e)}"


@tool
def search_protocols_by_category(category: str) -> str:
    """
    Search for DeFi protocols by category.

    Args:
        category: Protocol category (e.g., 'Lending', 'DEX', 'Liquid Staking', 'Yield')

    Returns:
        List of protocols in the specified category

    Example:
        search_protocols_by_category('Lending')
    """
    try:
        from defiagents.dataflows.defi import get_all_protocols

        protocols = get_all_protocols()

        # Filter by category (case-insensitive partial match)
        filtered = [
            p for p in protocols
            if category.lower() in p.get('category', '').lower()
        ]

        # Sort by TVL
        filtered = sorted(filtered, key=lambda x: x.get('tvl', 0), reverse=True)

        result = f"## {category} Protocols ({len(filtered)} found)\n\n"

        for i, protocol in enumerate(filtered[:20], 1):  # Top 20
            name = protocol.get('name', 'Unknown')
            slug = protocol.get('slug', '')
            tvl = protocol.get('tvl', 0)

            if tvl >= 1e9:
                tvl_str = f"${tvl/1e9:.2f}B"
            elif tvl >= 1e6:
                tvl_str = f"${tvl/1e6:.2f}M"
            else:
                tvl_str = f"${tvl:,.0f}"

            result += f"{i}. **{name}** (`{slug}`) - TVL: {tvl_str}\n"

        return result
    except Exception as e:
        logger.error(f"Error searching protocols: {e}")
        return f"Error: Unable to search protocols by category. {str(e)}"


# Tool list for easy registration
PROTOCOL_TOOLS = [
    get_protocol_overview,
    get_protocol_tvl,
    get_all_defi_protocols,
    get_chain_tvl_overview,
    compare_protocols,
    search_protocols_by_category,
]
