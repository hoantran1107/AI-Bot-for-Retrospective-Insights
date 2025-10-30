"""
Client to fetch dashboard data from N8N webhooks.
"""

import logging
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime, timedelta

import httpx

logger = logging.getLogger(__name__)

# Chart types supported by the dashboard API
ChartType = Literal[
    "testing-time",
    "review-time",
    "coding-time",
    "root-cause",
    "open-bugs-over-time",
    "bugs-per-environment",
    "sp-distribution",
    "items-out-of-sprint",
    "defect-rate-prod",
    "defect-rate-all",
    "happiness",
]


class DashboardAPIError(Exception):
    """Exception raised for errors in dashboard API."""

    pass


class TokenExpiredError(DashboardAPIError):
    """Exception raised when the API token has expired."""

    pass


class DashboardClient:
    """Client for fetching dashboard chart data from N8N webhooks."""

    # N8N webhook endpoints
    TOKEN_URL = (
        "https://n8n.idp.infodation.vn/webhook/88eda05f-41d5-4ce4-b836-cb0f1bba3b2e"
    )
    DATA_URL = (
        "https://n8n.idp.infodation.vn/webhook/39c5b0e5-4aca-4964-a718-5d3deeebed25"
    )

    def __init__(self, timeout: int = 30):
        """
        Initialize dashboard client.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self._token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    async def _fetch_token(self) -> str:
        """
        Fetch authentication token from N8N webhook.

        Returns:
            Authentication token

        Raises:
            DashboardAPIError: If token fetch fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.TOKEN_URL)
                response.raise_for_status()

                data = response.json()
                token = data.get("token")

                if not token:
                    raise DashboardAPIError("No token in response")

                # Token expires in 300 seconds (5 minutes)
                self._token = token
                self._token_expires_at = datetime.now() + timedelta(
                    seconds=290
                )  # 10s buffer

                logger.info("Successfully fetched authentication token")
                return token

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching token: {e}")
            raise DashboardAPIError(
                f"API returned status {e.response.status_code}"
            ) from e
        except httpx.RequestError as e:
            logger.error(f"Request error fetching token: {e}")
            raise DashboardAPIError(f"Failed to connect to API: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error fetching token: {e}")
            raise DashboardAPIError(f"Unexpected error: {str(e)}") from e

    async def _get_valid_token(self) -> str:
        """
        Get a valid authentication token, refreshing if necessary.

        Returns:
            Valid authentication token

        Raises:
            DashboardAPIError: If token fetch fails
        """
        now = datetime.now()

        # Fetch new token if we don't have one or it's expired
        if (
            not self._token
            or not self._token_expires_at
            or now >= self._token_expires_at
        ):
            return await self._fetch_token()

        return self._token

    async def fetch_chart_data(
        self, chart_name: ChartType, retry_on_auth_error: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch data for a specific chart from the dashboard API.

        Args:
            chart_name: Name of the chart to fetch (e.g., "testing-time", "happiness")
            retry_on_auth_error: Whether to retry once on authentication error

        Returns:
            Chart data dictionary

        Raises:
            DashboardAPIError: If API request fails
            TokenExpiredError: If token is expired and retry fails
        """
        token = await self._get_valid_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        params = {"name": chart_name}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.DATA_URL, headers=headers, params=params
                )

                # If unauthorized and retry is enabled, fetch new token and retry
                if response.status_code == 401 and retry_on_auth_error:
                    logger.warning("Token expired, fetching new token and retrying")
                    self._token = None  # Force token refresh
                    return await self.fetch_chart_data(
                        chart_name, retry_on_auth_error=False
                    )

                response.raise_for_status()
                data = response.json()

                logger.info(f"Successfully fetched data for chart: {chart_name}")
                return data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise TokenExpiredError("Authentication token expired") from e
            logger.error(f"HTTP error fetching chart data: {e}")
            raise DashboardAPIError(
                f"API returned status {e.response.status_code}"
            ) from e
        except httpx.RequestError as e:
            logger.error(f"Request error fetching chart data: {e}")
            raise DashboardAPIError(f"Failed to connect to API: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error fetching chart data: {e}")
            raise DashboardAPIError(f"Unexpected error: {str(e)}") from e

    async def fetch_all_charts(self) -> Dict[str, Dict[str, Any]]:
        """
        Fetch data for all supported charts.

        Returns:
            Dictionary mapping chart names to their data

        Raises:
            DashboardAPIError: If any API request fails
        """
        chart_types: List[ChartType] = [
            "testing-time",
            "review-time",
            "coding-time",
            "root-cause",
            "open-bugs-over-time",
            "bugs-per-environment",
            "sp-distribution",
            "items-out-of-sprint",
            "defect-rate-prod",
            "defect-rate-all",
            "happiness",
        ]

        results = {}

        for chart_type in chart_types:
            try:
                data = await self.fetch_chart_data(chart_type)
                results[chart_type] = data
            except Exception as e:
                logger.error(f"Failed to fetch {chart_type}: {e}")
                results[chart_type] = {"error": str(e)}

        return results

    async def fetch_multiple_charts(
        self, chart_names: List[ChartType]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch data for multiple specific charts.

        Args:
            chart_names: List of chart names to fetch

        Returns:
            Dictionary mapping chart names to their data

        Raises:
            DashboardAPIError: If any API request fails
        """
        results = {}

        for chart_name in chart_names:
            try:
                data = await self.fetch_chart_data(chart_name)
                results[chart_name] = data
            except Exception as e:
                logger.error(f"Failed to fetch {chart_name}: {e}")
                results[chart_name] = {"error": str(e)}

        return results

    def invalidate_token(self):
        """Invalidate the current token to force refresh on next request."""
        self._token = None
        self._token_expires_at = None


# Global client instance
_dashboard_client_instance: Optional[DashboardClient] = None


def get_dashboard_client() -> DashboardClient:
    """Get global dashboard client instance."""
    global _dashboard_client_instance
    if _dashboard_client_instance is None:
        _dashboard_client_instance = DashboardClient()
    return _dashboard_client_instance
