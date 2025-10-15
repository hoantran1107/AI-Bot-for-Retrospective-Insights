"""Tests for health check API endpoints."""

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns API information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Retrospective Insights API"
    assert data["version"] == "1.0.0"
    assert "docs" in data
    assert "health" in data


def test_health_check_success():
    """Test health check endpoint returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "database" in data
    assert "environment" in data


def test_health_check_database_status():
    """Test health check includes database connectivity status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    # Database should be healthy with test setup
    assert data["database"] == "healthy"
    assert data["status"] == "healthy"
