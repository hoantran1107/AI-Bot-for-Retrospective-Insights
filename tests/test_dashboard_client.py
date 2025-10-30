"""Tests for dashboard data client."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from src.utils.dashboard_client import (
    DashboardClient,
    DashboardAPIError,
    TokenExpiredError,
    get_dashboard_client,
)


@pytest.fixture
def dashboard_client():
    """Create a dashboard client instance for testing."""
    return DashboardClient(timeout=10)


@pytest.fixture
def mock_token_response():
    """Mock token response from API."""
    return {"token": "test-token-12345"}


@pytest.fixture
def mock_chart_data():
    """Mock chart data response from API."""
    return {
        "values": [10, 15, 20, 25, 30],
        "labels": ["Sprint 1", "Sprint 2", "Sprint 3", "Sprint 4", "Sprint 5"],
        "metadata": {"chart_type": "line", "unit": "hours"},
    }


class TestDashboardClient:
    """Test suite for DashboardClient."""

    @pytest.mark.asyncio
    async def test_fetch_token_success(self, dashboard_client, mock_token_response):
        """Test successful token fetch."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_token_response
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            token = await dashboard_client._fetch_token()

            assert token == "test-token-12345"
            assert dashboard_client._token == "test-token-12345"
            assert dashboard_client._token_expires_at is not None

    @pytest.mark.asyncio
    async def test_fetch_token_no_token_in_response(self, dashboard_client):
        """Test token fetch with missing token in response."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {}
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(DashboardAPIError, match="No token in response"):
                await dashboard_client._fetch_token()

    @pytest.mark.asyncio
    async def test_get_valid_token_fresh_token(
        self, dashboard_client, mock_token_response
    ):
        """Test getting valid token when token is fresh."""
        # Set a valid token
        dashboard_client._token = "existing-token"
        dashboard_client._token_expires_at = datetime.now() + timedelta(seconds=100)

        token = await dashboard_client._get_valid_token()

        assert token == "existing-token"

    @pytest.mark.asyncio
    async def test_get_valid_token_expired_token(
        self, dashboard_client, mock_token_response
    ):
        """Test getting valid token when token is expired."""
        # Set an expired token
        dashboard_client._token = "expired-token"
        dashboard_client._token_expires_at = datetime.now() - timedelta(seconds=10)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_token_response
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            token = await dashboard_client._get_valid_token()

            assert token == "test-token-12345"

    @pytest.mark.asyncio
    async def test_fetch_chart_data_success(
        self, dashboard_client, mock_token_response, mock_chart_data
    ):
        """Test successful chart data fetch."""
        with patch.object(
            dashboard_client, "_get_valid_token", return_value="test-token"
        ):
            with patch("httpx.AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = mock_chart_data
                mock_response.raise_for_status = MagicMock()

                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )

                data = await dashboard_client.fetch_chart_data("happiness")

                assert data == mock_chart_data

    @pytest.mark.asyncio
    async def test_fetch_chart_data_with_retry_on_auth_error(
        self, dashboard_client, mock_token_response, mock_chart_data
    ):
        """Test chart data fetch with retry on authentication error."""
        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            mock_response = MagicMock()
            if call_count == 1:
                # First call returns 401
                mock_response.status_code = 401
            else:
                # Second call returns success
                mock_response.status_code = 200
                mock_response.json.return_value = mock_chart_data

            mock_response.raise_for_status = MagicMock()
            return mock_response

        with patch.object(
            dashboard_client, "_get_valid_token", return_value="test-token"
        ):
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get = mock_get

                data = await dashboard_client.fetch_chart_data("happiness")

                assert data == mock_chart_data
                assert call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_all_charts(
        self, dashboard_client, mock_token_response, mock_chart_data
    ):
        """Test fetching all charts."""
        with patch.object(
            dashboard_client, "fetch_chart_data", return_value=mock_chart_data
        ):
            results = await dashboard_client.fetch_all_charts()

            assert isinstance(results, dict)
            assert len(results) == 11  # Total number of chart types
            assert "happiness" in results
            assert "defect-rate-all" in results

    @pytest.mark.asyncio
    async def test_fetch_multiple_charts(
        self, dashboard_client, mock_token_response, mock_chart_data
    ):
        """Test fetching specific multiple charts."""
        with patch.object(
            dashboard_client, "fetch_chart_data", return_value=mock_chart_data
        ):
            chart_names = ["happiness", "review-time", "coding-time"]
            results = await dashboard_client.fetch_multiple_charts(chart_names)

            assert isinstance(results, dict)
            assert len(results) == 3
            assert all(name in results for name in chart_names)

    def test_invalidate_token(self, dashboard_client):
        """Test token invalidation."""
        dashboard_client._token = "some-token"
        dashboard_client._token_expires_at = datetime.now() + timedelta(seconds=100)

        dashboard_client.invalidate_token()

        assert dashboard_client._token is None
        assert dashboard_client._token_expires_at is None


def test_get_dashboard_client_singleton():
    """Test that get_dashboard_client returns the same instance."""
    client1 = get_dashboard_client()
    client2 = get_dashboard_client()

    assert client1 is client2
