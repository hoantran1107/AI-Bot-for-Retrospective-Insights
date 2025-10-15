"""
Unit tests for database models and operations.
"""

from datetime import datetime

import pytest

from src.core.database import (
    AnalysisReportDB,
    AnalysisTaskDB,
    ExperimentDB,
    HypothesisDB,
    MetricsSnapshot,
)


def test_metrics_snapshot_creation(test_db_session, sample_sprint_metrics):
    """Test creating and saving MetricsSnapshot."""
    snapshot = MetricsSnapshot(
        sprint_id=sample_sprint_metrics["sprint_id"],
        sprint_name=sample_sprint_metrics["sprint_name"],
        start_date=datetime.fromisoformat(sample_sprint_metrics["start_date"]),
        end_date=datetime.fromisoformat(sample_sprint_metrics["end_date"]),
        metrics_data=sample_sprint_metrics,
    )

    test_db_session.add(snapshot)
    test_db_session.commit()

    # Query back
    retrieved = (
        test_db_session.query(MetricsSnapshot)
        .filter_by(sprint_id=sample_sprint_metrics["sprint_id"])
        .first()
    )

    assert retrieved is not None
    assert retrieved.sprint_id == sample_sprint_metrics["sprint_id"]
    assert retrieved.metrics_data["team_happiness"] == 7.5


def test_metrics_snapshot_unique_sprint_id(test_db_session, sample_sprint_metrics):
    """Test that sprint_id is unique."""
    snapshot1 = MetricsSnapshot(
        sprint_id="SPRINT-001",
        sprint_name="Sprint 1",
        start_date=datetime.now(),
        end_date=datetime.now(),
        metrics_data=sample_sprint_metrics,
    )

    snapshot2 = MetricsSnapshot(
        sprint_id="SPRINT-001",  # Same ID
        sprint_name="Sprint 1 Duplicate",
        start_date=datetime.now(),
        end_date=datetime.now(),
        metrics_data=sample_sprint_metrics,
    )

    test_db_session.add(snapshot1)
    test_db_session.commit()

    test_db_session.add(snapshot2)
    with pytest.raises(Exception):  # Should raise integrity error
        test_db_session.commit()


def test_analysis_report_creation(test_db_session):
    """Test creating and saving AnalysisReportDB."""
    from datetime import datetime

    report_data = {
        "headline": "Test headline",
        "trends": [],
        "hypotheses": [],
        "experiments": [],
    }

    report = AnalysisReportDB(
        report_date=datetime.utcnow(),
        sprint_ids=["SPRINT-1", "SPRINT-2", "SPRINT-3", "SPRINT-4", "SPRINT-5"],
        headline="Test headline",
        summary="Analysis of 5 sprints",
        report_data=report_data,
    )

    test_db_session.add(report)
    test_db_session.commit()

    retrieved = (
        test_db_session.query(AnalysisReportDB)
        .filter_by(headline="Test headline")
        .first()
    )

    assert retrieved is not None
    assert retrieved.headline == "Test headline"
    assert len(retrieved.sprint_ids) == 5
    assert retrieved.summary == "Analysis of 5 sprints"


def test_hypothesis_db_creation(test_db_session):
    """Test creating and saving HypothesisDB."""
    from datetime import datetime

    # First create a parent report
    report = AnalysisReportDB(
        report_date=datetime.utcnow(),
        sprint_ids=["SPRINT-1", "SPRINT-2"],
        headline="Test Report",
        summary="Test",
        report_data={},
    )
    test_db_session.add(report)
    test_db_session.commit()

    hypothesis = HypothesisDB(
        report_id=report.id,  # Use integer FK
        hypothesis_type="review",
        title="Review bottleneck",
        description="Long review times causing delays",
        confidence="High",
        confidence_score=0.85,
        potential_impact="Quality degradation",
        affected_metrics=["review_time", "defect_rate"],
        supporting_evidence=[  # Changed from evidence_data
            {"metric_name": "review_time", "trend": "up 28%", "value": "24→31 hours"}
        ],
    )

    test_db_session.add(hypothesis)
    test_db_session.commit()

    retrieved = (
        test_db_session.query(HypothesisDB).filter_by(report_id=report.id).first()
    )

    assert retrieved is not None
    assert retrieved.title == "Review bottleneck"
    assert retrieved.confidence_score == 0.85
    assert len(retrieved.supporting_evidence) == 1


