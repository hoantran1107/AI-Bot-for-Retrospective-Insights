"""
Unit tests for Celery tasks.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.database import (
    AnalysisReportDB,
    Base,
    ExperimentDB,
    HypothesisDB,
    MetricsSnapshot,
)
from src.core.models import SprintMetrics
from src.tasks.analysis_tasks import (
    cleanup_old_reports_task,
    generate_report_task,
    sync_metrics_task,
)

# Create test database (in-memory)
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def setup_test_db():
    """Setup and teardown test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_db_session(setup_test_db):
    """Provide a mock database session."""
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_sprint_data():
    """Create sample sprint data for testing."""

    def _create_sprint(sprint_number: int) -> dict:
        start_date = datetime.utcnow() - timedelta(days=14 * sprint_number)
        end_date = start_date + timedelta(days=14)

        return {
            "sprint_id": f"SPRINT-{sprint_number}",
            "sprint_name": f"Sprint {sprint_number}",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "team_happiness": 7.0 + (sprint_number % 3),
            "story_points_completed": 30 + sprint_number * 2,
            "story_points_planned": 35 + sprint_number * 2,
            "review_time": 24.0,
            "coding_time": 80.0,
            "testing_time": 30.0,
            "bugs_prod": 2,
            "story_point_distribution": {"small": 5, "medium": 8, "large": 3},
        }

    return _create_sprint


@pytest.fixture(autouse=True)
def mock_llm():
    """Mock LLM integration to avoid real API calls."""
    with patch("src.analysis.llm_integration.LLMClient._call_llm") as mock:
        mock.return_value = "Mocked LLM response"
        yield mock


def test_generate_report_task_success(mock_db_session, sample_sprint_data):
    """Test successful report generation task."""
    # Create test data
    for i in range(1, 6):
        sprint_data = sample_sprint_data(i)
        sprint_metrics = SprintMetrics(**sprint_data)
        snapshot = MetricsSnapshot(
            sprint_id=sprint_metrics.sprint_id,
            sprint_name=sprint_metrics.sprint_name,
            start_date=sprint_metrics.start_date,
            end_date=sprint_metrics.end_date,
            metrics_data=sprint_metrics.model_dump(mode="json"),
        )
        mock_db_session.add(snapshot)
    mock_db_session.commit()

    # Mock the task's db property using SessionLocal
    with patch("src.tasks.analysis_tasks.SessionLocal", return_value=mock_db_session):
        # Call the task function using .run() to bypass Celery decorator
        result = generate_report_task.run(sprint_count=5)

        # Verify results
        assert result["status"] == "success"
        assert result["sprints_analyzed"] == 5
        assert "report_id" in result
        assert "headline" in result

        # Verify database entries
        reports = mock_db_session.query(AnalysisReportDB).all()
        assert len(reports) == 1
        assert len(reports[0].sprint_ids) == 5


def test_generate_report_task_with_specific_sprints(
    mock_db_session, sample_sprint_data
):
    """Test report generation with specific sprint IDs."""
    # Create test data
    for i in range(1, 6):
        sprint_data = sample_sprint_data(i)
        sprint_metrics = SprintMetrics(**sprint_data)
        snapshot = MetricsSnapshot(
            sprint_id=sprint_metrics.sprint_id,
            sprint_name=sprint_metrics.sprint_name,
            start_date=sprint_metrics.start_date,
            end_date=sprint_metrics.end_date,
            metrics_data=sprint_metrics.model_dump(mode="json"),
        )
        mock_db_session.add(snapshot)
    mock_db_session.commit()

    with patch("src.tasks.analysis_tasks.SessionLocal", return_value=mock_db_session):
        # Call with specific sprint IDs using .run()
        result = generate_report_task.run(
            sprint_ids=["SPRINT-1", "SPRINT-2", "SPRINT-3"]
        )

        assert result["status"] == "success"
        assert result["sprints_analyzed"] == 3


def test_generate_report_task_insufficient_data(mock_db_session, sample_sprint_data):
    """Test report generation fails with insufficient data."""
    # Create only 1 sprint (need at least 2)
    sprint_data = sample_sprint_data(1)
    sprint_metrics = SprintMetrics(**sprint_data)
    snapshot = MetricsSnapshot(
        sprint_id=sprint_metrics.sprint_id,
        sprint_name=sprint_metrics.sprint_name,
        start_date=sprint_metrics.start_date,
        end_date=sprint_metrics.end_date,
        metrics_data=sprint_metrics.model_dump(mode="json"),
    )
    mock_db_session.add(snapshot)
    mock_db_session.commit()

    with patch("src.tasks.analysis_tasks.SessionLocal", return_value=mock_db_session):
        # Should raise ValueError
        with pytest.raises(ValueError, match="Insufficient data"):
            generate_report_task.run(sprint_count=5)


