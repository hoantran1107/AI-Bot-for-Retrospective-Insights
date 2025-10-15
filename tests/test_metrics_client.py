"""
Unit tests for metrics API client.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from src.core.models import SprintMetrics
from src.utils.metrics_client import MetricsAPIError, MetricsClient, get_metrics_client


@pytest.fixture
def metrics_client():
    """Create a test metrics client."""
    return MetricsClient(
        api_url="https://test-api.com", api_key="test-key-123", timeout=10
    )


@pytest.fixture
def mock_sprint_data():
    """Mock sprint data from API."""
    return {
        "sprint_id": "SPRINT-2024-01",
        "sprint_name": "Sprint 24.01",
        "start_date": "2024-01-01T00:00:00",
        "end_date": "2024-01-14T23:59:59",
        "team_happiness": 7.5,
        "story_points_completed": 42,
        "review_time": 24.3,
    }


def test_metrics_client_initialization():
    """Test MetricsClient initialization."""
    client = MetricsClient(api_url="https://api.example.com", api_key="secret-key")

    assert client.api_url == "https://api.example.com"
    assert client.api_key == "secret-key"
    assert "Authorization" in client.headers
    assert client.timeout == 30


def test_metrics_client_default_settings():
    """Test MetricsClient uses settings by default."""
    client = MetricsClient()
    assert client.timeout == 30


@pytest.mark.asyncio
async def test_fetch_sprints_mock_data():
    """Test fetching sprints with mock data (no API configured)."""
    client = MetricsClient(api_url="", api_key="")

    sprints = await client.fetch_sprints(count=3)

    assert len(sprints) == 3
    assert sprints[0]["sprint_id"] == "SPRINT-2024-01"
    assert "team_happiness" in sprints[0]
    assert "review_time" in sprints[0]


@pytest.mark.asyncio
async def test_fetch_sprints_success(metrics_client, mock_sprint_data):
    """Test successful fetch of sprints from API."""
    mock_response = Mock()
    mock_response.json.return_value = [mock_sprint_data]
    mock_response.status_code = 200

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        sprints = await metrics_client.fetch_sprints(count=1)

        assert len(sprints) == 1
        assert sprints[0]["sprint_id"] == "SPRINT-2024-01"
        mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_sprints_with_team_id(metrics_client, mock_sprint_data):
    """Test fetching sprints with team_id parameter."""
    mock_response = Mock()
    mock_response.json.return_value = [mock_sprint_data]
    mock_response.status_code = 200

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        await metrics_client.fetch_sprints(count=5, team_id="TEAM-001")

        # Verify team_id was passed in params
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["params"]["team_id"] == "TEAM-001"


@pytest.mark.asyncio
async def test_fetch_sprints_http_error(metrics_client):
    """Test handling of HTTP error."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not found", request=Mock(), response=mock_response
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        with pytest.raises(MetricsAPIError, match="API returned status 404"):
            await metrics_client.fetch_sprints()


@pytest.mark.asyncio
async def test_fetch_sprints_connection_error(metrics_client):
    """Test handling of connection error."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.RequestError("Connection failed")

        with pytest.raises(MetricsAPIError, match="Failed to connect to API"):
            await metrics_client.fetch_sprints()


@pytest.mark.asyncio
async def test_fetch_sprint_metrics_success(metrics_client, mock_sprint_data):
    """Test fetching single sprint metrics."""
    mock_response = Mock()
    mock_response.json.return_value = mock_sprint_data
    mock_response.status_code = 200

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        metrics = await metrics_client.fetch_sprint_metrics("SPRINT-2024-01")

        assert metrics["sprint_id"] == "SPRINT-2024-01"
        assert metrics["team_happiness"] == 7.5


@pytest.mark.asyncio
async def test_fetch_sprint_metrics_mock_data():
    """Test fetching sprint metrics with mock data."""
    client = MetricsClient(api_url="", api_key="")

    metrics = await client.fetch_sprint_metrics("SPRINT-2024-01")

    assert metrics["sprint_id"] == "SPRINT-2024-01"
    assert "team_happiness" in metrics


def test_validate_and_transform_success(metrics_client, mock_sprint_data):
    """Test validation and transformation of valid data."""
    metrics = metrics_client.validate_and_transform(mock_sprint_data)

    assert isinstance(metrics, SprintMetrics)
    assert metrics.sprint_id == "SPRINT-2024-01"
    assert metrics.team_happiness == 7.5


def test_validate_and_transform_with_string_dates(metrics_client):
    """Test transformation of string dates to datetime."""
    data = {
        "sprint_id": "TEST",
        "sprint_name": "Test Sprint",
        "start_date": "2024-01-01T00:00:00",
        "end_date": "2024-01-14T23:59:59",
        "team_happiness": 8.0,
    }

    metrics = metrics_client.validate_and_transform(data)

    assert isinstance(metrics.start_date, datetime)
    assert isinstance(metrics.end_date, datetime)


def test_validate_and_transform_invalid_data(metrics_client):
    """Test validation fails for invalid data."""
    invalid_data = {
        "sprint_id": "TEST",
        # Missing required fields
    }

    with pytest.raises(ValueError, match="Invalid metrics data"):
        metrics_client.validate_and_transform(invalid_data)


def test_get_mock_data(metrics_client):
    """Test mock data generation."""
    mock_data = metrics_client._get_mock_data(count=3)

    assert len(mock_data) == 3
    assert mock_data[0]["sprint_id"] == "SPRINT-2024-01"
    assert mock_data[1]["sprint_id"] == "SPRINT-2024-02"

    # Verify trends in mock data
    assert mock_data[1]["team_happiness"] < mock_data[0]["team_happiness"]
    assert mock_data[1]["review_time"] > mock_data[0]["review_time"]


def test_get_mock_sprint_data(metrics_client):
    """Test mock sprint data generation."""
    mock_data = metrics_client._get_mock_sprint_data("SPRINT-2024-05")

    assert mock_data["sprint_id"] == "SPRINT-2024-05"
    assert "team_happiness" in mock_data
    assert "review_time" in mock_data


def test_get_metrics_client_singleton():
    """Test global metrics client instance."""
    client1 = get_metrics_client()
    client2 = get_metrics_client()

    assert client1 is client2  # Same instance


def test_client_headers_include_auth(metrics_client):
    """Test that client headers include authorization."""
    assert "Authorization" in metrics_client.headers
    assert metrics_client.headers["Authorization"] == "Bearer test-key-123"
    assert metrics_client.headers["Content-Type"] == "application/json"
