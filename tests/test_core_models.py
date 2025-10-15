"""
Unit tests for Pydantic models.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.core.models import (
    AnalysisRequest,
    AnalysisStatus,
    ChartData,
    CorrelationResult,
    Evidence,
    ExperimentSuggestion,
    FacilitationGuide,
    Hypothesis,
    MetricsSyncRequest,
    RetrospectiveReport,
    SprintMetrics,
    TrendAnalysis,
)


def test_sprint_metrics_valid(sample_sprint_metrics):
    """Test creating valid SprintMetrics."""
    metrics = SprintMetrics(**sample_sprint_metrics)
    assert metrics.sprint_id == sample_sprint_metrics["sprint_id"]
    assert metrics.team_happiness == 7.5
    assert metrics.story_points_completed == 42


def test_sprint_metrics_happiness_validation():
    """Test happiness score validation (0-10 range)."""
    with pytest.raises(ValidationError):
        SprintMetrics(
            sprint_id="TEST",
            sprint_name="Test",
            start_date=datetime.now(),
            end_date=datetime.now(),
            team_happiness=11.0,  # Invalid: > 10
        )


def test_trend_analysis_creation():
    """Test creating TrendAnalysis."""
    trend = TrendAnalysis(
        metric_name="review_time",
        current_value=30.5,
        previous_value=24.0,
        change_percent=27.1,
        trend_direction="up",
        is_significant=True,
    )
    assert trend.metric_name == "review_time"
    assert trend.trend_direction == "up"
    assert trend.is_significant is True


def test_correlation_result_validation():
    """Test CorrelationResult coefficient validation."""
    # Valid correlation
    corr = CorrelationResult(
        metric_1="review_time",
        metric_2="defect_rate",
        correlation_coefficient=0.75,
        is_strong=True,
        interpretation="Strong positive correlation",
    )
    assert corr.correlation_coefficient == 0.75

    # Invalid correlation (> 1)
    with pytest.raises(ValidationError):
        CorrelationResult(
            metric_1="A",
            metric_2="B",
            correlation_coefficient=1.5,
            is_strong=True,
            interpretation="Invalid",
        )


def test_evidence_creation():
    """Test Evidence model."""
    evidence = Evidence(
        metric_name="review_time",
        trend="up 28%",
        value="24.3 → 31.1 hours",
        supporting_data={"sprint_1": 24.3, "sprint_2": 31.1},
    )
    assert evidence.metric_name == "review_time"
    assert evidence.supporting_data is not None


def test_hypothesis_with_evidence():
    """Test Hypothesis with evidence list."""
    evidence_list = [
        Evidence(metric_name="review_time", trend="up", value="30%"),
        Evidence(metric_name="defect_rate", trend="up", value="15%"),
    ]

    hypothesis = Hypothesis(
        title="Review bottleneck",
        description="Long review times correlate with defects",
        confidence="High",
        confidence_score=0.85,
        evidence=evidence_list,
        potential_impact="Quality issues",
        affected_metrics=["review_time", "defect_rate"],
    )

    assert len(hypothesis.evidence) == 2
    assert hypothesis.confidence == "High"
    assert hypothesis.confidence_score == 0.85


def test_experiment_suggestion():
    """Test ExperimentSuggestion model."""
    experiment = ExperimentSuggestion(
        title="Set WIP limit",
        description="Limit work in review to 2 items",
        rationale="Reduce review queue",
        duration_sprints=1,
        success_metrics=["review_time", "reopen_rate"],
        implementation_steps=["Communicate to team", "Update board"],
        expected_outcome="Review time decreased by 20%",
    )

    assert experiment.duration_sprints == 1
    assert len(experiment.success_metrics) == 2


def test_chart_data_types():
    """Test ChartData with different chart types."""
    for chart_type in ["line", "bar", "heatmap", "box", "scatter"]:
        chart = ChartData(
            chart_id=f"chart_{chart_type}",
            chart_type=chart_type,
            title=f"Test {chart_type} chart",
            data={"x": [1, 2, 3], "y": [4, 5, 6]},
        )
        assert chart.chart_type == chart_type


def test_facilitation_guide():
    """Test FacilitationGuide model."""
    guide = FacilitationGuide(
        retro_questions=[
            "What slowed us down?",
            "What patterns do we see?",
            "What experiment should we try?",
        ],
        agenda_15min=[
            "Review metrics (5 min)",
            "Discuss hypotheses (7 min)",
            "Choose experiment (3 min)",
        ],
        focus_areas=["Review process", "Story sizing"],
    )

    assert len(guide.retro_questions) == 3
    assert len(guide.agenda_15min) == 3


def test_retrospective_report_structure():
    """Test RetrospectiveReport structure."""
    report = RetrospectiveReport(
        report_id="RPT-2024-001",
        headline="Review time increased 28%",
        sprint_period="Sprint 24.01 - 24.05",
        generated_at=datetime.now(),
        trends=[],
        correlations=[],
        charts=[],
        hypotheses=[
            Hypothesis(
                title="Test",
                description="Test hypothesis",
                confidence="High",
                confidence_score=0.8,
                evidence=[],
                potential_impact="Test impact",
                affected_metrics=["test"],
            )
        ],
        suggested_experiments=[
            ExperimentSuggestion(
                title="Test experiment",
                description="Test",
                rationale="Test",
                success_metrics=["metric1"],
                implementation_steps=["step1"],
                expected_outcome="outcome",
            )
        ],
        facilitation_guide=FacilitationGuide(
            retro_questions=["Q1", "Q2", "Q3"], agenda_15min=["A1"], focus_areas=["F1"]
        ),
        sprints_analyzed=5,
        confidence_overall="High",
    )

    assert report.report_id == "RPT-2024-001"
    assert report.sprints_analyzed == 5
    assert len(report.hypotheses) <= 3  # Max 3 hypotheses


def test_metrics_sync_request():
    """Test MetricsSyncRequest validation."""
    request = MetricsSyncRequest(sprint_count=5, force_refresh=True)
    assert request.sprint_count == 5
    assert request.force_refresh is True

    # Test bounds
    with pytest.raises(ValidationError):
        MetricsSyncRequest(sprint_count=0)  # Too low

    with pytest.raises(ValidationError):
        MetricsSyncRequest(sprint_count=13)  # Too high


def test_analysis_request():
    """Test AnalysisRequest model."""
    request = AnalysisRequest(
        sprint_count=5,
        focus_metrics=["review_time", "defect_rate"],
        custom_context="Team recently changed process",
    )

    assert request.sprint_count == 5
    assert len(request.focus_metrics) == 2


def test_analysis_status():
    """Test AnalysisStatus model."""
    status = AnalysisStatus(
        task_id="task-123",
        status="running",
        progress_percent=45,
        message="Analyzing trends...",
    )

    assert status.task_id == "task-123"
    assert status.status == "running"
    assert status.progress_percent == 45
