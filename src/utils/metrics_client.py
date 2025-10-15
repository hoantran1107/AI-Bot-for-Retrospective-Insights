"""
Client to fetch team metrics from external API.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from src.core.config import settings
from src.core.models import SprintMetrics

logger = logging.getLogger(__name__)


class MetricsAPIError(Exception):
    """Exception raised for errors in metrics API."""

    pass


class MetricsClient:
    """Client for fetching team metrics from external API."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize metrics client.

        Args:
            api_url: Base URL of metrics API
            api_key: API authentication key
            timeout: Request timeout in seconds
        """
        self.api_url = api_url or settings.external_metrics_api_url
        self.api_key = api_key or settings.external_metrics_api_key
        self.timeout = timeout

        if not self.api_url:
            logger.warning("Metrics API URL not configured")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def fetch_sprints(
        self, count: int = 5, team_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch latest sprints data from external API.

        Args:
            count: Number of sprints to fetch
            team_id: Optional team identifier

        Returns:
            List of sprint data dictionaries

        Raises:
            MetricsAPIError: If API request fails
        """
        if not self.api_url:
            # Return mock data for development/testing
            logger.warning("Using mock data - API URL not configured")
            return self._get_mock_data(count)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {"count": count}
                if team_id:
                    params["team_id"] = team_id

                response = await client.get(
                    f"{self.api_url}/sprints", headers=self.headers, params=params
                )

                response.raise_for_status()
                data = response.json()

                logger.info(f"Fetched {len(data)} sprints from API")
                return data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching sprints: {e}")
            raise MetricsAPIError(
                f"API returned status {e.response.status_code}"
            ) from e
        except httpx.RequestError as e:
            logger.error(f"Request error fetching sprints: {e}")
            raise MetricsAPIError(f"Failed to connect to API: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error fetching sprints: {e}")
            raise MetricsAPIError(f"Unexpected error: {str(e)}") from e

    async def fetch_sprint_metrics(self, sprint_id: str) -> Dict[str, Any]:
        """
        Fetch detailed metrics for a specific sprint.

        Args:
            sprint_id: Sprint identifier

        Returns:
            Sprint metrics dictionary

        Raises:
            MetricsAPIError: If API request fails
        """
        if not self.api_url:
            logger.warning("Using mock data - API URL not configured")
            return self._get_mock_sprint_data(sprint_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_url}/sprints/{sprint_id}", headers=self.headers
                )

                response.raise_for_status()
                data = response.json()

                logger.info(f"Fetched metrics for sprint {sprint_id}")
                return data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching sprint {sprint_id}: {e}")
            raise MetricsAPIError(
                f"API returned status {e.response.status_code}"
            ) from e
        except httpx.RequestError as e:
            logger.error(f"Request error fetching sprint {sprint_id}: {e}")
            raise MetricsAPIError(f"Failed to connect to API: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error fetching sprint {sprint_id}: {e}")
            raise MetricsAPIError(f"Unexpected error: {str(e)}") from e

    def validate_and_transform(self, raw_data: Dict[str, Any]) -> SprintMetrics:
        """
        Validate and transform raw API data to SprintMetrics model.

        Args:
            raw_data: Raw data from API

        Returns:
            Validated SprintMetrics instance

        Raises:
            ValueError: If data validation fails
        """
        try:
            # Transform date strings to datetime if needed
            if isinstance(raw_data.get("start_date"), str):
                raw_data["start_date"] = datetime.fromisoformat(
                    raw_data["start_date"].replace("Z", "+00:00")
                )

            if isinstance(raw_data.get("end_date"), str):
                raw_data["end_date"] = datetime.fromisoformat(
                    raw_data["end_date"].replace("Z", "+00:00")
                )

            # Validate using Pydantic model
            metrics = SprintMetrics(**raw_data)
            return metrics

        except Exception as e:
            logger.error(f"Failed to validate metrics data: {e}")
            raise ValueError(f"Invalid metrics data: {str(e)}") from e

    def _get_mock_data(self, count: int = 5) -> List[Dict[str, Any]]:
        """Generate mock sprint data for testing."""
        sprints = []
        for i in range(count):
            sprint_num = i + 1
            sprints.append(
                {
                    "sprint_id": f"SPRINT-2024-{sprint_num:02d}",
                    "sprint_name": f"Sprint 24.{sprint_num:02d}",
                    "start_date": f"2024-{sprint_num:02d}-01T00:00:00",
                    "end_date": f"2024-{sprint_num:02d}-14T23:59:59",
                    "team_happiness": 7.5 - (i * 0.2),
                    "story_points_completed": 40 + (i * 2),
                    "story_points_planned": 45,
                    "story_point_distribution": {
                        "small": 5,
                        "medium": 8 + i,
                        "large": 3,
                    },
                    "items_completed": 15 + i,
                    "items_carried_over": 2 + (i % 3),
                    "items_out_of_sprint_percent": 10.0 + (i * 2),
                    "defect_rate_production": 0.05 + (i * 0.01),
                    "defect_rate_all": 0.12 + (i * 0.02),
                    "bugs_prod": 2 + i,
                    "bugs_acc": 3 + i,
                    "bugs_test": 4,
                    "bugs_dev": 1,
                    "bugs_other": 0,
                    "open_bugs_count": 5 + (i * 2),
                    "bugs_missed_testing": 3,
                    "bugs_missed_impact": 2,
                    "bugs_requirement_gap": 1,
                    "bugs_configuration": 1,
                    "bugs_third_party": 1,
                    "bugs_database": 1,
                    "bugs_security": 0,
                    "coding_time": 100.0 + (i * 5),
                    "review_time": 20.0 + (i * 3),
                    "testing_time": 18.0 + (i * 2),
                }
            )

        return sprints

    def _get_mock_sprint_data(self, sprint_id: str) -> Dict[str, Any]:
        """Generate mock data for a specific sprint."""
        return {
            "sprint_id": sprint_id,
            "sprint_name": f"Sprint {sprint_id.split('-')[-1]}",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-01-14T23:59:59",
            "team_happiness": 7.5,
            "story_points_completed": 42,
            "story_points_planned": 45,
            "review_time": 24.3,
            "coding_time": 120.5,
            "testing_time": 18.7,
        }


# Global client instance
_client_instance: Optional[MetricsClient] = None


def get_metrics_client() -> MetricsClient:
    """Get global metrics client instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = MetricsClient()
    return _client_instance
