# TradingAgents/graph/setup.py

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode

from defiagents.agents import *
from defiagents.agents.utils.agent_states import AgentState

from .conditional_logic import ConditionalLogic
from .node_wrappers import wrap_agent_node_with_validation


class GraphSetup:
    """Handles the setup and configuration of the agent graph."""

    def __init__(
        self,
        quick_thinking_llm: ChatOpenAI,
        deep_thinking_llm: ChatOpenAI,
        tool_nodes: Dict[str, ToolNode],
        bull_memory,
        bear_memory,
        trader_memory,
        invest_judge_memory,
        risk_manager_memory,
        conditional_logic: ConditionalLogic,
    ):
        """Initialize with required components."""
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.tool_nodes = tool_nodes
        self.bull_memory = bull_memory
        self.bear_memory = bear_memory
        self.trader_memory = trader_memory
        self.invest_judge_memory = invest_judge_memory
        self.risk_manager_memory = risk_manager_memory
        self.conditional_logic = conditional_logic

    def setup_graph(
        self, selected_analysts=["defi_market", "protocol", "yield", "risk"]
    ):
        """Set up and compile the agent workflow graph.

        Args:
            selected_analysts (list): List of analyst types to include. Options are:
                - "market": Market analyst (legacy)
                - "social": Social media analyst
                - "news": News analyst
                - "fundamentals": Fundamentals analyst (legacy)
                - "defi_market": DeFi Market Analyst (NEW - recommended for DeFi)
                - "protocol": Protocol Fundamentals Analyst (NEW - DeFi protocols)
                - "yield": Yield Analyst (NEW - DeFi yield strategies)
                - "risk": DeFi Risk Analyst (NEW - DeFi-specific risks)
        """
        if len(selected_analysts) == 0:
            raise ValueError("Trading Agents Graph Setup Error: no analysts selected!")

        # Create analyst nodes
        analyst_nodes = {}
        delete_nodes = {}
        tool_nodes = {}

        def _wrap(node, agent_label: str, state_key: str):
            return wrap_agent_node_with_validation(node, agent_label, state_key)

        if "market" in selected_analysts:
            analyst_nodes["market"] = create_market_analyst(
                self.quick_thinking_llm
            )
            delete_nodes["market"] = create_msg_delete()
            tool_nodes["market"] = self.tool_nodes["market"]
            analyst_nodes["market"] = _wrap(
                analyst_nodes["market"], "Market Analyst", "market_report"
            )

        if "social" in selected_analysts:
            analyst_nodes["social"] = create_social_media_analyst(
                self.quick_thinking_llm
            )
            delete_nodes["social"] = create_msg_delete()
            tool_nodes["social"] = self.tool_nodes["social"]
            analyst_nodes["social"] = _wrap(
                analyst_nodes["social"], "Social Media Analyst", "sentiment_report"
            )

        if "news" in selected_analysts:
            analyst_nodes["news"] = create_news_analyst(
                self.quick_thinking_llm
            )
            delete_nodes["news"] = create_msg_delete()
            tool_nodes["news"] = self.tool_nodes["news"]
            analyst_nodes["news"] = _wrap(
                analyst_nodes["news"], "News Analyst", "news_report"
            )

        if "fundamentals" in selected_analysts:
            analyst_nodes["fundamentals"] = create_fundamentals_analyst(
                self.quick_thinking_llm
            )
            delete_nodes["fundamentals"] = create_msg_delete()
            tool_nodes["fundamentals"] = self.tool_nodes["fundamentals"]
            analyst_nodes["fundamentals"] = _wrap(
                analyst_nodes["fundamentals"],
                "Fundamentals Analyst",
                "fundamentals_report",
            )

        # New DeFi-specific analysts
        if "defi_market" in selected_analysts:
            analyst_nodes["defi_market"] = create_defi_market_analyst(
                self.quick_thinking_llm
            )
            delete_nodes["defi_market"] = create_msg_delete()
            tool_nodes["defi_market"] = self.tool_nodes.get("defi_market", self.tool_nodes.get("market"))
            analyst_nodes["defi_market"] = _wrap(
                analyst_nodes["defi_market"],
                "DeFi Market Analyst",
                "market_report",
            )

        if "protocol" in selected_analysts:
            analyst_nodes["protocol"] = create_protocol_analyst(
                self.quick_thinking_llm
            )
            delete_nodes["protocol"] = create_msg_delete()
            tool_nodes["protocol"] = self.tool_nodes.get("protocol", self.tool_nodes.get("fundamentals"))
            analyst_nodes["protocol"] = _wrap(
                analyst_nodes["protocol"], "Protocol Analyst", "fundamentals_report"
            )

        if "yield" in selected_analysts:
            analyst_nodes["yield"] = create_yield_analyst(
                self.quick_thinking_llm
            )
            delete_nodes["yield"] = create_msg_delete()
            tool_nodes["yield"] = self.tool_nodes.get("yield", self.tool_nodes.get("market"))
            analyst_nodes["yield"] = _wrap(
                analyst_nodes["yield"], "Yield Analyst", "yield_report"
            )

        if "risk" in selected_analysts:
            analyst_nodes["risk"] = create_defi_risk_analyst(
                self.quick_thinking_llm
            )
            delete_nodes["risk"] = create_msg_delete()
            tool_nodes["risk"] = self.tool_nodes.get("risk", self.tool_nodes.get("market"))
            analyst_nodes["risk"] = _wrap(
                analyst_nodes["risk"], "DeFi Risk Analyst", "risk_report"
            )

        # Create researcher and manager nodes
        bull_researcher_node = create_bull_researcher(
            self.quick_thinking_llm, self.bull_memory
        )
        bull_researcher_node = _wrap(
            bull_researcher_node, "Bull Researcher", "investment_debate_state"
        )
        bear_researcher_node = create_bear_researcher(
            self.quick_thinking_llm, self.bear_memory
        )
        bear_researcher_node = _wrap(
            bear_researcher_node, "Bear Researcher", "investment_debate_state"
        )
        research_manager_node = create_research_manager(
            self.deep_thinking_llm, self.invest_judge_memory
        )
        research_manager_node = _wrap(
            research_manager_node, "Research Manager", "investment_plan"
        )
        trader_node = create_trader(self.quick_thinking_llm, self.trader_memory)
        trader_node = _wrap(trader_node, "Trader", "trader_investment_plan")

        # Create risk analysis nodes
        risky_analyst = create_risky_debator(self.quick_thinking_llm)
        risky_analyst = _wrap(
            risky_analyst, "Risky Analyst", "risk_debate_state"
        )
        neutral_analyst = create_neutral_debator(self.quick_thinking_llm)
        neutral_analyst = _wrap(
            neutral_analyst, "Neutral Analyst", "risk_debate_state"
        )
        safe_analyst = create_safe_debator(self.quick_thinking_llm)
        safe_analyst = _wrap(
            safe_analyst, "Safe Analyst", "risk_debate_state"
        )
        risk_manager_node = create_risk_manager(
            self.deep_thinking_llm, self.risk_manager_memory
        )
        risk_manager_node = _wrap(
            risk_manager_node, "Risk Judge", "final_trade_decision"
        )

        # Create workflow
        workflow = StateGraph(AgentState)

        # Add analyst nodes to the graph
        for analyst_type, node in analyst_nodes.items():
            workflow.add_node(f"{analyst_type.capitalize()} Analyst", node)
            workflow.add_node(
                f"Msg Clear {analyst_type.capitalize()}", delete_nodes[analyst_type]
            )
            workflow.add_node(f"tools_{analyst_type}", tool_nodes[analyst_type])

        # Add other nodes
        workflow.add_node("Bull Researcher", bull_researcher_node)
        workflow.add_node("Bear Researcher", bear_researcher_node)
        workflow.add_node("Research Manager", research_manager_node)
        workflow.add_node("Trader", trader_node)
        workflow.add_node("Risky Analyst", risky_analyst)
        workflow.add_node("Neutral Analyst", neutral_analyst)
        workflow.add_node("Safe Analyst", safe_analyst)
        workflow.add_node("Risk Judge", risk_manager_node)

        # Define edges
        # Start with the first analyst
        first_analyst = selected_analysts[0]
        workflow.add_edge(START, f"{first_analyst.capitalize()} Analyst")

        # Connect analysts in sequence
        for i, analyst_type in enumerate(selected_analysts):
            current_analyst = f"{analyst_type.capitalize()} Analyst"
            current_tools = f"tools_{analyst_type}"
            current_clear = f"Msg Clear {analyst_type.capitalize()}"

            # Add conditional edges for current analyst
            workflow.add_conditional_edges(
                current_analyst,
                getattr(self.conditional_logic, f"should_continue_{analyst_type}"),
                [current_tools, current_clear],
            )
            workflow.add_edge(current_tools, current_analyst)

            # Connect to next analyst or to Bull Researcher if this is the last analyst
            if i < len(selected_analysts) - 1:
                next_analyst = f"{selected_analysts[i+1].capitalize()} Analyst"
                workflow.add_edge(current_clear, next_analyst)
            else:
                workflow.add_edge(current_clear, "Bull Researcher")

        # Add remaining edges
        workflow.add_conditional_edges(
            "Bull Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bear Researcher": "Bear Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_conditional_edges(
            "Bear Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bull Researcher": "Bull Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_edge("Research Manager", "Trader")
        workflow.add_edge("Trader", "Risky Analyst")
        workflow.add_conditional_edges(
            "Risky Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Safe Analyst": "Safe Analyst",
                "Risk Judge": "Risk Judge",
            },
        )
        workflow.add_conditional_edges(
            "Safe Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Neutral Analyst": "Neutral Analyst",
                "Risk Judge": "Risk Judge",
            },
        )
        workflow.add_conditional_edges(
            "Neutral Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Risky Analyst": "Risky Analyst",
                "Risk Judge": "Risk Judge",
            },
        )

        workflow.add_edge("Risk Judge", END)

        # Compile and return
        return workflow.compile()
