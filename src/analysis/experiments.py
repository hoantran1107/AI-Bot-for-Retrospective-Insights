"""
Experiment suggestion engine for retrospective action items.
Maps hypotheses to concrete, timeboxed experiments.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from src.core.models import ExperimentSuggestion, Hypothesis

logger = logging.getLogger(__name__)


@dataclass
class ExperimentTemplate:
    """Template for experiment generation."""

    hypothesis_pattern: str
    title: str
    description: str
    implementation_steps: List[str]
    success_metrics: List[str]
    expected_outcome: str
    duration_sprints: int = 1


class ExperimentGenerator:
    """Generate actionable experiments from hypotheses."""

    def __init__(self):
        """Initialize experiment generator with templates."""
        self.templates = self._initialize_templates()

    def generate_experiments(
        self, hypotheses: List[Hypothesis], max_experiments: int = 3
    ) -> List[ExperimentSuggestion]:
        """
        Generate experiment suggestions from hypotheses.

        Args:
            hypotheses: List of hypotheses to address
            max_experiments: Maximum number of experiments

        Returns:
            List of experiment suggestions
        """
        logger.info(f"Generating experiments for {len(hypotheses)} hypotheses")

        experiments = []

        for idx, hypothesis in enumerate(hypotheses):
            experiment = self._generate_experiment_for_hypothesis(hypothesis, idx)
            if experiment:
                experiments.append(experiment)

        # Limit to max
        experiments = experiments[:max_experiments]

        logger.info(f"Generated {len(experiments)} experiments")
        return experiments

    def _generate_experiment_for_hypothesis(
        self, hypothesis: Hypothesis, hypothesis_index: int
    ) -> Optional[ExperimentSuggestion]:
        """Generate experiment for a specific hypothesis."""
        title_lower = hypothesis.title.lower()

        # Review bottleneck experiments
        if "review" in title_lower and "bottleneck" in title_lower:
            return self._create_review_bottleneck_experiment(
                hypothesis, hypothesis_index
            )

        # Story sizing experiments
        if "sizing" in title_lower or "slicing" in title_lower:
            return self._create_story_sizing_experiment(hypothesis, hypothesis_index)

        # Quality/defect experiments
        if (
            "quality" in title_lower
            or "defect" in title_lower
            or "testing" in title_lower
        ):
            return self._create_quality_experiment(hypothesis, hypothesis_index)

        # Team morale experiments
        if (
            "morale" in title_lower
            or "happiness" in title_lower
            or "engagement" in title_lower
        ):
            return self._create_morale_experiment(hypothesis, hypothesis_index)

        # Workflow efficiency experiments
        if "workflow" in title_lower or "efficiency" in title_lower:
            return self._create_workflow_experiment(hypothesis, hypothesis_index)

        # Generic experiment
        return self._create_generic_experiment(hypothesis, hypothesis_index)

    def _create_review_bottleneck_experiment(
        self, hypothesis: Hypothesis, index: int
    ) -> ExperimentSuggestion:
        """Create experiment for review bottleneck."""
        return ExperimentSuggestion(
            title="Implement WIP Limit for Code Review",
            description=(
                "Set a work-in-progress (WIP) limit of 2-3 items in the 'Code Review' column. "
                "Team members should prioritize reviewing existing PRs before starting new work."
            ),
            rationale=(
                f"Addressing: {hypothesis.title}. "
                "WIP limits force the team to complete reviews faster and prevent review queue buildup. "
                "This creates a pull system that balances development and review capacity."
            ),
            duration_sprints=1,
            success_metrics=[
                "average_review_time",
                "review_queue_size",
                "pr_lead_time",
                "developer_satisfaction",
            ],
            implementation_steps=[
                "Set WIP limit on review column to 2-3 items",
                "Establish team agreement: review before starting new work",
                "Assign review buddies or rotation for accountability",
                "Track review metrics daily for first week",
                "Hold mid-sprint check-in to assess progress",
            ],
            expected_outcome="Reduce average review time by 20-30% and improve flow",
            related_hypothesis_index=index,
        )

    def _create_story_sizing_experiment(
        self, hypothesis: Hypothesis, index: int
    ) -> ExperimentSuggestion:
        """Create experiment for story sizing issues."""
        return ExperimentSuggestion(
            title="Enforce Story Slicing for Large Items",
            description=(
                "For all stories estimated > 5 story points, require decomposition into "
                "smaller chunks with clear acceptance criteria and deliverable increments."
            ),
            rationale=(
                f"Addressing: {hypothesis.title}. "
                "Large stories increase uncertainty and reduce sprint completion rates. "
                "Breaking stories into smaller pieces improves flow and predictability."
            ),
            duration_sprints=1,
            success_metrics=[
                "items_out_of_sprint_percent",
                "story_point_distribution",
                "sprint_completion_rate",
                "velocity_consistency",
            ],
            implementation_steps=[
                "Review backlog and identify all stories > 5 points",
                "Hold story slicing workshop for top 5-10 stories",
                "Create slicing checklist (INVEST criteria)",
                "Enforce slicing rule during sprint planning",
                "Track % of stories that are 3 points or less",
            ],
            expected_outcome="Reduce items out of sprint by 10-15% and increase predictability",
            related_hypothesis_index=index,
        )

    def _create_quality_experiment(
        self, hypothesis: Hypothesis, index: int
    ) -> ExperimentSuggestion:
        """Create experiment for quality issues."""
        return ExperimentSuggestion(
            title="Implement Pre-Review Testing Checklist",
            description=(
                "Introduce a mandatory testing checklist that developers complete before "
                "requesting code review. Include unit tests, integration tests, and manual smoke testing."
            ),
            rationale=(
                f"Addressing: {hypothesis.title}. "
                "Many defects slip through when testing is rushed or incomplete. "
                "A checklist ensures consistent quality before code review."
            ),
            duration_sprints=1,
            success_metrics=[
                "defect_rate_production",
                "defect_rate_all",
                "bugs_found_in_testing_vs_production",
                "review_rework_rate",
            ],
            implementation_steps=[
                "Create testing checklist (unit tests, integration, manual scenarios)",
                "Add checklist to PR template",
                "Establish 'Definition of Ready' for code review",
                "Track checklist compliance for 2 weeks",
                "Review defect trends mid-sprint and end-of-sprint",
            ],
            expected_outcome="Reduce production defect rate by 20-30%",
            related_hypothesis_index=index,
        )

    def _create_morale_experiment(
        self, hypothesis: Hypothesis, index: int
    ) -> ExperimentSuggestion:
        """Create experiment for team morale."""
        return ExperimentSuggestion(
            title="Establish Weekly Team Health Check-ins",
            description=(
                "Introduce brief 15-minute weekly team health check-ins to discuss workload, "
                "blockers, and morale. Create safe space for raising concerns early."
            ),
            rationale=(
                f"Addressing: {hypothesis.title}. "
                "Declining morale often stems from unaddressed frustrations and lack of visibility. "
                "Regular check-ins create psychological safety and early intervention opportunities."
            ),
            duration_sprints=2,
            success_metrics=[
                "team_happiness",
                "team_satisfaction_survey",
                "issues_raised_and_resolved",
                "meeting_effectiveness_score",
            ],
            implementation_steps=[
                "Schedule weekly 15-min health check-in (Fridays recommended)",
                "Create simple format: highs, lows, blockers, shout-outs",
                "Rotate facilitator each week",
                "Track issues raised and follow-up actions",
                "Survey team after 2 sprints on effectiveness",
            ],
            expected_outcome="Improve team happiness score by 10-15% and address issues proactively",
            related_hypothesis_index=index,
        )

    def _create_workflow_experiment(
        self, hypothesis: Hypothesis, index: int
    ) -> ExperimentSuggestion:
        """Create experiment for workflow efficiency."""
        return ExperimentSuggestion(
            title="Implement Pairing for Complex Work",
            description=(
                "For stories estimated at 5+ points or involving critical systems, "
                "require pair programming or mob programming sessions."
            ),
            rationale=(
                f"Addressing: {hypothesis.title}. "
                "Pairing reduces rework, improves code quality, and accelerates knowledge sharing, "
                "which can offset longer individual work times."
            ),
            duration_sprints=1,
            success_metrics=[
                "coding_time",
                "review_time",
                "rework_rate",
                "knowledge_sharing_score",
            ],
            implementation_steps=[
                "Identify 3-5 complex stories for pairing",
                "Schedule pairing sessions (2-4 hours)",
                "Rotate pairs to spread knowledge",
                "Track time spent vs. solo development",
                "Gather feedback on pairing effectiveness",
            ],
            expected_outcome="Reduce overall cycle time by 15-20% through reduced rework",
            related_hypothesis_index=index,
        )

    def _create_generic_experiment(
        self, hypothesis: Hypothesis, index: int
    ) -> ExperimentSuggestion:
        """Create generic experiment when no specific template matches."""
        # Extract key metrics from hypothesis
        affected_metrics = (
            hypothesis.affected_metrics[:3] if hypothesis.affected_metrics else []
        )

        return ExperimentSuggestion(
            title=f"Targeted Improvement: {hypothesis.title}",
            description=(
                f"Focus team attention on addressing {hypothesis.title.lower()}. "
                "Hold a dedicated improvement workshop to identify root causes and design interventions."
            ),
            rationale=f"Addressing: {hypothesis.title}. {hypothesis.description[:150]}...",
            duration_sprints=1,
            success_metrics=affected_metrics
            if affected_metrics
            else ["team_effectiveness"],
            implementation_steps=[
                "Schedule 60-minute improvement workshop",
                "Use 5 Whys or fishbone diagram to find root causes",
                "Brainstorm potential solutions",
                "Vote on top 2-3 actions to try",
                "Assign owners and track progress",
            ],
            expected_outcome=f"Measurable improvement in {', '.join(affected_metrics[:2])}",
            related_hypothesis_index=index,
        )

    def _initialize_templates(self) -> List[ExperimentTemplate]:
        """Initialize experiment templates."""
        return [
            ExperimentTemplate(
                hypothesis_pattern="review_bottleneck",
                title="Set WIP Limit in Review",
                description="Limit code review queue to improve flow",
                implementation_steps=["Set WIP limit", "Track metrics"],
                success_metrics=["review_time", "pr_lead_time"],
                expected_outcome="20% reduction in review time",
                duration_sprints=1,
            ),
            # More templates can be added here
        ]


def get_experiment_generator() -> ExperimentGenerator:
    """Get experiment generator instance."""
    return ExperimentGenerator()
