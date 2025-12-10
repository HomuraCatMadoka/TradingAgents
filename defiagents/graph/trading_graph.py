# TradingAgents/graph/trading_graph.py

import os
from pathlib import Path
import json
from datetime import date
from typing import Dict, Any, Tuple, List, Optional

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.prebuilt import ToolNode

from defiagents.agents import *
from defiagents.default_config import DEFAULT_CONFIG
from defiagents.agents.utils.memory import FinancialSituationMemory
from defiagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)
from defiagents.dataflows.config import set_config

# Import the new abstract tool methods from agent_utils
from defiagents.agents.utils.agent_utils import (
    get_stock_data,
    get_indicators,
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement,
    get_news,
    get_insider_sentiment,
    get_insider_transactions,
    get_global_news
)

# Import DeFi-specific tools
from defiagents.agents.utils.defi_protocol_tools import (
    get_protocol_overview,
    get_protocol_tvl,
    get_all_defi_protocols,
    get_chain_tvl_overview,
    compare_protocols,
    search_protocols_by_category,
    get_compound_markets,
)
from defiagents.agents.utils.defi_pool_tools import (
    get_uniswap_top_pools,
    get_uniswap_pool_details,
    get_aave_lending_markets,
    get_aave_asset_details,
    compare_yield_opportunities,
)
from defiagents.agents.utils.defi_market_tools import (
    get_crypto_price,
    get_crypto_market_data,
    search_crypto_tokens,
    compare_token_prices,
    get_trending_tokens,
    get_global_defi_metrics,
    get_token_by_contract,
)
from defiagents.agents.utils.defi_wallet_tools import (
    get_native_balance,
    get_erc20_balance,
    get_token_info,
    get_wallet_portfolio,
    get_current_block,
    get_gas_price,
)

from .conditional_logic import ConditionalLogic
from .setup import GraphSetup
from .propagation import Propagator
from .reflection import Reflector
from .signal_processing import SignalProcessor


