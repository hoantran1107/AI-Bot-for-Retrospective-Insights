"""FastAPI dependencies for dependency injection."""

from typing import Generator

from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.database import SessionLocal
from src.utils.metrics_client import MetricsClient


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_metrics_client() -> MetricsClient:
    """
    Get metrics client instance.

    Returns:
        MetricsClient instance
    """
    settings = get_settings()
    return MetricsClient(
        api_url=settings.external_metrics_api_url,
        api_key=settings.external_metrics_api_key,
        timeout=30,
    )


