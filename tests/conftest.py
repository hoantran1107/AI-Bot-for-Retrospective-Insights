"""Shared test configuration and fixtures."""

import os
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Force tests to use SQLite before importing app/database modules
os.environ.setdefault(
    "DATABASE_URL", "sqlite:///file:memdb_test?mode=memory&cache=shared&uri=true"
)
# Force mock metrics usage (no outbound HTTP)
os.environ.setdefault("EXTERNAL_METRICS_API_URL", "")
os.environ.setdefault("EXTERNAL_METRICS_API_KEY", "")
# Default LLM provider to openai for tests; clear Azure to satisfy default tests
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("AZURE_ENDPOINT", "")
os.environ.setdefault("AZURE_DEPLOYMENT", "")

from src.api.dependencies import get_db
from src.api.main import app
from src.core.database import Base

# Create shared test database (in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///file:memdb_test?mode=memory&cache=shared&uri=true"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False, "uri": True}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency once at module level
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Setup and teardown database for each test."""
    # Drop all tables first to ensure clean state
    Base.metadata.drop_all(bind=engine)
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop all tables after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def mock_llm():
    """Mock LLM integration to avoid real API calls."""
    with patch("src.analysis.llm_integration.LLMClient._call_llm") as mock:
        # Return simple mock responses
        mock.return_value = "Mocked LLM response"
        yield mock


@pytest.fixture
def test_db():
    """Provide a database session for tests that need direct DB access."""
    db = next(override_get_db())
    try:
        yield db
    finally:
        db.close()


# Alias for backward compatibility
@pytest.fixture
def test_db_session(test_db):
    """Alias for test_db fixture."""
    return test_db


@pytest.fixture
def sample_sprint_metrics():
    """Provide sample sprint metrics data for testing."""
    from datetime import datetime

    return {
        "sprint_id": "SPRINT-TEST-001",
        "sprint_name": "Test Sprint 1",
        "start_date": datetime(2024, 1, 1).isoformat(),
        "end_date": datetime(2024, 1, 14).isoformat(),
        "team_happiness": 7.5,
        "story_points_completed": 42,
        "story_points_planned": 45,
        "items_completed": 15,
        "items_carried_over": 2,
        "bugs_prod": 3,
        "bugs_acc": 2,
        "review_time": 24.5,
        "coding_time": 120.0,
        "testing_time": 36.0,
        "defect_rate_production": 7.1,
        "story_point_distribution": {"small": 5, "medium": 8, "large": 2},
    }