def test_sync_metrics_task_success(mock_db_session, sample_sprint_data):
    """Test successful metrics sync task."""
    # Mock the metrics client
    mock_sprints = [sample_sprint_data(i) for i in range(1, 4)]

    with patch("src.tasks.analysis_tasks.MetricsClient") as mock_client_class:
        mock_client = Mock()
        mock_client.fetch_sprints.return_value = mock_sprints
        mock_client_class.return_value = mock_client

        with patch(
            "src.tasks.analysis_tasks.SessionLocal", return_value=mock_db_session
        ):
            # Call the task using .run()
            result = sync_metrics_task.run(sprint_count=3)

            # Verify results
            assert result["status"] == "success"
            assert result["sprints_fetched"] == 3
            assert result["created"] == 3
            assert result["updated"] == 0
            assert result["skipped"] == 0

            # Verify database entries
            snapshots = mock_db_session.query(MetricsSnapshot).all()
            assert len(snapshots) == 3


def test_sync_metrics_task_with_force_refresh(mock_db_session, sample_sprint_data):
    """Test metrics sync with force refresh."""
    # Create existing data
    sprint_data = sample_sprint_data(1)
    sprint_metrics = SprintMetrics(**sprint_data)
    snapshot = MetricsSnapshot(
        sprint_id=sprint_metrics.sprint_id,
        sprint_name=sprint_metrics.sprint_name,
        start_date=sprint_metrics.start_date,
        end_date=sprint_metrics.end_date,
        metrics_data=sprint_metrics.model_dump(mode="json"),
    )
    mock_db_session.add(snapshot)
    mock_db_session.commit()

    # Mock the metrics client
    mock_sprints = [sample_sprint_data(1)]  # Same sprint

    with patch("src.tasks.analysis_tasks.MetricsClient") as mock_client_class:
        mock_client = Mock()
        mock_client.fetch_sprints.return_value = mock_sprints
        mock_client_class.return_value = mock_client

        with patch(
            "src.tasks.analysis_tasks.SessionLocal", return_value=mock_db_session
        ):
            # Call with force_refresh=True using .run()
            result = sync_metrics_task.run(sprint_count=1, force_refresh=True)

            # Verify results
            assert result["status"] == "success"
            assert result["updated"] == 1
            assert result["created"] == 0


def test_sync_metrics_task_skip_existing(mock_db_session, sample_sprint_data):
    """Test metrics sync skips existing data without force refresh."""
    # Create existing data
    sprint_data = sample_sprint_data(1)
    sprint_metrics = SprintMetrics(**sprint_data)
    snapshot = MetricsSnapshot(
        sprint_id=sprint_metrics.sprint_id,
        sprint_name=sprint_metrics.sprint_name,
        start_date=sprint_metrics.start_date,
        end_date=sprint_metrics.end_date,
        metrics_data=sprint_metrics.model_dump(mode="json"),
    )
    mock_db_session.add(snapshot)
    mock_db_session.commit()

    # Mock the metrics client
    mock_sprints = [sample_sprint_data(1)]  # Same sprint

    with patch("src.tasks.analysis_tasks.MetricsClient") as mock_client_class:
        mock_client = Mock()
        mock_client.fetch_sprints.return_value = mock_sprints
        mock_client_class.return_value = mock_client

        with patch(
            "src.tasks.analysis_tasks.SessionLocal", return_value=mock_db_session
        ):
            # Call with force_refresh=False (default) using .run()
            result = sync_metrics_task.run(sprint_count=1, force_refresh=False)

            # Verify results
            assert result["status"] == "success"
            assert result["skipped"] == 1
            assert result["created"] == 0
            assert result["updated"] == 0


