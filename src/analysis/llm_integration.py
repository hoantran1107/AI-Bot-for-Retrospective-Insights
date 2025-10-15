"""
LLM integration for generating narrative insights.
Supports OpenAI and Anthropic APIs.
"""

import logging
from typing import Any, Dict, List, Optional

from src.core.config import settings
from src.core.models import Hypothesis, TrendAnalysis

logger = logging.getLogger(__name__)


class LLMIntegrationError(Exception):
    """Exception raised for LLM integration errors."""

    pass


class LLMClient:
    """Client for LLM API integration."""

    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize LLM client.

        Args:
            provider: LLM provider ("openai" or "anthropic")
            model: Model name
            api_key: API key for the provider
        """
        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model

        if self.provider == "openai":
            self.api_key = api_key or settings.chat_completion_api_key
        elif self.provider == "anthropic":
            self.api_key = api_key or settings.chat_completion_api_key
        elif self.provider == "azure":
            self.api_key = api_key or settings.chat_completion_api_key
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

        self.client = self._initialize_client()

    def _initialize_client(self):
        """Initialize the appropriate LLM client."""
        try:
            if self.provider == "openai":
                if not self.api_key:
                    logger.warning("OpenAI API key not configured")
                    return None

                import openai

                return openai.OpenAI(api_key=self.api_key)

            elif self.provider == "anthropic":
                if not self.api_key:
                    logger.warning("Anthropic API key not configured")
                    return None

                import anthropic

                return anthropic.Anthropic(api_key=self.api_key)
            elif self.provider == "azure":
                if not self.api_key:
                    logger.warning("Azure API key not configured")
                    return None

                if not settings.azure_endpoint:
                    logger.warning("Azure endpoint not configured")
                    return None

                if not settings.azure_deployment:
                    logger.warning("Azure deployment not configured")
                    return None

                import openai

                return openai.AzureOpenAI(
                    api_key=self.api_key,
                    azure_endpoint=settings.azure_endpoint,
                    api_version=settings.azure_api_version,
                    azure_deployment=settings.azure_deployment,
                )

        except ImportError as e:
            logger.error(f"Failed to import {self.provider} library: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize {self.provider} client: {e}")
            return None

    def generate_headline(
        self, trends: List[TrendAnalysis], hypotheses: List[Hypothesis]
    ) -> str:
        """
        Generate a compelling headline for the retrospective report.

        Args:
            trends: List of trend analyses
            hypotheses: List of generated hypotheses

        Returns:
            Generated headline (1-2 lines)
        """
        if not self.client:
            return self._fallback_headline(trends, hypotheses)

        # Prepare context
        context = self._prepare_headline_context(trends, hypotheses)

        try:
            response = self._call_llm(
                system_prompt="You are an expert Agile coach analyzing team metrics.",
                user_prompt=(
                    "Based on the following sprint metrics analysis, generate a compelling, "
                    "concise headline (1-2 lines) that captures the most important trend or issue. "
                    "Focus on actionable insights and impact.\n\n"
                    f"{context}\n\n"
                    "Headline:"
                ),
            )

            return response.strip()

        except Exception as e:
            logger.error(f"LLM headline generation failed: {e}")
            return self._fallback_headline(trends, hypotheses)

    def enhance_hypothesis_description(
        self, hypothesis: Hypothesis, context: Dict[str, Any]
    ) -> str:
        """
        Enhance hypothesis description with LLM-generated narrative.

        Args:
            hypothesis: Hypothesis to enhance
            context: Additional context about the team/project

        Returns:
            Enhanced description
        """
        if not self.client:
            return hypothesis.description

        try:
            prompt = (
                f"Hypothesis: {hypothesis.title}\n"
                f"Current description: {hypothesis.description}\n"
                f"Evidence:\n"
            )

            for ev in hypothesis.evidence:
                prompt += f"- {ev.metric_name}: {ev.trend} ({ev.value})\n"

            if context.get("custom_context"):
                prompt += f"\nAdditional context: {context['custom_context']}\n"

            prompt += (
                "\nEnhance this hypothesis description to be more clear and actionable "
                "for a Scrum team retrospective. Keep it concise (2-3 sentences)."
            )

            response = self._call_llm(
                system_prompt="You are an expert Agile coach helping teams improve.",
                user_prompt=prompt,
            )

            return response.strip()

        except Exception as e:
            logger.error(f"LLM hypothesis enhancement failed: {e}")
            return hypothesis.description

    def generate_retro_questions(self, hypotheses: List[Hypothesis]) -> List[str]:
        """
        Generate retrospective questions based on hypotheses.

        Args:
            hypotheses: List of hypotheses

        Returns:
            List of 3 retrospective questions
        """
        if not self.client:
            return self._fallback_retro_questions(hypotheses)

        try:
            context = "\n".join(
                [
                    f"{i + 1}. {h.title}: {h.description}"
                    for i, h in enumerate(hypotheses[:3])
                ]
            )

            response = self._call_llm(
                system_prompt="You are an expert Scrum Master facilitating retrospectives.",
                user_prompt=(
                    "Based on these hypotheses about the team's recent performance:\n\n"
                    f"{context}\n\n"
                    "Generate exactly 3 powerful retrospective questions that will help the team:\n"
                    "1. Reflect on root causes\n"
                    "2. Identify concrete improvements\n"
                    "3. Commit to actionable experiments\n\n"
                    "Format: Return only the 3 questions, one per line, numbered."
                ),
            )

            # Parse questions
            questions = []
            for line in response.strip().split("\n"):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith("-")):
                    # Remove numbering
                    question = line.lstrip("0123456789.-) ")
                    if question:
                        questions.append(question)

            # Ensure we have exactly 3
            if len(questions) >= 3:
                return questions[:3]

            return self._fallback_retro_questions(hypotheses)

        except Exception as e:
            logger.error(f"LLM retro questions generation failed: {e}")
            return self._fallback_retro_questions(hypotheses)

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call the appropriate LLM API."""
        if not self.client:
            raise LLMIntegrationError("LLM client not initialized")

        try:
            if self.provider in ["openai", "azure"]:
                # Both OpenAI and Azure OpenAI use the same API
                # For Azure, the model parameter is actually the deployment name
                model_or_deployment = (
                    self.model
                    if self.provider == "openai"
                    else settings.azure_deployment
                )

                response = self.client.chat.completions.create(
                    model=model_or_deployment,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=500,
                    temperature=0.7,
                )
                return response.choices[0].message.content

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                return response.content[0].text

            else:
                raise LLMIntegrationError(f"Unsupported provider: {self.provider}")

        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise LLMIntegrationError(f"LLM call failed: {str(e)}") from e

    def _prepare_headline_context(
        self, trends: List[TrendAnalysis], hypotheses: List[Hypothesis]
    ) -> str:
        """Prepare context for headline generation."""
        context = "Key Trends:\n"

        # Top 3 significant trends
        significant_trends = [t for t in trends if t.is_significant]
        for trend in significant_trends[:3]:
            context += f"- {trend.metric_name}: {trend.trend_direction} {abs(trend.change_percent or 0):.0f}%\n"

        context += "\nTop Hypothesis: "
        if hypotheses:
            context += f"{hypotheses[0].title}\n"

        return context

    def _fallback_headline(
        self, trends: List[TrendAnalysis], hypotheses: List[Hypothesis]
    ) -> str:
        """Generate fallback headline without LLM."""
        if not hypotheses:
            return "Sprint metrics analysis: Review key trends and patterns"

        top_hypothesis = hypotheses[0]

        # Find most significant trend
        significant = [t for t in trends if t.is_significant]
        if significant:
            top_trend = max(significant, key=lambda t: abs(t.change_percent or 0))
            return (
                f"{top_trend.metric_name.replace('_', ' ').title()} "
                f"{top_trend.trend_direction} {abs(top_trend.change_percent):.0f}% - "
                f"{top_hypothesis.title}"
            )

        return f"{top_hypothesis.title} - Key insight from recent sprints"

    def _fallback_retro_questions(self, hypotheses: List[Hypothesis]) -> List[str]:
        """Generate fallback retro questions without LLM."""
        if not hypotheses:
            return [
                "What went well in the last sprint?",
                "What could we improve?",
                "What will we try differently next sprint?",
            ]

        top_hypothesis = hypotheses[0]

        return [
            f"What factors are contributing to {top_hypothesis.title.lower()}?",
            "How is this pattern affecting our team's effectiveness and well-being?",
            "What's one experiment we can run next sprint to address this issue?",
        ]


# Global LLM client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get global LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
