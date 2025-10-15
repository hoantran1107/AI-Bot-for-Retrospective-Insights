"""
Application configuration management using Pydantic Settings.
"""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "AI Retrospective Insights"
    app_version: str = "1.0.0"
    debug: bool = True
    environment: str = "development"

    # Database
    database_url: str = "sqlite:///./retro_insights.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # External Metrics API
    external_metrics_api_url: str = ""
    external_metrics_api_key: str = ""

    # LLM Configuration
    llm_provider: Literal["openai", "anthropic", "azure"] = "openai"
    chat_completion_api_key: str = ""
    llm_model: str = "gpt-4"

    # Azure OpenAI Configuration (only needed if llm_provider is "azure")
    azure_endpoint: str = ""
    azure_api_version: str = "2024-02-15-preview"
    azure_deployment: str = ""

    # Analysis Configuration
    default_sprint_count: int = 5
    trend_threshold: float = 0.20  # 20% change considered significant
    correlation_threshold: float = 0.6  # |r| > 0.6 considered strong
    confidence_high_threshold: float = 0.8
    confidence_medium_threshold: float = 0.5

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


# Global settings instance
_settings = None


def get_settings() -> Settings:
    """
    Get settings instance (singleton pattern).

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Convenience alias for backward compatibility
settings = get_settings()
