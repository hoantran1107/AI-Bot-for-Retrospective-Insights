"""
LangGraph-based AI agent for intelligent dashboard data analysis and insights.
"""

import logging
from typing import Any, TypedDict, Annotated
import operator

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from src.core.config import get_settings
from src.utils.dashboard_client import DashboardClient, get_dashboard_client

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the LangGraph agent."""

    messages: Annotated[list[BaseMessage], operator.add]
    chart_data: dict[str, Any]
    analysis_results: dict[str, Any]
    user_query: str
    response: str


class DashboardAnalysisAgent:
    """
    LangGraph-based AI agent for analyzing dashboard data and providing insights.

    This agent uses a state graph to:
    1. Fetch relevant chart data based on user query
    2. Analyze the data for patterns and trends
    3. Generate intelligent insights using LLM
    4. Provide actionable recommendations
    """

    def __init__(
        self,
        dashboard_client: DashboardClient | None = None,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.7,
    ):
        """
        Initialize the dashboard analysis agent.

        Args:
            dashboard_client: Client for fetching dashboard data
            model_name: Name of the LLM model to use
            temperature: Temperature for LLM generation
        """
        settings = get_settings()
        self.dashboard_client = dashboard_client or get_dashboard_client()

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=settings.chat_completion_api_key,
        )

        # Build the state graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph for the agent."""

        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("analyze_query", self._analyze_query)
        workflow.add_node("fetch_data", self._fetch_data)
        workflow.add_node("analyze_data", self._analyze_data)
        workflow.add_node("generate_insights", self._generate_insights)

        # Define the flow
        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query", "fetch_data")
        workflow.add_edge("fetch_data", "analyze_data")
        workflow.add_edge("analyze_data", "generate_insights")
        workflow.add_edge("generate_insights", END)

        return workflow.compile()

    async def _analyze_query(self, state: AgentState) -> AgentState:
        """
        Analyze user query to determine which chart data to fetch.

        Args:
            state: Current agent state

        Returns:
            Updated state with query analysis
        """
        user_query = state["user_query"]

        # Use LLM to identify relevant charts
        system_prompt = """You are a data analysis assistant. Given a user query about team metrics, 
        identify which of the following chart types would be most relevant:
        
        - testing-time: Time spent on testing
        - review-time: Time spent on code review
        - coding-time: Time spent on coding
        - root-cause: Root causes of bugs
        - open-bugs-over-time: Trend of open bugs
        - bugs-per-environment: Bugs by environment (PROD, ACC, TEST, DEV)
        - sp-distribution: Story point distribution
        - items-out-of-sprint: Items carried over
        - defect-rate-prod: Defect rate in production
        - defect-rate-all: Overall defect rate
        - happiness: Team happiness scores
        
        Respond with a JSON array of chart names, e.g., ["testing-time", "happiness"]
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query),
        ]

        response = await self.llm.ainvoke(messages)

        # Parse the response to get chart names
        try:
            import json

            chart_names = json.loads(response.content)
            state["analysis_results"] = {"relevant_charts": chart_names}
        except Exception as e:
            logger.error(f"Failed to parse chart names: {e}")
            # Default to common charts
            state["analysis_results"] = {
                "relevant_charts": ["happiness", "defect-rate-all", "review-time"]
            }

        state["messages"].append(HumanMessage(content=user_query))
        state["messages"].append(response)

        return state

    async def _fetch_data(self, state: AgentState) -> AgentState:
        """
        Fetch relevant chart data from dashboard API.

        Args:
            state: Current agent state

        Returns:
            Updated state with fetched data
        """
        relevant_charts = state["analysis_results"].get("relevant_charts", [])

        try:
            # Fetch data for relevant charts
            chart_data = await self.dashboard_client.fetch_multiple_charts(
                relevant_charts
            )
            state["chart_data"] = chart_data

            logger.info(f"Fetched data for {len(chart_data)} charts")
        except Exception as e:
            logger.error(f"Failed to fetch chart data: {e}")
            state["chart_data"] = {}

        return state

    async def _analyze_data(self, state: AgentState) -> AgentState:
        """
        Analyze the fetched chart data for patterns and trends.

        Args:
            state: Current agent state

        Returns:
            Updated state with analysis results
        """
        chart_data = state["chart_data"]

        # Perform basic statistical analysis
        analysis = {
            "data_summary": {},
            "trends": [],
            "anomalies": [],
        }

        for chart_name, data in chart_data.items():
            if "error" in data:
                continue

            # Add data summary
            analysis["data_summary"][chart_name] = {
                "available": True,
                "data_points": len(data) if isinstance(data, list) else 1,
            }

            # Detect trends (simplified for now)
            if isinstance(data, dict) and "values" in data:
                values = data["values"]
                if len(values) >= 2:
                    if values[-1] > values[0] * 1.2:
                        analysis["trends"].append(
                            {
                                "chart": chart_name,
                                "direction": "increasing",
                                "change": f"{((values[-1] / values[0]) - 1) * 100:.1f}%",
                            }
                        )
                    elif values[-1] < values[0] * 0.8:
                        analysis["trends"].append(
                            {
                                "chart": chart_name,
                                "direction": "decreasing",
                                "change": f"{(1 - (values[-1] / values[0])) * 100:.1f}%",
                            }
                        )

        state["analysis_results"].update(analysis)

        return state

    async def _generate_insights(self, state: AgentState) -> AgentState:
        """
        Generate intelligent insights and recommendations using LLM.

        Args:
            state: Current agent state

        Returns:
            Updated state with generated insights
        """
        user_query = state["user_query"]
        chart_data = state["chart_data"]
        analysis = state["analysis_results"]

        # Create a comprehensive prompt for the LLM
        system_prompt = """You are an expert Agile Coach and data analyst. 
        You help teams understand their metrics and improve their processes.
        
        Analyze the provided dashboard data and generate:
        1. Key insights about team performance
        2. Identified patterns and trends
        3. Potential issues or bottlenecks
        4. Actionable recommendations for improvement
        
        Be specific, data-driven, and practical in your recommendations."""

        # Format the data for the LLM
        data_summary = f"""