def test_experiment_db_creation(test_db_session):
    """Test creating and saving ExperimentDB."""
    from datetime import datetime

    # First create a parent report
    report = AnalysisReportDB(
        report_date=datetime.utcnow(),
        sprint_ids=["SPRINT-1", "SPRINT-2"],
        headline="Test Report",
        summary="Test",
        report_data={},
    )
    test_db_session.add(report)
    test_db_session.commit()

    experiment = ExperimentDB(
        report_id=report.id,  # Use integer FK
        title="Set WIP limit",
        description="Limit review to 2 items",
        rationale="Reduce queue",
        duration_sprints=1,
        success_metrics=["review_time", "reopen_rate"],
        implementation_steps=["Step 1", "Step 2"],
        expected_outcome="20% reduction",
        status="suggested",
    )

    test_db_session.add(experiment)
    test_db_session.commit()

    retrieved = (
        test_db_session.query(ExperimentDB).filter_by(report_id=report.id).first()
    )

    assert retrieved is not None
    assert retrieved.title == "Set WIP limit"
    assert retrieved.status == "suggested"
    assert len(retrieved.success_metrics) == 2


def test_experiment_status_transition(test_db_session):
    """Test updating experiment status."""
    from datetime import datetime

    # First create a parent report
    report = AnalysisReportDB(
        report_date=datetime.utcnow(),
        sprint_ids=["SPRINT-1"],
        headline="Test Report",
        summary="Test",
        report_data={},
    )
    test_db_session.add(report)
    test_db_session.commit()

    experiment = ExperimentDB(
        report_id=report.id,  # Use integer FK
        title="Test experiment",
        description="Test",
        rationale="Test",
        success_metrics=["metric1"],
        implementation_steps=["step1"],
        expected_outcome="outcome",
        status="suggested",
    )

    test_db_session.add(experiment)
    test_db_session.commit()

    # Update status
    experiment.status = "in_progress"
    experiment.started_at = datetime.now()
    test_db_session.commit()

    retrieved = test_db_session.query(ExperimentDB).first()
    assert retrieved.status == "in_progress"
    assert retrieved.started_at is not None


def test_analysis_task_db_creation(test_db_session):
    """Test creating and saving AnalysisTaskDB."""
    task = AnalysisTaskDB(
        task_id="task-12345",
        status="pending",
        progress_percent=0,
        sprint_count=5,
        focus_metrics=["review_time"],
        custom_context="Test context",
    )

    test_db_session.add(task)
    test_db_session.commit()

    retrieved = (
        test_db_session.query(AnalysisTaskDB).filter_by(task_id="task-12345").first()
    )

    assert retrieved is not None
    assert retrieved.status == "pending"
    assert retrieved.sprint_count == 5


def test_analysis_task_progress_update(test_db_session):
    """Test updating analysis task progress."""
    task = AnalysisTaskDB(task_id="task-67890", status="pending", sprint_count=5)

    test_db_session.add(task)
    test_db_session.commit()

    # Update progress
    task.status = "running"
    task.progress_percent = 50
    task.message = "Analyzing trends..."
    task.started_at = datetime.now()
    test_db_session.commit()

    retrieved = test_db_session.query(AnalysisTaskDB).first()
    assert retrieved.status == "running"
    assert retrieved.progress_percent == 50
    assert retrieved.message == "Analyzing trends..."


def test_query_multiple_hypotheses_by_report(test_db_session):
    """Test querying multiple hypotheses for a report."""
    from datetime import datetime

    # First create a parent report
    report = AnalysisReportDB(
        report_date=datetime.utcnow(),
        sprint_ids=["SPRINT-1"],
        headline="Test Report",
        summary="Test",
        report_data={},
    )
    test_db_session.add(report)
    test_db_session.commit()

    for i in range(3):
        hypothesis = HypothesisDB(
            report_id=report.id,  # Use integer FK
            hypothesis_type="general",
            title=f"Hypothesis {i + 1}",
            description=f"Description {i + 1}",
            confidence="High",
            confidence_score=0.8,
            potential_impact="Impact",
            affected_metrics=["metric1"],
            supporting_evidence=[],  # Changed from evidence_data
        )
        test_db_session.add(hypothesis)

    test_db_session.commit()

    hypotheses = (
        test_db_session.query(HypothesisDB).filter_by(report_id=report.id).all()
    )

    assert len(hypotheses) == 3
    assert all(h.report_id == report.id for h in hypotheses)
