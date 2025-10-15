"""
Pydantic models for data validation and API schemas.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

# ============= Sprint Metrics Models =============


class SprintMetrics(BaseModel):
    """Raw metrics data for a single sprint."""

    sprint_id: str
    sprint_name: str
    start_date: datetime
    end_date: datetime

    # Happiness
    team_happiness: Optional[float] = Field(
        None, ge=0, le=10, description="Team happiness score 0-10"
    )

    # Story points
    story_points_completed: Optional[int] = Field(None, ge=0)
    story_points_planned: Optional[int] = Field(None, ge=0)
    story_point_distribution: Optional[Dict[str, int]] = Field(
        None,
        description="Distribution by size, e.g., {'small': 5, 'medium': 8, 'large': 3}",
    )

    # Items out of sprint
    items_completed: Optional[int] = Field(None, ge=0)
    items_carried_over: Optional[int] = Field(None, ge=0)
    items_out_of_sprint_percent: Optional[float] = Field(None, ge=0, le=100)

    # Defect rates
    defect_rate_production: Optional[float] = Field(
        None, ge=0, description="PROD bugs / completed tickets"
    )
    defect_rate_all: Optional[float] = Field(
        None, ge=0, description="All bugs / completed tickets"
    )

    # Bugs by environment
    bugs_prod: Optional[int] = Field(None, ge=0)
    bugs_acc: Optional[int] = Field(None, ge=0)
    bugs_test: Optional[int] = Field(None, ge=0)
    bugs_dev: Optional[int] = Field(None, ge=0)
    bugs_other: Optional[int] = Field(None, ge=0)

    # Open bugs
    open_bugs_count: Optional[int] = Field(None, ge=0)

    # Bug root causes
    bugs_missed_testing: Optional[int] = Field(None, ge=0)
    bugs_missed_impact: Optional[int] = Field(None, ge=0)
    bugs_requirement_gap: Optional[int] = Field(None, ge=0)
    bugs_configuration: Optional[int] = Field(None, ge=0)
    bugs_third_party: Optional[int] = Field(None, ge=0)
    bugs_database: Optional[int] = Field(None, ge=0)
    bugs_security: Optional[int] = Field(None, ge=0)

    # Time metrics (in hours)
    coding_time: Optional[float] = Field(
        None, ge=0, description="Time in In Progress + Reopened"
    )
    review_time: Optional[float] = Field(None, ge=0, description="Time in Code Review")
    testing_time: Optional[float] = Field(None, ge=0, description="Time in Test status")

    class Config:
        json_schema_extra = {
            "example": {
                "sprint_id": "SPRINT-2024-01",
                "sprint_name": "Sprint 24.01",
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2024-01-14T23:59:59",
                "team_happiness": 7.5,
                "story_points_completed": 42,
                "coding_time": 120.5,
                "review_time": 24.3,
                "testing_time": 18.7,
            }
        }


# ============= Analysis Models =============


class TrendAnalysis(BaseModel):
    """Trend analysis for a specific metric."""

    metric_name: str
    current_value: Optional[float]
    previous_value: Optional[float]
    change_percent: Optional[float]
    trend_direction: Literal["up", "down", "stable"]
    is_significant: bool = Field(description="Whether change exceeds threshold")
    significance_level: Optional[str] = Field(
        None, description="Statistical significance if applicable"
    )


class CorrelationResult(BaseModel):
    """Correlation between two metrics."""

    metric_1: str
    metric_2: str
    correlation_coefficient: float = Field(ge=-1, le=1)
    is_strong: bool = Field(description="Whether |r| > threshold")
    interpretation: str


class Evidence(BaseModel):
    """Supporting evidence for a hypothesis."""

    metric_name: str
    trend: str
    value: str
    supporting_data: Optional[Dict[str, Any]] = None


class Hypothesis(BaseModel):
    """A hypothesis about team performance."""

    title: str
    description: str
    confidence: Literal["High", "Medium", "Low"]
    confidence_score: float = Field(ge=0, le=1)
    evidence: List[Evidence]
    potential_impact: str
    affected_metrics: List[str]


class ExperimentSuggestion(BaseModel):
    """Suggested experiment for next sprint."""

    title: str
    description: str
    rationale: str
    duration_sprints: int = Field(default=1, ge=1)
    success_metrics: List[str]
    implementation_steps: List[str]
    expected_outcome: str
    related_hypothesis_index: Optional[int] = None


class ChartData(BaseModel):
    """Chart data for frontend rendering."""

    chart_id: str
    chart_type: Literal["line", "bar", "heatmap", "box", "scatter"]
    title: str
    data: Dict[str, Any] = Field(description="Plotly figure JSON")
    annotations: Optional[List[str]] = None


class FacilitationGuide(BaseModel):
    """Facilitation notes for retrospective meeting."""

    retro_questions: List[str] = Field(min_length=3, max_length=3)
    agenda_15min: List[str]
    focus_areas: List[str]


class RetrospectiveReport(BaseModel):
    """Complete retrospective insight report."""

    report_id: str = Field(
        default_factory=lambda: f"RPT-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    )
    headline: str
    summary: str = ""
    sprint_period: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    # Analysis results
    trends: List[TrendAnalysis]
    correlations: List[CorrelationResult] = []
    charts: List[ChartData] = []

    # Insights
    hypotheses: List[Hypothesis] = Field(
        default=[], max_length=3, description="Top 3 hypotheses"
    )
    suggested_experiments: List[ExperimentSuggestion] = Field(
        default=[], min_length=0, max_length=3
    )

    # Facilitation
    facilitation_guide: FacilitationGuide

    # Metadata
    sprints_analyzed: int
    confidence_overall: str


# ============= API Request/Response Models =============


class MetricsSnapshotCreate(BaseModel):
    """Request to create a metrics snapshot."""

    sprint_id: str
    sprint_name: str
    start_date: datetime
    end_date: datetime
    metrics_data: Dict[str, Any]


class MetricsSnapshotResponse(BaseModel):
    """Response containing metrics snapshot data."""

    id: int
    sprint_id: str
    sprint_name: str
    start_date: datetime
    end_date: datetime
    metrics_data: Dict[str, Any]
    fetched_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    """Response for list of reports (summary view)."""

    id: int
    report_date: datetime
    headline: str
    summary: str
    sprint_ids: List[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class GenerateReportRequest(BaseModel):
    """Request to generate a retrospective report."""

    sprint_count: Optional[int] = Field(
        None, ge=2, le=20, description="Number of recent sprints to analyze"
    )
    sprint_ids: Optional[List[str]] = Field(
        None, description="Specific sprint IDs to analyze"
    )
    custom_context: Optional[str] = Field(
        None, description="Additional context for the analysis"
    )
    focus_metrics: Optional[List[str]] = Field(
        None, description="Specific metrics to focus on"
    )


class MetricsSyncRequest(BaseModel):
    """Request to sync metrics from external API."""

    sprint_count: Optional[int] = Field(
        5, ge=1, le=12, description="Number of sprints to fetch"
    )
    force_refresh: bool = Field(False, description="Force refresh even if cached")


class AnalysisRequest(BaseModel):
    """Request to generate retrospective report."""

    sprint_count: int = Field(5, ge=3, le=12)
    focus_metrics: Optional[List[str]] = Field(
        None, description="Specific metrics to focus on"
    )
    custom_context: Optional[str] = Field(
        None, description="Additional context for LLM"
    )


class AnalysisStatus(BaseModel):
    """Status of analysis task."""

    task_id: str
    status: Literal["pending", "running", "completed", "failed"]
    progress_percent: Optional[int] = Field(None, ge=0, le=100)
    message: Optional[str] = None
    report_id: Optional[str] = None


# ============= Async Task Models =============


class TaskStatus(BaseModel):
    """Status of a Celery task."""

    task_id: str
    status: Literal["PENDING", "STARTED", "SUCCESS", "FAILURE", "RETRY", "REVOKED"]
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None


class AsyncReportRequest(BaseModel):
    """Request to generate a report asynchronously."""

    sprint_count: Optional[int] = Field(
        None, ge=2, le=20, description="Number of recent sprints to analyze"
    )
    sprint_ids: Optional[List[str]] = Field(
        None, description="Specific sprint IDs to analyze"
    )
    custom_context: Optional[str] = Field(
        None, description="Additional context for the analysis"
    )
    focus_metrics: Optional[List[str]] = Field(
        None, description="Specific metrics to focus on"
    )


class AsyncReportResponse(BaseModel):
    """Response for async report generation request."""

    task_id: str
    status: str
    message: str


class AsyncMetricsSyncRequest(BaseModel):
    """Request to sync metrics asynchronously."""

    sprint_count: int = Field(5, ge=1, le=20, description="Number of sprints to fetch")
    team_id: Optional[str] = Field(None, description="Optional team identifier")
    force_refresh: bool = Field(False, description="Force refresh even if data exists")


class AsyncMetricsSyncResponse(BaseModel):
    """Response for async metrics sync request."""

    task_id: str
    status: str
    message: str
