"""
Integration tests for async task API endpoints.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_db
from src.api.main import app
from src.core.database import Base, MetricsSnapshot
from src.core.models import SprintMetrics

# Create test database (shared in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///file:memdb_tasks?mode=memory&cache=shared&uri=true"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False, "uri": True}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def create_sample_sprint_data(sprint_number: int) -> dict:
    """Create sample sprint data."""
    start_date = datetime.utcnow() - timedelta(days=14 * (6 - sprint_number))
    end_date = start_date + timedelta(days=14)

    return {
        "sprint_id": f"SPRINT-{sprint_number}",
        "sprint_name": f"Sprint {sprint_number}",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "team_happiness": 7.0 + (sprint_number % 3),
        "story_points_completed": 30 + sprint_number * 2,
        "story_points_planned": 35 + sprint_number * 2,
        "review_time": 20.0 + sprint_number * 2,
        "coding_time": 80.0,
        "testing_time": 30.0,
        "bugs_prod": 2,
        "story_point_distribution": {"small": 5, "medium": 8, "large": 3},
    }


def create_test_metrics(count: int = 5):
    """Create test metrics snapshots in database."""
    db = next(override_get_db())
    for i in range(1, count + 1):
        sprint_data = create_sample_sprint_data(i)
        sprint_metrics = SprintMetrics(**sprint_data)
        snapshot = MetricsSnapshot(
            sprint_id=sprint_metrics.sprint_id,
            sprint_name=sprint_metrics.sprint_name,
            start_date=sprint_metrics.start_date,
            end_date=sprint_metrics.end_date,
            metrics_data=sprint_metrics.model_dump(mode="json"),
        )
        db.add(snapshot)
    db.commit()
    db.close()


@pytest.fixture(autouse=True)
def setup_test_data():
    """Setup test data before each test."""
    # Cleanup first to ensure clean state
    db = next(override_get_db())
    db.query(MetricsSnapshot).delete()
    db.commit()
    db.close()

    # Then create test data
    create_test_metrics(5)
    yield

    # Cleanup after test
    db = next(override_get_db())
    db.query(MetricsSnapshot).delete()
    db.commit()
    db.close()


def test_generate_report_async():
    """Test async report generation endpoint."""
    with patch("src.tasks.analysis_tasks.generate_report_task.delay") as mock_delay:
        # Mock the Celery task
        mock_task = Mock()
        mock_task.id = "test-task-123"
        mock_delay.return_value = mock_task

        response = client.post(
            "/tasks/reports/generate",
            json={"sprint_count": 5, "custom_context": "Test context"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-123"
        assert data["status"] == "PENDING"
        assert "Task ID" in data["message"]

        # Verify task was called with correct parameters
        mock_delay.assert_called_once_with(
            sprint_count=5,
            sprint_ids=None,
            custom_context="Test context",
            focus_metrics=None,
        )


def test_generate_report_async_with_sprint_ids():
    """Test async report generation with specific sprint IDs."""
    with patch("src.tasks.analysis_tasks.generate_report_task.delay") as mock_delay:
        mock_task = Mock()
        mock_task.id = "test-task-456"
        mock_delay.return_value = mock_task

        response = client.post(
            "/tasks/reports/generate",
            json={"sprint_ids": ["SPRINT-1", "SPRINT-2", "SPRINT-3"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-456"

        mock_delay.assert_called_once_with(
            sprint_count=None,
            sprint_ids=["SPRINT-1", "SPRINT-2", "SPRINT-3"],
            custom_context=None,
            focus_metrics=None,
        )


def test_sync_metrics_async():
    """Test async metrics sync endpoint."""
    with patch("src.tasks.analysis_tasks.sync_metrics_task.delay") as mock_delay:
        mock_task = Mock()
        mock_task.id = "sync-task-789"
        mock_delay.return_value = mock_task

        response = client.post(
            "/tasks/metrics/sync",
            json={"sprint_count": 3, "team_id": "TEAM-123", "force_refresh": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "sync-task-789"
        assert data["status"] == "PENDING"

        mock_delay.assert_called_once_with(
            sprint_count=3, team_id="TEAM-123", force_refresh=True
        )


def test_sync_metrics_async_default_params():
    """Test async metrics sync with default parameters."""
    with patch("src.tasks.analysis_tasks.sync_metrics_task.delay") as mock_delay:
        mock_task = Mock()
        mock_task.id = "sync-task-default"
        mock_delay.return_value = mock_task

        response = client.post("/tasks/metrics/sync", json={})

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "sync-task-default"

        mock_delay.assert_called_once_with(
            sprint_count=5, team_id=None, force_refresh=False
        )


def test_get_task_status_pending():
    """Test getting status of a pending task."""
    with patch("src.api.routers.tasks.AsyncResult") as mock_result:
        mock_task = Mock()
        mock_task.state = "PENDING"
        mock_result.return_value = mock_task

        response = client.get("/tasks/status/test-task-123")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-123"
        assert data["status"] == "PENDING"
        assert data["result"] is None
        assert data["error"] is None


def test_get_task_status_success():
    """Test getting status of a successful task."""
    with patch("src.api.routers.tasks.AsyncResult") as mock_result:
        mock_task = Mock()
        mock_task.state = "SUCCESS"
        mock_task.result = {
            "status": "success",
            "report_id": 1,
            "sprints_analyzed": 5,
        }
        mock_result.return_value = mock_task

        response = client.get("/tasks/status/test-task-success")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert data["result"]["status"] == "success"
        assert data["result"]["report_id"] == 1


def test_get_task_status_failure():
    """Test getting status of a failed task."""
    with patch("src.api.routers.tasks.AsyncResult") as mock_result:
        mock_task = Mock()
        mock_task.state = "FAILURE"
        mock_task.info = Exception("Task failed due to error")
        mock_result.return_value = mock_task

        response = client.get("/tasks/status/test-task-failed")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "FAILURE"
        assert "Task failed" in data["error"]


def test_revoke_task_pending():
    """Test revoking a pending task."""
    with patch("src.api.routers.tasks.AsyncResult") as mock_result:
        mock_task = Mock()
        mock_task.state = "PENDING"
        mock_task.revoke = Mock()
        mock_result.return_value = mock_task

        response = client.delete("/tasks/test-task-revoke")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-revoke"
        assert data["status"] == "REVOKED"

        mock_task.revoke.assert_called_once_with(terminate=True)


def test_revoke_task_running():
    """Test revoking a running task."""
    with patch("src.api.routers.tasks.AsyncResult") as mock_result:
        mock_task = Mock()
        mock_task.state = "STARTED"
        mock_task.revoke = Mock()
        mock_result.return_value = mock_task

        response = client.delete("/tasks/test-task-running")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REVOKED"

        mock_task.revoke.assert_called_once_with(terminate=True)


def test_revoke_task_already_completed():
    """Test revoking a task that is already completed."""
    with patch("src.api.routers.tasks.AsyncResult") as mock_result:
        mock_task = Mock()
        mock_task.state = "SUCCESS"
        mock_task.revoke = Mock()
        mock_result.return_value = mock_task

        response = client.delete("/tasks/test-task-completed")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert "cannot revoke" in data["message"]

        # Revoke should not be called
        mock_task.revoke.assert_not_called()


def test_generate_report_async_validation_error():
    """Test report generation with invalid parameters."""
    response = client.post(
        "/tasks/reports/generate",
        json={"sprint_count": 1},  # Too few sprints
    )

    # Should fail validation
    assert response.status_code == 422


def test_sync_metrics_async_validation_error():
    """Test metrics sync with invalid parameters."""
    response = client.post(
        "/tasks/metrics/sync",
        json={"sprint_count": 25},  # Too many sprints
    )

    # Should fail validation
    assert response.status_code == 422


def test_generate_report_async_with_focus_metrics():
    """Test async report generation with focus metrics."""
    with patch("src.tasks.analysis_tasks.generate_report_task.delay") as mock_delay:
        mock_task = Mock()
        mock_task.id = "test-task-focus"
        mock_delay.return_value = mock_task

        response = client.post(
            "/tasks/reports/generate",
            json={
                "sprint_count": 5,
                "focus_metrics": ["team_happiness", "velocity"],
            },
        )

        assert response.status_code == 200
        mock_delay.assert_called_once_with(
            sprint_count=5,
            sprint_ids=None,
            custom_context=None,
            focus_metrics=["team_happiness", "velocity"],
        )
