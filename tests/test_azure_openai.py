"""
Tests for Azure OpenAI integration.
"""

from unittest.mock import Mock, patch

from src.analysis.llm_integration import LLMClient
from src.core.config import Settings


def test_azure_openai_initialization():
    """Test Azure OpenAI client initialization."""
    mock_settings = Settings(
        llm_provider="azure",
        chat_completion_api_key="test-key",
        azure_endpoint="https://test.openai.azure.com/",
        azure_deployment="test-deployment",
        azure_api_version="2024-02-15-preview",
    )

    with patch("src.analysis.llm_integration.settings", mock_settings):
        with patch("openai.AzureOpenAI") as mock_azure:
            llm = LLMClient(provider="azure", api_key="test-key")

            # Verify AzureOpenAI was called with correct parameters
            mock_azure.assert_called_once_with(
                api_key="test-key",
                azure_endpoint="https://test.openai.azure.com/",
                api_version="2024-02-15-preview",
                azure_deployment="test-deployment",
            )


def test_azure_openai_missing_endpoint():
    """Test Azure OpenAI initialization fails without endpoint."""
    mock_settings = Settings(
        llm_provider="azure",
        chat_completion_api_key="test-key",
        azure_endpoint="",  # Missing endpoint
        azure_deployment="test-deployment",
    )

    with patch("src.analysis.llm_integration.settings", mock_settings):
        llm = LLMClient(provider="azure", api_key="test-key")

        # Client should be None due to missing endpoint
        assert llm.client is None


def test_azure_openai_missing_deployment():
    """Test Azure OpenAI initialization fails without deployment."""
    mock_settings = Settings(
        llm_provider="azure",
        chat_completion_api_key="test-key",
        azure_endpoint="https://test.openai.azure.com/",
        azure_deployment="",  # Missing deployment
    )

    with patch("src.analysis.llm_integration.settings", mock_settings):
        llm = LLMClient(provider="azure", api_key="test-key")

        # Client should be None due to missing deployment
        assert llm.client is None


def test_azure_openai_call_llm():
    """Test Azure OpenAI LLM call uses deployment name."""
    mock_settings = Settings(
        llm_provider="azure",
        chat_completion_api_key="test-key",
        azure_endpoint="https://test.openai.azure.com/",
        azure_deployment="gpt-4-deployment",
        azure_api_version="2024-02-15-preview",
    )

    # Setup mock client
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Test response"
    mock_client.chat.completions.create.return_value = mock_response

    with patch("src.analysis.llm_integration.settings", mock_settings):
        with patch("openai.AzureOpenAI", return_value=mock_client):
            # Create LLM client
            llm = LLMClient(provider="azure", api_key="test-key")

            # Call LLM
            result = llm._call_llm(system_prompt="Test system", user_prompt="Test user")

            # Verify it used the deployment name, not the model
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["model"] == "gpt-4-deployment"
            assert result == "Test response"


def test_azure_config_in_settings():
    """Test Azure configuration is properly defined in Settings."""
    settings = Settings(
        azure_endpoint="https://test.openai.azure.com/",
        azure_deployment="test-deployment",
        azure_api_version="2024-02-15-preview",
    )

    assert settings.azure_endpoint == "https://test.openai.azure.com/"
    assert settings.azure_deployment == "test-deployment"
    assert settings.azure_api_version == "2024-02-15-preview"


def test_azure_config_defaults():
    """Test Azure configuration has sensible defaults."""
    settings = Settings()

    # Endpoint and deployment should be empty by default
    assert settings.azure_endpoint == ""
    assert settings.azure_deployment == ""

    # API version should have a default value
    assert settings.azure_api_version == "2024-02-15-preview"
