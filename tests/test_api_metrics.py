"""Tests for metrics API endpoints."""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from src.api.dependencies import get_metrics_client
from src.api.main import app
from src.core.database import MetricsSnapshot
from src.core.models import SprintMetrics

client = TestClient(app)


def create_sample_sprint_data(sprint_number: int) -> dict:
    """Create sample sprint data for testing."""
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
        "avg_review_time_hours": 24.0 - sprint_number,
        "bugs_found": 5 - sprint_number % 3,
        "bugs_production": 1,
    }


def test_fetch_and_store_metrics(test_db):
    """Test fetching and storing metrics from external API."""
    # Mock metrics client
    from unittest.mock import Mock

    mock_client = Mock()
    mock_sprints = [create_sample_sprint_data(i) for i in range(1, 4)]

    # Create proper async mock
    async def mock_fetch(*args, **kwargs):
        return mock_sprints

    mock_client.fetch_sprints = mock_fetch

    def override_metrics_client():
        return mock_client

    app.dependency_overrides[get_metrics_client] = override_metrics_client

    try:
        response = client.post("/metrics/fetch?count=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["sprint_id"] == "SPRINT-1"
        assert "metrics_data" in data[0]

        # Verify data was stored in database
        snapshots = test_db.query(MetricsSnapshot).all()
        assert len(snapshots) == 3
    finally:
        app.dependency_overrides.pop(get_metrics_client, None)


def test_fetch_metrics_with_team_id():
    """Test fetching metrics with team ID parameter."""
    from unittest.mock import Mock

    mock_client = Mock()
    mock_sprints = [create_sample_sprint_data(1)]

    async def mock_fetch(*args, **kwargs):
        return mock_sprints

    mock_client.fetch_sprints = mock_fetch

    def override_metrics_client():
        return mock_client

    app.dependency_overrides[get_metrics_client] = override_metrics_client

    try:
        response = client.post("/metrics/fetch?count=1&team_id=TEAM-A")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
    finally:
        app.dependency_overrides.pop(get_metrics_client, None)


def test_fetch_metrics_updates_existing(test_db):
    """Test that fetching metrics updates existing snapshots."""
    from unittest.mock import Mock

    # First, create an existing snapshot
    sprint_data = create_sample_sprint_data(1)
    sprint_metrics = SprintMetrics(**sprint_data)

    existing = MetricsSnapshot(
        sprint_id=sprint_metrics.sprint_id,
        sprint_name=sprint_metrics.sprint_name,
        start_date=sprint_metrics.start_date,
        end_date=sprint_metrics.end_date,
        metrics_data=sprint_metrics.model_dump(mode="json"),
    )
    test_db.add(existing)
    test_db.commit()
    original_updated_at = existing.updated_at

    # Now fetch with updated data
    mock_client = Mock()
    updated_data = sprint_data.copy()
    updated_data["team_happiness"] = 9.0  # Changed value

    async def mock_fetch(*args, **kwargs):
        return [updated_data]

    mock_client.fetch_sprints = mock_fetch

    def override_metrics_client():
        return mock_client

    app.dependency_overrides[get_metrics_client] = override_metrics_client

    try:
        response = client.post("/metrics/fetch?count=1")
        assert response.status_code == 200

        # Verify snapshot was updated
        test_db.expire_all()  # Refresh the session
        snapshot = (
            test_db.query(MetricsSnapshot)
            .filter(MetricsSnapshot.sprint_id == "SPRINT-1")
            .first()
        )
        assert snapshot.metrics_data["team_happiness"] == 9.0
        assert snapshot.updated_at > original_updated_at
    finally:
        app.dependency_overrides.pop(get_metrics_client, None)


def test_list_metrics(test_db):
    """Test listing metrics snapshots."""
    # Create some test snapshots
    for i in range(1, 6):
        sprint_data = create_sample_sprint_data(i)
        sprint_metrics = SprintMetrics(**sprint_data)
        snapshot = MetricsSnapshot(
            sprint_id=sprint_metrics.sprint_id,
            sprint_name=sprint_metrics.sprint_name,
            start_date=sprint_metrics.start_date,
            end_date=sprint_metrics.end_date,
            metrics_data=sprint_metrics.model_dump(mode="json"),
        )
        test_db.add(snapshot)
    test_db.commit()

    # Test listing
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5

    # Test with limit
    response = client.get("/metrics?limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    # Test with offset
    response = client.get("/metrics?limit=2&offset=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_metrics_by_sprint_id(test_db):
    """Test retrieving specific metrics by sprint ID."""
    # Create test snapshot
    sprint_data = create_sample_sprint_data(1)
    sprint_metrics = SprintMetrics(**sprint_data)
    snapshot = MetricsSnapshot(
        sprint_id=sprint_metrics.sprint_id,
        sprint_name=sprint_metrics.sprint_name,
        start_date=sprint_metrics.start_date,
        end_date=sprint_metrics.end_date,
        metrics_data=sprint_metrics.model_dump(mode="json"),
    )
    test_db.add(snapshot)
    test_db.commit()

    # Test retrieval
    response = client.get("/metrics/SPRINT-1")
    assert response.status_code == 200
    data = response.json()
    assert data["sprint_id"] == "SPRINT-1"
    assert data["sprint_name"] == "Sprint 1"
    assert "metrics_data" in data


def test_get_metrics_not_found():
    """Test retrieving non-existent metrics returns 404."""
    response = client.get("/metrics/NONEXISTENT")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_metrics(test_db):
    """Test deleting metrics snapshot."""
    # Create test snapshot
    sprint_data = create_sample_sprint_data(1)
    sprint_metrics = SprintMetrics(**sprint_data)
    snapshot = MetricsSnapshot(
        sprint_id=sprint_metrics.sprint_id,
        sprint_name=sprint_metrics.sprint_name,
        start_date=sprint_metrics.start_date,
        end_date=sprint_metrics.end_date,
        metrics_data=sprint_metrics.model_dump(mode="json"),
    )
    test_db.add(snapshot)
    test_db.commit()

    # Test deletion
    response = client.delete("/metrics/SPRINT-1")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

    # Verify deletion
    test_db.expire_all()  # Refresh the session
    snapshot = (
        test_db.query(MetricsSnapshot)
        .filter(MetricsSnapshot.sprint_id == "SPRINT-1")
        .first()
    )
    assert snapshot is None


def test_delete_metrics_not_found():
    """Test deleting non-existent metrics returns 404."""
    response = client.delete("/metrics/NONEXISTENT")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_fetch_metrics_validates_count():
    """Test that fetch validates count parameter range."""
    # No need to mock client for validation tests
    # Test count too low
    response = client.post("/metrics/fetch?count=0")
    assert response.status_code == 422  # Validation error

    # Test count too high
    response = client.post("/metrics/fetch?count=21")
    assert response.status_code == 422  # Validation error
