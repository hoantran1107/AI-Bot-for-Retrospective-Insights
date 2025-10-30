"""Tests for LangGraph AI agent."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.analysis.langgraph_agent import (
    DashboardAnalysisAgent,
    AgentState,
    get_dashboard_agent,
)


@pytest.fixture
def mock_dashboard_client():
    """Create a mock dashboard client."""
    client = MagicMock()
    client.fetch_multiple_charts = AsyncMock(
        return_value={
            "happiness": {"values": [7.5, 7.0, 6.5], "trend": "decreasing"},
            "defect-rate-all": {"values": [0.1, 0.15, 0.2], "trend": "increasing"},
        }
    )
    return client


@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    return llm


@pytest.fixture
def agent(mock_dashboard_client, mock_llm):
    """Create an agent instance for testing."""
    with patch("src.analysis.langgraph_agent.get_dashboard_client") as mock_get_client:
        mock_get_client.return_value = mock_dashboard_client
        agent = DashboardAnalysisAgent(dashboard_client=mock_dashboard_client)
        agent.llm = mock_llm
        return agent


class TestDashboardAnalysisAgent:
    """Test suite for DashboardAnalysisAgent."""

    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent.dashboard_client is not None
        assert agent.llm is not None
        assert agent.graph is not None

    @pytest.mark.asyncio
    async def test_analyze_query(self, agent, mock_llm):
        """Test query analysis step."""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.content = '["happiness", "defect-rate-all"]'
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        state: AgentState = {
            "messages": [],
            "chart_data": {},
            "analysis_results": {},
            "user_query": "How is team happiness trending?",
            "response": "",
        }

        result_state = await agent._analyze_query(state)

        assert "relevant_charts" in result_state["analysis_results"]
        assert isinstance(result_state["analysis_results"]["relevant_charts"], list)

    @pytest.mark.asyncio
    async def test_fetch_data(self, agent, mock_dashboard_client):
        """Test data fetching step."""
        state: AgentState = {
            "messages": [],
            "chart_data": {},
            "analysis_results": {"relevant_charts": ["happiness", "defect-rate-all"]},
            "user_query": "How is team happiness?",
            "response": "",
        }

        result_state = await agent._fetch_data(state)

        assert "happiness" in result_state["chart_data"]
        assert "defect-rate-all" in result_state["chart_data"]
        mock_dashboard_client.fetch_multiple_charts.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_data(self, agent):
        """Test data analysis step."""
        state: AgentState = {
            "messages": [],
            "chart_data": {
                "happiness": {"values": [7.5, 7.0, 6.5, 6.0, 5.5]},
                "defect-rate-all": {"values": [0.1, 0.12, 0.15, 0.18, 0.2]},
            },
            "analysis_results": {},
            "user_query": "Analyze team metrics",
            "response": "",
        }

        result_state = await agent._analyze_data(state)

        assert "data_summary" in result_state["analysis_results"]
        assert "trends" in result_state["analysis_results"]

    @pytest.mark.asyncio
    async def test_generate_insights(self, agent, mock_llm):
        """Test insights generation step."""
        mock_response = MagicMock()
        mock_response.content = (
            "Team happiness is declining while defect rates are increasing. "
            "This suggests potential issues with team morale and code quality."
        )
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        state: AgentState = {
            "messages": [],
            "chart_data": {
                "happiness": {"values": [7.5, 7.0, 6.5]},
            },
            "analysis_results": {
                "trends": [
                    {"chart": "happiness", "direction": "decreasing", "change": "13.3%"}
                ]
            },
            "user_query": "What's happening with team happiness?",
            "response": "",
        }

        result_state = await agent._generate_insights(state)

        assert result_state["response"] != ""
        assert "Team happiness" in result_state["response"]

    @pytest.mark.asyncio
    async def test_analyze_full_flow(self, agent, mock_llm, mock_dashboard_client):
        """Test full analysis flow."""
        # Mock LLM responses
        mock_llm_response_query = MagicMock()
        mock_llm_response_query.content = '["happiness"]'

        mock_llm_response_insights = MagicMock()
        mock_llm_response_insights.content = "Team happiness is stable."

        mock_llm.ainvoke = AsyncMock(
            side_effect=[mock_llm_response_query, mock_llm_response_insights]
        )

        result = await agent.analyze("How is team happiness?")

        assert result["success"] is True
        assert "insights" in result
        assert "chart_data" in result
        assert "analysis" in result

    @pytest.mark.asyncio
    async def test_analyze_with_error(self, agent):
        """Test analysis with error handling."""
        # Force an error by setting graph to None
        agent.graph = None

        result = await agent.analyze("Test query")

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_chat_interface(self, agent, mock_llm, mock_dashboard_client):
        """Test simple chat interface."""
        # Mock LLM responses
        mock_llm_response_query = MagicMock()
        mock_llm_response_query.content = '["happiness"]'

        mock_llm_response_insights = MagicMock()
        mock_llm_response_insights.content = "Team is doing well!"

        mock_llm.ainvoke = AsyncMock(
            side_effect=[mock_llm_response_query, mock_llm_response_insights]
        )

        response = await agent.chat("How is the team?")

        assert isinstance(response, str)
        assert len(response) > 0

    def test_format_trends(self, agent):
        """Test trend formatting helper."""
        trends = [
            {"chart": "happiness", "direction": "increasing", "change": "10%"},
            {"chart": "defect-rate-all", "direction": "decreasing", "change": "5%"},
        ]

        formatted = agent._format_trends(trends)

        assert "happiness" in formatted
        assert "increasing" in formatted
        assert "10%" in formatted

    def test_format_trends_empty(self, agent):
        """Test trend formatting with no trends."""
        formatted = agent._format_trends([])

        assert "No significant trends" in formatted

    def test_format_chart_data(self, agent):
        """Test chart data formatting helper."""
        chart_data = {
            "happiness": {"values": [7.5, 7.0], "labels": ["S1", "S2"]},
            "defect-rate-all": {"error": "Failed to fetch"},
        }

        formatted = agent._format_chart_data(chart_data)

        assert "happiness" in formatted
        assert "defect-rate-all" in formatted
        assert "Error" in formatted


def test_get_dashboard_agent_singleton():
    """Test that get_dashboard_agent returns the same instance."""
    agent1 = get_dashboard_agent()
    agent2 = get_dashboard_agent()

    assert agent1 is agent2
