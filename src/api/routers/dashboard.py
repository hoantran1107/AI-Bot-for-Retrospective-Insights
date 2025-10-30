"""Dashboard API endpoints for chart data and AI insights."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field

from src.analysis.langgraph_agent import get_dashboard_agent
from src.utils.dashboard_client import get_dashboard_client, ChartType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class ChartDataResponse(BaseModel):
    """Response model for chart data."""

    chart_name: str
    data: dict[str, Any]
    success: bool


class MultipleChartsResponse(BaseModel):
    """Response model for multiple charts data."""

    charts: dict[str, dict[str, Any]]
    success: bool
    total_charts: int


class InsightRequest(BaseModel):
    """Request model for AI insights generation."""

    query: str = Field(..., description="User's question or analysis request")
    include_chart_data: bool = Field(
        default=True, description="Whether to include raw chart data in response"
    )


class InsightResponse(BaseModel):
    """Response model for AI-generated insights."""

    query: str
    insights: str
    analysis: dict[str, Any]
    chart_data: dict[str, Any] | None = None
    success: bool


@router.get("/health")
async def dashboard_health():
    """Health check endpoint for dashboard service."""
    return {"status": "healthy", "service": "dashboard"}


@router.get("/charts/{chart_name}", response_model=ChartDataResponse)
async def get_chart_data(
    chart_name: ChartType,
):
    """
    Fetch data for a specific chart from the dashboard.

    Args:
        chart_name: Name of the chart (e.g., "testing-time", "happiness")

    Returns:
        Chart data response

    Raises:
        HTTPException: If chart data cannot be fetched
    """
    try:
        client = get_dashboard_client()
        data = await client.fetch_chart_data(chart_name)

        return ChartDataResponse(
            chart_name=chart_name,
            data=data,
            success=True,
        )

    except Exception as e:
        logger.exception("Failed to fetch chart data")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch chart data: {str(e)}",
        ) from e


@router.get("/charts", response_model=MultipleChartsResponse)
async def get_multiple_charts(
    chart_names: list[ChartType] = Query(
        None, description="List of chart names to fetch (empty for all)"
    ),
):
    """
    Fetch data for multiple charts from the dashboard.

    Args:
        chart_names: List of chart names to fetch. If empty, fetches all charts.

    Returns:
        Multiple charts data response

    Raises:
        HTTPException: If chart data cannot be fetched
    """
    try:
        client = get_dashboard_client()

        if chart_names:
            charts = await client.fetch_multiple_charts(chart_names)
        else:
            charts = await client.fetch_all_charts()

        return MultipleChartsResponse(
            charts=charts,
            success=True,
            total_charts=len(charts),
        )

    except Exception as e:
        logger.exception("Failed to fetch multiple charts")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch charts: {str(e)}",
        ) from e


@router.post("/insights", response_model=InsightResponse)
async def generate_insights(request: InsightRequest):
    """
    Generate AI-powered insights based on user query and dashboard data.

    This endpoint uses LangGraph-based AI agent to:
    1. Analyze the user's query
    2. Fetch relevant chart data
    3. Perform data analysis
    4. Generate intelligent insights and recommendations

    Args:
        request: Insight generation request with user query

    Returns:
        AI-generated insights response

    Raises:
        HTTPException: If insight generation fails
    """
    try:
        agent = get_dashboard_agent()
        result = await agent.analyze(request.query)

        # Optionally exclude chart data to reduce response size
        chart_data = result.get("chart_data") if request.include_chart_data else None

        return InsightResponse(
            query=result["query"],
            insights=result["insights"],
            analysis=result.get("analysis", {}),
            chart_data=chart_data,
            success=result["success"],
        )

    except Exception as e:
        logger.exception("Failed to generate insights")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate insights: {str(e)}",
        ) from e


@router.post("/chat")
async def chat_with_agent(message: str = Query(..., description="User's message")):
    """
    Simple chat interface with the AI agent.

    Args:
        message: User's chat message

    Returns:
        Agent's response

    Raises:
        HTTPException: If chat fails
    """
    try:
        agent = get_dashboard_agent()
        response = await agent.chat(message)

        return {
            "message": message,
            "response": response,
            "success": True,
        }

    except Exception as e:
        logger.exception("Chat failed")
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}",
        ) from e


@router.get("/available-charts")
async def get_available_charts():
    """
    Get list of all available chart types.

    Returns:
        List of available chart types with descriptions
    """
    charts = [
        {
            "name": "testing-time",
            "description": "Time spent on testing activities",
            "category": "time-metrics",
        },
        {
            "name": "review-time",
            "description": "Time spent on code review",
            "category": "time-metrics",
        },
        {
            "name": "coding-time",
            "description": "Time spent on coding",
            "category": "time-metrics",
        },
        {
            "name": "root-cause",
            "description": "Root causes of bugs and issues",
            "category": "quality",
        },
        {
            "name": "open-bugs-over-time",
            "description": "Trend of open bugs over time",
            "category": "quality",
        },
        {
            "name": "bugs-per-environment",
            "description": "Bug distribution by environment (PROD, ACC, TEST, DEV)",
            "category": "quality",
        },
        {
            "name": "sp-distribution",
            "description": "Story point distribution",
            "category": "planning",
        },
        {
            "name": "items-out-of-sprint",
            "description": "Items carried over from sprint",
            "category": "planning",
        },
        {
            "name": "defect-rate-prod",
            "description": "Defect rate in production",
            "category": "quality",
        },
        {
            "name": "defect-rate-all",
            "description": "Overall defect rate across all environments",
            "category": "quality",
        },
        {
            "name": "happiness",
            "description": "Team happiness and satisfaction scores",
            "category": "team-health",
        },
    ]

    return {
        "charts": charts,
        "total": len(charts),
    }
