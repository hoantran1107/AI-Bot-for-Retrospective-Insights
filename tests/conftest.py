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
# Set other required environment variables for tests
os.environ.setdefault("CHAT_COMPLETION_API_KEY", "test-key")
os.environ.setdefault("LLM_MODEL", "gpt-4")
os.environ.setdefault("TREND_THRESHOLD", "0.20")
os.environ.setdefault("CORRELATION_THRESHOLD", "0.6")
os.environ.setdefault("CONFIDENCE_HIGH_THRESHOLD", "0.8")
os.environ.setdefault("CONFIDENCE_MEDIUM_THRESHOLD", "0.5")
os.environ.setdefault("DEFAULT_SPRINT_COUNT", "5")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("AZURE_API_VERSION", "2024-02-15-preview")

from dotenv import load_dotenv

from src.api.dependencies import get_db
from src.api.main import app
from src.core.database import Base

load_dotenv()

# Global database configuration - will be overridden per test file
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_global.db"
engine = None
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def setup_test_database():
    """Setup database for each test module (file)."""
    global engine, TestingSessionLocal

    # Create unique database for this test file
    db_url = "sqlite:///./test.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Drop all tables first to ensure clean state
    Base.metadata.drop_all(bind=engine)
    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield

    # Cleanup after all tests in this module
    try:
        Base.metadata.drop_all(bind=engine)
    except Exception:
        pass  # Ignore cleanup errors
    finally:
        engine.dispose()


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency - this will be called after database setup
@pytest.fixture(scope="module", autouse=True)
def setup_dependencies(setup_test_database):
    """Setup FastAPI dependencies for testing."""
    app.dependency_overrides.clear()  # Clear existing overrides
    app.dependency_overrides[get_db] = override_get_db

    yield

    # Cleanup dependencies
    app.dependency_overrides.clear()


@pytest.fixture(scope="module", autouse=True)
def mock_llm(setup_test_database):
    """Mock LLM integration to avoid real API calls."""
    with patch("src.analysis.llm_integration.LLMClient._call_llm") as mock:
        # Return simple mock responses
        mock.return_value = "Mocked LLM response"
        yield mock


@pytest.fixture
def test_db():
    """Provide a database session for tests that need direct DB access."""
    # Create fresh session for each test and ensure clean state
    db = TestingSessionLocal()

    # Clear all data from database for this test
    try:
        # Import models here to avoid circular imports
        from src.core.database import (
            AnalysisReportDB,
            AnalysisTaskDB,
            ExperimentDB,
            HypothesisDB,
            MetricsSnapshot,
        )

        db.query(MetricsSnapshot).delete()
        db.query(AnalysisReportDB).delete()
        db.query(HypothesisDB).delete()
        db.query(ExperimentDB).delete()
        db.query(AnalysisTaskDB).delete()
        db.commit()
    except Exception:
        db.rollback()

    try:
        yield db
    finally:
        try:
            db.rollback()
            db.close()
        except Exception:
            pass


@pytest.fixture(autouse=True)
def reset_database():
    """Ensure clean database state for each test."""
    # This runs before each test to ensure clean state
    # Database tables are already created by setup_test_database fixture
    pass


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
