"""Tests for reports API endpoints."""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from src.api.main import app
from src.core.database import AnalysisReportDB, MetricsSnapshot
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
        "story_point_distribution": {"small": 5, "medium": 8, "large": 3},
    }


def create_test_metrics(test_db, count: int = 5):
    """Create test metrics snapshots in database."""
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
        test_db.add(snapshot)
    test_db.commit()


def test_generate_report_success(test_db):
    """Test successful report generation."""
    # Create test metrics
    create_test_metrics(test_db, 5)

    # Generate report
    request_data = {"sprint_count": 5}
    response = client.post("/reports/generate", json=request_data)

    assert response.status_code == 200
    data = response.json()

    # Verify report structure
    assert "headline" in data
    assert "summary" in data
    assert "trends" in data
    assert "hypotheses" in data
    assert "suggested_experiments" in data
    assert "charts" in data
    assert "facilitation_guide" in data
    assert "generated_at" in data

    # Verify report was stored in database
    reports = test_db.query(AnalysisReportDB).all()
    assert len(reports) == 1
    assert reports[0].headline == data["headline"]


def test_generate_report_with_specific_sprints(test_db):
    """Test report generation with specific sprint IDs."""
    create_test_metrics(test_db, 5)

    request_data = {"sprint_ids": ["SPRINT-1", "SPRINT-2", "SPRINT-3"]}
    response = client.post("/reports/generate", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "headline" in data


def test_generate_report_with_custom_context(test_db):
    """Test report generation with custom context."""
    create_test_metrics(test_db, 5)

    request_data = {
        "sprint_count": 3,
        "custom_context": "Team recently adopted new testing framework",
    }
    response = client.post("/reports/generate", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "headline" in data


def test_generate_report_with_focus_metrics(test_db):
    """Test report generation with focused metrics."""
    create_test_metrics(test_db, 5)

    request_data = {
        "sprint_count": 4,
        "focus_metrics": ["team_happiness", "avg_review_time_hours"],
    }
    response = client.post("/reports/generate", json=request_data)

    assert response.status_code == 200
    data = response.json()

    # Verify trends include focused metrics
    trend_metrics = [t["metric_name"] for t in data["trends"]]
    assert "team_happiness" in trend_metrics or "avg_review_time_hours" in trend_metrics


def test_generate_report_insufficient_data(test_db):
    """Test report generation fails with insufficient data."""
    # Create only 1 sprint
    create_test_metrics(test_db, 1)

    request_data = {"sprint_count": 5}
    response = client.post("/reports/generate", json=request_data)

    assert response.status_code == 400
    assert "at least 2 sprints" in response.json()["detail"].lower()


def test_generate_report_no_data():
    """Test report generation fails with no data."""
    request_data = {"sprint_count": 5}
    response = client.post("/reports/generate", json=request_data)

    assert response.status_code == 400
    assert "at least 2 sprints" in response.json()["detail"].lower()


def test_list_reports(test_db):
    """Test listing generated reports."""
    # Generate some reports
    create_test_metrics(test_db, 5)

    for i in range(3):
        request_data = {"sprint_count": 3}
        client.post("/reports/generate", json=request_data)

    # List reports
    response = client.get("/reports")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    # Verify response structure
    for report in data:
        assert "id" in report
        assert "report_date" in report
        assert "headline" in report
        assert "summary" in report
        assert "sprint_ids" in report
        assert "created_at" in report


def test_list_reports_with_pagination(test_db):
    """Test listing reports with pagination."""
    create_test_metrics(test_db, 5)

    # Generate multiple reports
    for i in range(10):
        request_data = {"sprint_count": 2}
        client.post("/reports/generate", json=request_data)

    # Test limit
    response = client.get("/reports?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5

    # Test offset
    response = client.get("/reports?limit=3&offset=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_get_report_by_id(test_db):
    """Test retrieving specific report by ID."""
    create_test_metrics(test_db, 5)

    # Generate report
    request_data = {"sprint_count": 3}
    gen_response = client.post("/reports/generate", json=request_data)

    # Get report from database to find ID
    test_db.expire_all()  # Refresh the session
    report = test_db.query(AnalysisReportDB).first()
    report_id = report.id

    # Retrieve report
    response = client.get(f"/reports/{report_id}")
    assert response.status_code == 200
    data = response.json()

    # Verify full report structure
    assert "headline" in data
    assert "summary" in data
    assert "trends" in data
    assert "hypotheses" in data
    assert "suggested_experiments" in data


def test_get_report_not_found():
    """Test retrieving non-existent report returns 404."""
    response = client.get("/reports/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_report(test_db):
    """Test deleting a report."""
    create_test_metrics(test_db, 5)

    # Generate report
    request_data = {"sprint_count": 3}
    client.post("/reports/generate", json=request_data)

    # Get report ID
    test_db.expire_all()  # Refresh the session
    report = test_db.query(AnalysisReportDB).first()
    report_id = report.id

    # Delete report
    response = client.delete(f"/reports/{report_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

    # Verify deletion by trying to get it via API (should return 404)
    get_response = client.get(f"/reports/{report_id}")
    assert get_response.status_code == 404


def test_delete_report_not_found():
    """Test deleting non-existent report returns 404."""
    response = client.delete("/reports/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_report_stores_hypotheses_and_experiments(test_db):
    """Test that generated report stores related hypotheses and experiments."""
    # Create test data with strong patterns to trigger hypothesis generation
    for i in range(1, 6):
        start_date = datetime.utcnow() - timedelta(days=14 * (6 - i))
        end_date = start_date + timedelta(days=14)

        # Create data with clear patterns (most recent sprint has worst metrics):
        # - Increasing review time (trigger review bottleneck hypothesis)
        # - Increasing production bugs (trigger quality hypothesis)
        # - Decreasing happiness (trigger morale hypothesis)
        # Note: i=1 is oldest (70 days ago), i=5 is most recent (14 days ago)
        sprint_data = {
            "sprint_id": f"SPRINT-TEST-{i}",
            "sprint_name": f"Sprint {i}",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "team_happiness": 10.0 - i,  # DECREASING: 9, 8, 7, 6, 5 (getting worse)
            "story_points_completed": 30 + i * 2,  # Increasing: 32, 34, 36, 38, 40
            "story_points_planned": 35 + i * 2,  # Increasing: 37, 39, 41, 43, 45
            "items_completed": 10 + i,  # Increasing: 11, 12, 13, 14, 15
            "story_point_distribution": {"small": 3, "medium": 8 + i, "large": 2 + i},
            # Time metrics - review time INCREASING (getting worse over time)
            "review_time": 10.0 + i * 10,  # INCREASING: 20, 30, 40, 50, 60 hours
            "coding_time": 60.0 + i * 5,  # INCREASING: 65, 70, 75, 80, 85
            "testing_time": 20.0 + i * 3,  # INCREASING: 23, 26, 29, 32, 35
            # Bug metrics - production bugs INCREASING (getting worse)
            "bugs_prod": i,  # INCREASING: 1, 2, 3, 4, 5 bugs
            "defect_rate_production": (i / (30 + i * 2))
            * 100,  # Increasing defect rate
        }
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

    # Generate report
    request_data = {"sprint_count": 5}
    response = client.post("/reports/generate", json=request_data)
    assert response.status_code == 200

    # Verify report was stored in database
    test_db.expire_all()  # Refresh the session
    report = test_db.query(AnalysisReportDB).first()
    assert report is not None, "Report should be stored in database"

    # Check response and database consistency
    report_data = response.json()
    num_hypotheses_in_response = len(report_data.get("hypotheses", []))
    num_experiments_in_response = len(report_data.get("suggested_experiments", []))

    # Verify that what's in the API response matches what's in the database
    from src.core.database import ExperimentDB, HypothesisDB

    hypotheses_in_db = (
        test_db.query(HypothesisDB).filter(HypothesisDB.report_id == report.id).all()
    )
    experiments_in_db = (
        test_db.query(ExperimentDB).filter(ExperimentDB.report_id == report.id).all()
    )

    # The counts should match between API and database
    assert len(hypotheses_in_db) == num_hypotheses_in_response, (
        f"Database should have {num_hypotheses_in_response} hypotheses, "
        f"but found {len(hypotheses_in_db)}"
    )
    assert len(experiments_in_db) == num_experiments_in_response, (
        f"Database should have {num_experiments_in_response} experiments, "
        f"but found {len(experiments_in_db)}"
    )