class TradingAgentsGraph:
    """Main class that orchestrates the trading agents framework."""

    def __init__(
        self,
        selected_analysts=["defi_market", "protocol", "yield", "risk"],
        debug=False,
        config: Dict[str, Any] = None,
    ):
        """Initialize the trading agents graph and components.

        Args:
            selected_analysts: List of analyst types to include.
                Default is DeFi analysts for DeFi analysis.
                Options: "defi_market", "protocol", "yield", "risk" (NEW DeFi analysts)
                         "market", "social", "news", "fundamentals" (legacy stock analysts)
            debug: Whether to run in debug mode
            config: Configuration dictionary. If None, uses default config
        """
        self.debug = debug
        self.config = config or DEFAULT_CONFIG

        # Update the interface's config
        set_config(self.config)

        # Create necessary directories
        os.makedirs(
            os.path.join(self.config["project_dir"], "dataflows/data_cache"),
            exist_ok=True,
        )

        # Initialize LLMs
        if self.config["llm_provider"].lower() == "openai" or self.config["llm_provider"] == "ollama" or self.config["llm_provider"] == "openrouter":
            self.deep_thinking_llm = ChatOpenAI(model=self.config["deep_think_llm"], base_url=self.config["backend_url"])
            self.quick_thinking_llm = ChatOpenAI(model=self.config["quick_think_llm"], base_url=self.config["backend_url"])
        elif self.config["llm_provider"].lower() == "anthropic":
            self.deep_thinking_llm = ChatAnthropic(model=self.config["deep_think_llm"], base_url=self.config["backend_url"])
            self.quick_thinking_llm = ChatAnthropic(model=self.config["quick_think_llm"], base_url=self.config["backend_url"])
        elif self.config["llm_provider"].lower() == "google":
            # 支持多 API Key 轮询
            google_api_keys = self.config.get("google_api_keys", [])

            if google_api_keys and len(google_api_keys) > 1:
                # 多 key 模式：使用轮询算法
                from defiagents.key_pool import get_next_google_api_key
                current_key = get_next_google_api_key(google_api_keys)

                if current_key:
                    logger.info(f"Using Google API Key pool ({len(google_api_keys)} keys), selected key: {current_key[:10]}...")
                else:
                    # 所有 key 都在冷却中，使用第一个并等待
                    current_key = google_api_keys[0]
                    logger.warning(f"All keys in cooldown, using first key with retry")
            else:
                # 单 key 模式（向后兼容）
                current_key = google_api_keys[0] if google_api_keys else None
                logger.info(f"Using single Google API Key: {current_key[:10] if current_key else 'None'}...")

            self.deep_thinking_llm = ChatGoogleGenerativeAI(
                model=self.config["deep_think_llm"],
                google_api_key=current_key
            )
            self.quick_thinking_llm = ChatGoogleGenerativeAI(
                model=self.config["quick_think_llm"],
                google_api_key=current_key
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config['llm_provider']}")
        
        # Initialize memories
        self.bull_memory = FinancialSituationMemory("bull_memory", self.config)
        self.bear_memory = FinancialSituationMemory("bear_memory", self.config)
        self.trader_memory = FinancialSituationMemory("trader_memory", self.config)
        self.invest_judge_memory = FinancialSituationMemory("invest_judge_memory", self.config)
        self.risk_manager_memory = FinancialSituationMemory("risk_manager_memory", self.config)

        # Create tool nodes
        self.tool_nodes = self._create_tool_nodes()

        # Initialize components
        self.conditional_logic = ConditionalLogic()
        self.graph_setup = GraphSetup(
            self.quick_thinking_llm,
            self.deep_thinking_llm,
            self.tool_nodes,
            self.bull_memory,
            self.bear_memory,
            self.trader_memory,
            self.invest_judge_memory,
            self.risk_manager_memory,
            self.conditional_logic,
        )

        self.propagator = Propagator()
        self.reflector = Reflector(self.quick_thinking_llm)
        self.signal_processor = SignalProcessor(self.quick_thinking_llm)

        # State tracking
        self.curr_state = None
        self.ticker = None
        self.log_states_dict = {}  # date to full state dict

        # Set up the graph
        self.graph = self.graph_setup.setup_graph(selected_analysts)

    def _create_tool_nodes(self) -> Dict[str, ToolNode]:
        """Create tool nodes for different data sources using abstract methods."""
        return {
            # Legacy stock analyst tool nodes
            "market": ToolNode(
                [
                    # Core stock data tools
                    get_stock_data,
                    # Technical indicators
                    get_indicators,
                ]
            ),
            "social": ToolNode(
                [
                    # News tools for social media analysis
                    get_news,
                ]
            ),
            "news": ToolNode(
                [
                    # News and insider information
                    get_news,
                    get_global_news,
                    get_insider_sentiment,
                    get_insider_transactions,
                ]
            ),
            "fundamentals": ToolNode(
                [
                    # Fundamental analysis tools
                    get_fundamentals,
                    get_balance_sheet,
                    get_cashflow,
                    get_income_statement,
                ]
            ),
            # New DeFi analyst tool nodes
            "defi_market": ToolNode(
                [
                    # Protocol data
                    get_protocol_overview,
                    get_protocol_tvl,
                    get_all_defi_protocols,
                    get_chain_tvl_overview,
                    compare_protocols,
                    get_compound_markets,
                    search_protocols_by_category,
                    # Market data
                    get_crypto_price,
                    get_crypto_market_data,
                    search_crypto_tokens,
                    compare_token_prices,
                    get_trending_tokens,
                    get_global_defi_metrics,
                ]
            ),
            "protocol": ToolNode(
                [
                    # Protocol analysis tools
                    get_protocol_overview,
                    get_protocol_tvl,
                    compare_protocols,
                    get_compound_markets,
                    # Token/market data
                    get_crypto_market_data,
                    get_token_by_contract,
                ]
            ),
            "yield": ToolNode(
                [
                    # Pool and lending analysis
                    get_uniswap_top_pools,
                    get_uniswap_pool_details,
                    get_aave_lending_markets,
                    get_aave_asset_details,
                    compare_yield_opportunities,
                    # Protocol comparison
                    get_protocol_overview,
                    compare_protocols,
                    # Price data
                    get_crypto_price,
                    compare_token_prices,
                ]
            ),
            "risk": ToolNode(
                [
                    # Protocol analysis
                    get_protocol_overview,
                    get_protocol_tvl,
                    compare_protocols,
                    # Pool details
                    get_uniswap_pool_details,
                    get_aave_asset_details,
                    # Market and system data
                    get_crypto_market_data,
                    get_global_defi_metrics,
                    get_current_block,
                    get_gas_price,
                ]
            ),
        }

    def propagate(self, company_name, trade_date):
        """Run the trading agents graph for a company on a specific date."""

        self.ticker = company_name

        # Initialize state
        init_agent_state = self.propagator.create_initial_state(
            company_name, trade_date
        )
        args = self.propagator.get_graph_args()

        if self.debug:
            # Debug mode with tracing
            trace = []
            for chunk in self.graph.stream(init_agent_state, **args):
                if len(chunk["messages"]) == 0:
                    pass
                else:
                    chunk["messages"][-1].pretty_print()
                    trace.append(chunk)

            final_state = trace[-1]
        else:
            # Standard mode without tracing
            final_state = self.graph.invoke(init_agent_state, **args)

        # Store current state for reflection
        self.curr_state = final_state

        # Log state
        self._log_state(trade_date, final_state)

        # Return decision and processed signal
        return final_state, self.process_signal(final_state["final_trade_decision"])

    def _log_state(self, trade_date, final_state):
        """Log the final state to a JSON file."""
        self.log_states_dict[str(trade_date)] = {
            "company_of_interest": final_state["company_of_interest"],
            "trade_date": final_state["trade_date"],
            "market_report": final_state["market_report"],
            "sentiment_report": final_state["sentiment_report"],
            "news_report": final_state["news_report"],
            "fundamentals_report": final_state["fundamentals_report"],
            "investment_debate_state": {
                "bull_history": final_state["investment_debate_state"]["bull_history"],
                "bear_history": final_state["investment_debate_state"]["bear_history"],
                "history": final_state["investment_debate_state"]["history"],
                "current_response": final_state["investment_debate_state"][
                    "current_response"
                ],
                "judge_decision": final_state["investment_debate_state"][
                    "judge_decision"
                ],
            },
            "trader_investment_decision": final_state["trader_investment_plan"],
            "risk_debate_state": {
                "risky_history": final_state["risk_debate_state"]["risky_history"],
                "safe_history": final_state["risk_debate_state"]["safe_history"],
                "neutral_history": final_state["risk_debate_state"]["neutral_history"],
                "history": final_state["risk_debate_state"]["history"],
                "judge_decision": final_state["risk_debate_state"]["judge_decision"],
            },
            "investment_plan": final_state["investment_plan"],
            "final_trade_decision": final_state["final_trade_decision"],
        }

        # Save to file
        directory = Path(f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/")
        directory.mkdir(parents=True, exist_ok=True)

        with open(
            f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/full_states_log_{trade_date}.json",
            "w",
        ) as f:
            json.dump(self.log_states_dict, f, indent=4)

    def reflect_and_remember(self, returns_losses):
        """Reflect on decisions and update memory based on returns."""
        self.reflector.reflect_bull_researcher(
            self.curr_state, returns_losses, self.bull_memory
        )
        self.reflector.reflect_bear_researcher(
            self.curr_state, returns_losses, self.bear_memory
        )
        self.reflector.reflect_trader(
            self.curr_state, returns_losses, self.trader_memory
        )
        self.reflector.reflect_invest_judge(
            self.curr_state, returns_losses, self.invest_judge_memory
        )
        self.reflector.reflect_risk_manager(
            self.curr_state, returns_losses, self.risk_manager_memory
        )

    def process_signal(self, full_signal):
        """Process a signal to extract the core decision."""
        return self.signal_processor.process_signal(full_signal)
