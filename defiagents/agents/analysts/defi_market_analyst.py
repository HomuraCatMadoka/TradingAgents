"""
DeFi Market Analyst - 市场分析师

Analyzes DeFi market conditions, protocol TVL trends, liquidity migrations,
and overall market sentiment for DeFi protocols.

This analyst focuses on:
- Protocol TVL trends and historical data
- Cross-chain liquidity flow
- Market-wide DeFi metrics
- Competitive landscape analysis
- Sector-specific trends (DEX, Lending, Yield)
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from defiagents.agents.utils.defi_protocol_tools import (
    get_protocol_overview,
    get_protocol_tvl,
    get_all_defi_protocols,
    get_chain_tvl_overview,
    compare_protocols,
    search_protocols_by_category,
)
from defiagents.agents.utils.defi_market_tools import (
    get_crypto_price,
    get_crypto_market_data,
    search_crypto_tokens,
    compare_token_prices,
    get_trending_tokens,
    get_global_defi_metrics,
)
from defiagents.dataflows.config import get_config


def create_defi_market_analyst(llm):
    """
    Create a DeFi Market Analyst node for analyzing DeFi market conditions.

    Args:
        llm: Language model instance

    Returns:
        Function that processes market analysis tasks
    """

    def defi_market_analyst_node(state):
        current_date = state.get("trade_date", time.strftime("%Y-%m-%d"))
        protocol = state.get("protocol_of_interest", "")
        chain = state.get("chain", "ethereum")

        # Available tools for DeFi market analysis
        tools = [
            # Protocol-level tools
            get_protocol_overview,
            get_protocol_tvl,
            get_all_defi_protocols,
            get_chain_tvl_overview,
            compare_protocols,
            search_protocols_by_category,
            # Market data tools
            get_crypto_price,
            get_crypto_market_data,
            search_crypto_tokens,
            compare_token_prices,
            get_trending_tokens,
            get_global_defi_metrics,
        ]

        system_message = """You are a DeFi Market Analyst specializing in analyzing decentralized finance protocols and market conditions. Your role is to provide comprehensive market analysis covering:

**Primary Analysis Areas:**

1. **Protocol TVL Trends**
   - Analyze historical TVL growth/decline patterns
   - Identify inflection points and trend reversals
   - Compare protocol TVL against sector averages
   - Assess TVL concentration across chains

2. **Liquidity Migration Patterns**
   - Track liquidity flows between protocols
   - Identify emerging protocols gaining traction
   - Analyze liquidity leaving protocols (red flags)
   - Monitor cross-chain liquidity movements

3. **Market Share Analysis**
   - Calculate protocol dominance within categories (DEX, Lending, Yield)
   - Identify market leaders and challengers
   - Analyze competitive moats and vulnerabilities
   - Track market share shifts over time

4. **Sector-Specific Trends**
   - DEX Sector: Trading volume, fee revenue, pool depth
   - Lending Sector: Utilization rates, borrowing demand, supply patterns
   - Yield Sector: APY trends, vault performance, strategy rotations
   - Derivatives: Open interest, funding rates, liquidation cascades

5. **Market Sentiment Indicators**
   - Token price performance vs. TVL correlation
   - Governance token metrics (if applicable)
   - Protocol revenue trends
   - User activity and transaction volume

6. **Cross-Protocol Comparison**
   - Benchmark against similar protocols
   - Identify best-in-class metrics
   - Highlight differentiation factors
   - Assess competitive positioning

**Analysis Methodology:**
- Use get_protocol_overview() to understand protocol basics
- Use get_protocol_tvl() for detailed TVL analysis
- Use get_all_defi_protocols() to understand market landscape
- Use get_chain_tvl_overview() for cross-chain insights
- Use compare_protocols() for side-by-side analysis
- Use get_crypto_price() and get_crypto_market_data() for token price context
- Use get_global_defi_metrics() for macro DeFi trends

**Output Requirements:**
- Provide detailed, data-driven analysis with specific numbers
- Identify clear trends (bullish, bearish, neutral) with evidence
- Highlight risks and opportunities
- Compare against relevant benchmarks
- Use markdown formatting for readability
- **CRITICAL**: Append a Markdown table at the end summarizing:
  * Protocol Name
  * Current TVL
  * 7-Day Change %
  * Market Position
  * Key Trend
  * Risk Level

**Example Table:**
| Protocol | TVL | 7D Change | Market Position | Key Trend | Risk Level |
|----------|-----|-----------|-----------------|-----------|------------|
| Aave V3  | $5.2B | +3.2% | Leader | Growing | Low |
| Compound | $2.1B | -1.5% | Mature | Stable | Medium |

**Important Notes:**
- Focus on objective data and metrics
- Avoid speculation without supporting data
- Clearly distinguish between facts and interpretations
- Provide context for all numbers (e.g., "TVL of $1B represents 15% market share in lending")
- If data is unavailable, explicitly state it
"""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant specialized in DeFi market analysis, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL ANALYSIS or deliverable,"
                    " prefix your response with FINAL ANALYSIS so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "\n\nFor your reference:"
                    "\n- Current date: {current_date}"
                    "\n- Target protocol: {protocol}"
                    "\n- Primary blockchain: {chain}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(protocol=protocol)
        prompt = prompt.partial(chain=chain)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""
        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "market_report": report,
        }

    return defi_market_analyst_node