User Query: {user_query}

Chart Data Available:
{", ".join(chart_data.keys())}

Analysis Summary:
Trends Detected: {len(analysis.get("trends", []))}
{self._format_trends(analysis.get("trends", []))}

Raw Data:
{self._format_chart_data(chart_data)}
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=data_summary),
        ]

        response = await self.llm.ainvoke(messages)

        state["response"] = response.content
        state["messages"].append(response)

        return state

    def _format_trends(self, trends: list[dict]) -> str:
        """Format trends for LLM consumption."""
        if not trends:
            return "No significant trends detected."

        formatted = []
        for trend in trends:
            formatted.append(
                f"- {trend['chart']}: {trend['direction']} by {trend['change']}"
            )

        return "\n".join(formatted)

    def _format_chart_data(self, chart_data: dict[str, Any]) -> str:
        """Format chart data for LLM consumption."""
        formatted = []

        for chart_name, data in chart_data.items():
            if "error" in data:
                formatted.append(f"{chart_name}: Error - {data['error']}")
            else:
                import json

                formatted.append(
                    f"{chart_name}:\n{json.dumps(data, indent=2)[:500]}..."
                )

        return "\n\n".join(formatted)

    async def analyze(self, user_query: str) -> dict[str, Any]:
        """
        Analyze a user query and generate insights.

        Args:
            user_query: User's question or request

        Returns:
            Dictionary with analysis results and insights
        """
        # Initialize state
        initial_state: AgentState = {
            "messages": [],
            "chart_data": {},
            "analysis_results": {},
            "user_query": user_query,
            "response": "",
        }

        try:
            # Run the graph
            final_state = await self.graph.ainvoke(initial_state)

            return {
                "success": True,
                "query": user_query,
                "insights": final_state["response"],
                "chart_data": final_state["chart_data"],
                "analysis": final_state["analysis_results"],
            }
        except Exception as e:
            logger.error(f"Error in agent analysis: {e}")
            return {
                "success": False,
                "query": user_query,
                "error": str(e),
                "insights": "Failed to generate insights due to an error.",
            }

    async def chat(
        self, message: str, conversation_history: list[dict] | None = None
    ) -> str:
        """
        Simple chat interface for conversational analysis.

        Args:
            message: User's message
            conversation_history: Previous conversation messages

        Returns:
            Agent's response
        """
        result = await self.analyze(message)
        return result.get("insights", "I couldn't generate insights for your query.")


# Global agent instance
_agent_instance: DashboardAnalysisAgent | None = None


def get_dashboard_agent() -> DashboardAnalysisAgent:
    """Get global dashboard analysis agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = DashboardAnalysisAgent()
    return _agent_instance
