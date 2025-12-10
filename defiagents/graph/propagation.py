# TradingAgents/graph/propagation.py

import logging
from typing import Dict, Any
from defiagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)
from defiagents.security.protocol_whitelist import ProtocolWhitelist, WhitelistResult

logger = logging.getLogger(__name__)


class Propagator:
    """Handles state initialization and propagation through the graph."""

    def __init__(self, max_recur_limit=100, whitelist: ProtocolWhitelist | None = None):
        """Initialize with configuration parameters."""
        self.max_recur_limit = max_recur_limit
        self.whitelist = whitelist or ProtocolWhitelist()

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

        whitelist_result: WhitelistResult | None = None
        try:
            whitelist_result = self.whitelist.check(target, chain)
        except Exception as exc:  # pragma: no cover - defensive downgrade
            logger.warning("Whitelist check failed for %s: %s", target, exc)

        messages = [("human", target)]
        if whitelist_result and whitelist_result.get("status") == "suspicious":
            warning_reason = whitelist_result.get("reason") or "protocol flagged as suspicious"
            safe_name = whitelist_result.get("protocol_slug") or target or "unknown protocol"
            warning = f"⚠️ Safety notice: {safe_name} flagged as suspicious. Reason: {warning_reason}"
            role, content = messages[0]
            messages[0] = (role, f"{content}\n\n{warning}")

        return {
            "messages": messages,
            # DeFi-specific parameters (NEW)
            "protocol_of_interest": target,
            "chain": chain,
            "investment_amount": investment_amount,
            "protocol_whitelist_status": (whitelist_result or {}).get("status") if whitelist_result else None,
            "whitelist_result": whitelist_result,
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