def test_cleanup_old_reports_task(mock_db_session):
    """Test cleanup of old reports."""
    # Create old and new reports
    old_date = datetime.utcnow() - timedelta(days=100)
    recent_date = datetime.utcnow() - timedelta(days=30)

    old_report = AnalysisReportDB(
        report_date=old_date,
        sprint_ids=["SPRINT-1"],
        headline="Old Report",
        summary="Old",
        report_data={},
    )
    recent_report = AnalysisReportDB(
        report_date=recent_date,
        sprint_ids=["SPRINT-2"],
        headline="Recent Report",
        summary="Recent",
        report_data={},
    )

    mock_db_session.add(old_report)
    mock_db_session.add(recent_report)
    mock_db_session.commit()

    with patch("src.tasks.analysis_tasks.SessionLocal", return_value=mock_db_session):
        # Clean up reports older than 90 days
        result = cleanup_old_reports_task(days_to_keep=90)

        # Verify results
        assert result["status"] == "success"
        assert result["deleted"] == 1

        # Verify only recent report remains
        remaining_reports = mock_db_session.query(AnalysisReportDB).all()
        assert len(remaining_reports) == 1
        assert remaining_reports[0].headline == "Recent Report"


def test_generate_report_task_with_custom_context(mock_db_session, sample_sprint_data):
    """Test report generation with custom context."""
    # Create test data
    for i in range(1, 6):
        sprint_data = sample_sprint_data(i)
        sprint_metrics = SprintMetrics(**sprint_data)
        snapshot = MetricsSnapshot(
            sprint_id=sprint_metrics.sprint_id,
            sprint_name=sprint_metrics.sprint_name,
            start_date=sprint_metrics.start_date,
            end_date=sprint_metrics.end_date,
            metrics_data=sprint_metrics.model_dump(mode="json"),
        )
        mock_db_session.add(snapshot)
    mock_db_session.commit()

    with patch("src.tasks.analysis_tasks.SessionLocal", return_value=mock_db_session):
        # Call with custom context using .run()
        result = generate_report_task.run(
            sprint_count=5,
            custom_context="Team recently changed processes",
            focus_metrics=["review_time", "team_happiness"],
        )

        assert result["status"] == "success"
        assert result["sprints_analyzed"] == 5


def test_sync_metrics_task_with_team_id(mock_db_session, sample_sprint_data):
    """Test metrics sync with specific team ID."""
    mock_sprints = [sample_sprint_data(i) for i in range(1, 4)]

    with patch("src.tasks.analysis_tasks.MetricsClient") as mock_client_class:
        mock_client = Mock()
        mock_client.fetch_sprints.return_value = mock_sprints
        mock_client_class.return_value = mock_client

        with patch(
            "src.tasks.analysis_tasks.SessionLocal", return_value=mock_db_session
        ):
            # Call with team_id using .run()
            result = sync_metrics_task.run(sprint_count=3, team_id="TEAM-123")

            # Verify client was called with team_id
            mock_client.fetch_sprints.assert_called_once_with(
                count=3, team_id="TEAM-123"
            )

            assert result["status"] == "success"
            assert result["created"] == 3


def test_generate_report_stores_hypotheses_and_experiments(
    mock_db_session, sample_sprint_data
):
    """Test that report generation stores hypotheses and experiments."""
    # Create test data with patterns to generate hypotheses
    for i in range(1, 6):
        sprint_data = sample_sprint_data(i)
        # Modify data to create clear patterns
        sprint_data["team_happiness"] = 10.0 - i  # Decreasing
        sprint_data["review_time"] = 10.0 + i * 10  # Increasing
        sprint_data["bugs_prod"] = i  # Increasing

        sprint_metrics = SprintMetrics(**sprint_data)
        snapshot = MetricsSnapshot(
            sprint_id=sprint_metrics.sprint_id,
            sprint_name=sprint_metrics.sprint_name,
            start_date=sprint_metrics.start_date,
            end_date=sprint_metrics.end_date,
            metrics_data=sprint_metrics.model_dump(mode="json"),
        )
        mock_db_session.add(snapshot)
    mock_db_session.commit()

    with patch("src.tasks.analysis_tasks.SessionLocal", return_value=mock_db_session):
        result = generate_report_task.run(sprint_count=5)

        # Verify report created
        assert result["status"] == "success"

        # Check that hypotheses and experiments counts match what's in DB
        report_db = mock_db_session.query(AnalysisReportDB).first()
        assert report_db is not None

        hypotheses_count = (
            mock_db_session.query(HypothesisDB)
            .filter(HypothesisDB.report_id == report_db.id)
            .count()
        )
        experiments_count = (
            mock_db_session.query(ExperimentDB)
            .filter(ExperimentDB.report_id == report_db.id)
            .count()
        )

        assert hypotheses_count == result["hypotheses_count"]
        assert experiments_count == result["experiments_count"]
