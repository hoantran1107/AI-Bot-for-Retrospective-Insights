"""
Unit tests for core configuration.
"""

from src.core.config import Settings, settings


def test_settings_initialization():
    """Test that settings can be initialized."""
    test_settings = Settings()
    assert test_settings.app_name == "AI Retrospective Insights"
    assert test_settings.app_version == "1.0.0"
    assert test_settings.default_sprint_count == 5


def test_settings_defaults():
    """Test default configuration values."""
    test_settings = Settings()
    assert test_settings.trend_threshold == 0.20
    assert test_settings.correlation_threshold == 0.6
    assert test_settings.confidence_high_threshold == 0.8
    assert test_settings.confidence_medium_threshold == 0.5


def test_settings_llm_provider():
    """Test LLM provider configuration."""
    test_settings = Settings()
    assert test_settings.llm_provider in ["openai", "anthropic"]
    assert test_settings.llm_model is not None


def test_global_settings_instance():
    """Test that global settings instance exists."""
    assert settings is not None
    assert isinstance(settings, Settings)


def test_database_url_format():
    """Test database URL has correct format."""
    test_settings = Settings()
    assert test_settings.database_url.startswith(
        "postgresql://"
    ) or test_settings.database_url.startswith("sqlite://")


def test_redis_url_format():
    """Test Redis URL has correct format."""
    test_settings = Settings()
    assert test_settings.redis_url.startswith("redis://")
