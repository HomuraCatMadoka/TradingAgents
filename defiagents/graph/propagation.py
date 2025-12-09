# TradingAgents/graph/propagation.py

from typing import Dict, Any
from defiagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)


class Propagator:
    """Handles state initialization and propagation through the graph."""

    def __init__(self, max_recur_limit=100):
        """Initialize with configuration parameters."""
        self.max_recur_limit = max_recur_limit

    def create_initial_state(
        self,
        company_name: str,
        trade_date: str,
        protocol_of_interest: str = None,
        chain: str = "ethereum",
        investment_amount: float = None
    ) -> Dict[str, Any]:
        """Create the initial state for the agent graph.

        Args:
            company_name: Stock ticker (legacy) or protocol name
            trade_date: Date of analysis
            protocol_of_interest: DeFi protocol slug (NEW - for DeFi analysis)
            chain: Blockchain network (NEW - for DeFi analysis)
            investment_amount: Investment amount in USD (NEW - for DeFi strategy analysis)

        Returns:
            Initial state dictionary for the agent graph
        """
        # Use protocol_of_interest if provided, otherwise use company_name for backward compatibility
        target = protocol_of_interest if protocol_of_interest else company_name

        return {
            "messages": [("human", target)],
            # DeFi-specific parameters (NEW)
            "protocol_of_interest": target,
            "chain": chain,
            "investment_amount": investment_amount,
            # Legacy compatibility
            "company_of_interest": company_name,
            "trade_date": str(trade_date),
            # Debate states
            "investment_debate_state": InvestDebateState(
                {"history": "", "current_response": "", "count": 0}
            ),
            "risk_debate_state": RiskDebateState(
                {
                    "history": "",
                    "current_risky_response": "",
                    "current_safe_response": "",
                    "current_neutral_response": "",
                    "count": 0,
                }
            ),
            # Analyst reports
            "market_report": "",
            "fundamentals_report": "",
            "sentiment_report": "",
            "news_report": "",
            # New DeFi analyst reports
            "yield_report": "",
            "risk_report": "",
        }

    def get_graph_args(self) -> Dict[str, Any]:
        """Get arguments for the graph invocation."""
        return {
            "stream_mode": "values",
            "config": {"recursion_limit": self.max_recur_limit},
        }
