"""
Hypothesis generation engine for retrospective insights.
Uses rule-based templates and statistical evidence to generate hypotheses.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from src.core.config import settings
from src.core.models import (
    CorrelationResult,
    Evidence,
    Hypothesis,
    SprintMetrics,
    TrendAnalysis,
)

logger = logging.getLogger(__name__)


@dataclass
class HypothesisTemplate:
    """Template for hypothesis generation."""

    pattern_type: str
    title_template: str
    description_template: str
    potential_impact: str
    required_metrics: List[str]
    confidence_weight: float = 0.5


class HypothesisGenerator:
    """Generate evidence-based hypotheses from statistical analysis."""

    def __init__(self):
        """Initialize hypothesis generator with templates."""
        self.templates = self._initialize_templates()

    def generate_hypotheses(
        self,
        trends: List[TrendAnalysis],
        correlations: List[CorrelationResult],
        sprints: List[SprintMetrics],
        max_hypotheses: int = 3,
    ) -> List[Hypothesis]:
        """
        Generate top N hypotheses from analysis results.

        Args:
            trends: List of trend analyses
            correlations: List of correlation results
            sprints: Original sprint data
            max_hypotheses: Maximum number of hypotheses to return

        Returns:
            List of top hypotheses ranked by confidence
        """
        logger.info("Generating hypotheses from analysis results")

        hypotheses = []

        # Check for review bottleneck patterns
        review_hyp = self._check_review_bottleneck(trends, correlations)
        if review_hyp:
            hypotheses.append(review_hyp)

        # Check for story sizing issues
        sizing_hyp = self._check_story_sizing_issues(trends, sprints)
        if sizing_hyp:
            hypotheses.append(sizing_hyp)

        # Check for quality issues
        quality_hyp = self._check_quality_issues(trends, correlations)
        if quality_hyp:
            hypotheses.append(quality_hyp)

        # Check for team morale issues
        morale_hyp = self._check_team_morale(trends, correlations)
        if morale_hyp:
            hypotheses.append(morale_hyp)

        # Check for workflow efficiency
        workflow_hyp = self._check_workflow_efficiency(trends, correlations)
        if workflow_hyp:
            hypotheses.append(workflow_hyp)

        # Check for defect patterns
        defect_hyp = self._check_defect_patterns(trends, sprints)
        if defect_hyp:
            hypotheses.append(defect_hyp)

        # Sort by confidence score
        hypotheses.sort(key=lambda h: h.confidence_score, reverse=True)

        # Return top N
        top_hypotheses = hypotheses[:max_hypotheses]

        logger.info(f"Generated {len(top_hypotheses)} hypotheses")
        return top_hypotheses

    def _check_review_bottleneck(
        self, trends: List[TrendAnalysis], correlations: List[CorrelationResult]
    ) -> Optional[Hypothesis]:
        """Check for review process bottleneck."""
        # Find review time trend
        review_trend = self._find_trend(trends, "review_time")
        if not review_trend or review_trend.trend_direction != "up":
            return None

        # Check if review time increase is significant
        if (
            not review_trend.is_significant
            and abs(review_trend.change_percent or 0) < 15
        ):
            return None

        evidence_list = [
            Evidence(
                metric_name="review_time",
                trend=f"{review_trend.trend_direction} {abs(review_trend.change_percent):.1f}%",
                value=f"{review_trend.previous_value:.1f} → {review_trend.current_value:.1f} hours",
            )
        ]

        # Check for correlated metrics
        defect_corr = self._find_correlation(
            correlations, "review_time", "defect_rate_production"
        )
        reopen_trend = self._find_trend(trends, "items_carried_over")

        confidence_score = 0.6  # Base confidence

        if defect_corr and defect_corr.correlation_coefficient > 0:
            evidence_list.append(
                Evidence(
                    metric_name="defect_rate_production",
                    trend="correlated with review time",
                    value=f"r={defect_corr.correlation_coefficient:.2f}",
                )
            )
            confidence_score += 0.15

        if reopen_trend and reopen_trend.trend_direction == "up":
            evidence_list.append(
                Evidence(
                    metric_name="items_carried_over",
                    trend=f"up {abs(reopen_trend.change_percent or 0):.1f}%",
                    value=f"{reopen_trend.previous_value} → {reopen_trend.current_value} items",
                )
            )
            confidence_score += 0.1

        confidence_level = self._score_to_level(min(confidence_score, 1.0))

        return Hypothesis(
            title="Review Process Bottleneck",
            description=(
                f"Review time has increased by {abs(review_trend.change_percent):.1f}% over recent sprints. "
                "This suggests the code review process may be becoming a bottleneck, potentially due to "
                "insufficient reviewer capacity, large PRs, or lack of clear review standards. "
                "Prolonged review times can lead to context switching and delayed feedback loops."
            ),
            confidence=confidence_level,
            confidence_score=round(confidence_score, 2),
            evidence=evidence_list,
            potential_impact=(
                "Slower delivery cycles, increased WIP, developer frustration, and potential quality issues "
                "from rushed reviews or outdated code context."
            ),
            affected_metrics=["review_time", "cycle_time", "developer_satisfaction"],
        )

    def _check_story_sizing_issues(
        self, trends: List[TrendAnalysis], sprints: List[SprintMetrics]
    ) -> Optional[Hypothesis]:
        """Check for story sizing/slicing issues."""
        items_out_trend = self._find_trend(trends, "items_out_of_sprint_percent")

        if not items_out_trend or items_out_trend.trend_direction != "up":
            return None

        # Check story point concentration
        recent_sprint = sprints[-1] if sprints else None
        if not recent_sprint or not recent_sprint.story_point_distribution:
            return None

        dist = recent_sprint.story_point_distribution
        total = sum(dist.values())
        large_percent = (dist.get("large", 0) / total * 100) if total > 0 else 0

        if large_percent < 30:  # Not a sizing issue
            return None

        evidence_list = [
            Evidence(
                metric_name="items_out_of_sprint_percent",
                trend=f"up {abs(items_out_trend.change_percent or 0):.1f}%",
                value=f"{items_out_trend.previous_value:.1f}% → {items_out_trend.current_value:.1f}%",
            ),
            Evidence(
                metric_name="story_point_distribution",
                trend=f"{large_percent:.0f}% large stories",
                value=f"Large stories: {dist.get('large', 0)}/{total}",
            ),
        ]

        confidence_score = 0.65
        if large_percent > 40:
            confidence_score = 0.8

        confidence_level = self._score_to_level(confidence_score)

        return Hypothesis(
            title="Story Sizing and Slicing Issues",
            description=(
                f"Increasingly high percentage of items out of sprint ({items_out_trend.current_value:.0f}%) "
                f"combined with high concentration of large stories ({large_percent:.0f}%). "
                "This pattern suggests stories are not being adequately broken down, making sprint "
                "planning less predictable and increasing the risk of incomplete work."
            ),
            confidence=confidence_level,
            confidence_score=round(confidence_score, 2),
            evidence=evidence_list,
            potential_impact=(
                "Reduced sprint predictability, more carryover work, difficulty in completing sprint goals, "
                "and increased risk of large stories blocking progress."
            ),
            affected_metrics=[
                "sprint_completion_rate",
                "velocity_consistency",
                "planning_accuracy",
            ],
        )

    def _check_quality_issues(
        self, trends: List[TrendAnalysis], correlations: List[CorrelationResult]
    ) -> Optional[Hypothesis]:
        """Check for quality and defect patterns."""
        defect_trend = self._find_trend(trends, "defect_rate_production")

        if not defect_trend or defect_trend.trend_direction != "up":
            return None

        evidence_list = [
            Evidence(
                metric_name="defect_rate_production",
                trend=f"up {abs(defect_trend.change_percent or 0):.1f}%",
                value=f"{defect_trend.previous_value:.3f} → {defect_trend.current_value:.3f}",
            )
        ]

        confidence_score = 0.7

        # Check if testing time is decreasing
        testing_trend = self._find_trend(trends, "testing_time")
        if testing_trend and testing_trend.trend_direction == "down":
            evidence_list.append(
                Evidence(
                    metric_name="testing_time",
                    trend=f"down {abs(testing_trend.change_percent or 0):.1f}%",
                    value=f"{testing_trend.previous_value:.1f} → {testing_trend.current_value:.1f} hours",
                )
            )
            confidence_score += 0.15

        confidence_level = self._score_to_level(min(confidence_score, 1.0))

        return Hypothesis(
            title="Quality Assurance Process Degradation",
            description=(
                f"Production defect rate has increased by {abs(defect_trend.change_percent or 0):.1f}%. "
                "This may indicate insufficient testing coverage, rushed QA due to time pressure, "
                "gaps in test automation, or changes in complexity without corresponding test investment."
            ),
            confidence=confidence_level,
            confidence_score=round(confidence_score, 2),
            evidence=evidence_list,
            potential_impact=(
                "Increased production incidents, customer dissatisfaction, emergency fixes disrupting planned work, "
                "and erosion of customer trust."
            ),
            affected_metrics=[
                "customer_satisfaction",
                "production_stability",
                "unplanned_work",
            ],
        )

    def _check_team_morale(
        self, trends: List[TrendAnalysis], correlations: List[CorrelationResult]
    ) -> Optional[Hypothesis]:
        """Check for team morale and happiness issues."""
        happiness_trend = self._find_trend(trends, "team_happiness")

        if not happiness_trend or happiness_trend.trend_direction != "down":
            return None

        if abs(happiness_trend.change_percent or 0) < 10:
            return None

        evidence_list = [
            Evidence(
                metric_name="team_happiness",
                trend=f"down {abs(happiness_trend.change_percent or 0):.1f}%",
                value=f"{happiness_trend.previous_value:.1f} → {happiness_trend.current_value:.1f}",
            )
        ]

        confidence_score = 0.65

        # Check for correlated stress indicators
        review_trend = self._find_trend(trends, "review_time")
        items_out_trend = self._find_trend(trends, "items_out_of_sprint_percent")

        if review_trend and review_trend.trend_direction == "up":
            evidence_list.append(
                Evidence(
                    metric_name="review_time",
                    trend="increasing workload indicator",
                    value=f"up {abs(review_trend.change_percent or 0):.1f}%",
                )
            )
            confidence_score += 0.1

        if items_out_trend and items_out_trend.trend_direction == "up":
            evidence_list.append(
                Evidence(
                    metric_name="items_out_of_sprint_percent",
                    trend="increased pressure/uncertainty",
                    value=f"up {abs(items_out_trend.change_percent or 0):.1f}%",
                )
            )
            confidence_score += 0.1

        confidence_level = self._score_to_level(min(confidence_score, 1.0))

        return Hypothesis(
            title="Team Morale and Engagement Concerns",
            description=(
                f"Team happiness has declined by {abs(happiness_trend.change_percent or 0):.1f}%. "
                "This may be correlated with increased workload, process bottlenecks, or external pressures. "
                "Sustained low morale can lead to decreased productivity, quality issues, and attrition."
            ),
            confidence=confidence_level,
            confidence_score=round(confidence_score, 2),
            evidence=evidence_list,
            potential_impact=(
                "Reduced productivity, increased turnover risk, lower code quality, decreased collaboration, "
                "and potential team dysfunction."
            ),
            affected_metrics=[
                "retention",
                "productivity",
                "quality",
                "collaboration_health",
            ],
        )

    def _check_workflow_efficiency(
        self, trends: List[TrendAnalysis], correlations: List[CorrelationResult]
    ) -> Optional[Hypothesis]:
        """Check for overall workflow efficiency issues."""
        coding_trend = self._find_trend(trends, "coding_time")
        review_trend = self._find_trend(trends, "review_time")
        testing_trend = self._find_trend(trends, "testing_time")

        # All phases increasing suggests workflow inefficiency
        increasing_phases = []
        if (
            coding_trend
            and coding_trend.trend_direction == "up"
            and coding_trend.is_significant
        ):
            increasing_phases.append(("coding", coding_trend))
        if (
            review_trend
            and review_trend.trend_direction == "up"
            and review_trend.is_significant
        ):
            increasing_phases.append(("review", review_trend))
        if (
            testing_trend
            and testing_trend.trend_direction == "up"
            and testing_trend.is_significant
        ):
            increasing_phases.append(("testing", testing_trend))

        if len(increasing_phases) < 2:
            return None

        evidence_list = []
        for phase_name, trend in increasing_phases:
            evidence_list.append(
                Evidence(
                    metric_name=f"{phase_name}_time",
                    trend=f"up {abs(trend.change_percent or 0):.1f}%",
                    value=f"{trend.previous_value:.1f} → {trend.current_value:.1f} hours",
                )
            )

        confidence_score = 0.6 + (len(increasing_phases) * 0.1)
        confidence_level = self._score_to_level(min(confidence_score, 1.0))

        return Hypothesis(
            title="Workflow Efficiency Degradation",
            description=(
                f"Multiple workflow phases show increasing time: {', '.join(p[0] for p in increasing_phases)}. "
                "This systematic increase across phases suggests broader workflow issues such as increased complexity, "
                "inadequate tooling, process inefficiencies, or growing technical debt."
            ),
            confidence=confidence_level,
            confidence_score=round(confidence_score, 2),
            evidence=evidence_list,
            potential_impact=(
                "Longer cycle times, reduced throughput, missed deadlines, and decreased team capacity for new work."
            ),
            affected_metrics=[
                "cycle_time",
                "throughput",
                "lead_time",
                "delivery_predictability",
            ],
        )

    def _check_defect_patterns(
        self, trends: List[TrendAnalysis], sprints: List[SprintMetrics]
    ) -> Optional[Hypothesis]:
        """Check for specific defect patterns by environment or root cause."""
        # Look at recent sprint for defect distribution
        if not sprints:
            return None

        recent_sprint = sprints[-1]

        # Check bug environment distribution
        prod_bugs = recent_sprint.bugs_prod or 0
        test_bugs = recent_sprint.bugs_test or 0

        total_bugs = (
            prod_bugs
            + (recent_sprint.bugs_acc or 0)
            + test_bugs
            + (recent_sprint.bugs_dev or 0)
            + (recent_sprint.bugs_other or 0)
        )

        if total_bugs == 0:
            return None

        prod_percent = (prod_bugs / total_bugs) * 100

        # If high % of bugs in production, it's a testing gap
        if prod_percent > 40 and prod_bugs >= 3:
            evidence_list = [
                Evidence(
                    metric_name="bugs_prod",
                    trend=f"{prod_percent:.0f}% of bugs found in production",
                    value=f"{prod_bugs}/{total_bugs} bugs",
                )
            ]

            # Check root causes if available
            missed_testing = recent_sprint.bugs_missed_testing or 0
            if missed_testing > 0:
                evidence_list.append(
                    Evidence(
                        metric_name="bugs_missed_testing",
                        trend="testing gaps identified",
                        value=f"{missed_testing} bugs missed during testing",
                    )
                )

            return Hypothesis(
                title="Testing Coverage Gaps",
                description=(
                    f"High proportion ({prod_percent:.0f}%) of bugs are being found in production rather than "
                    "during development or QA phases. This indicates potential gaps in test coverage, "
                    "inadequate test environments, or insufficient testing rigor."
                ),
                confidence="Medium",
                confidence_score=0.7,
                evidence=evidence_list,
                potential_impact=(
                    "Customer-facing defects, production incidents, emergency fixes, and damaged reputation."
                ),
                affected_metrics=[
                    "production_quality",
                    "customer_satisfaction",
                    "test_effectiveness",
                ],
            )

        return None

    def _find_trend(
        self, trends: List[TrendAnalysis], metric_name: str
    ) -> Optional[TrendAnalysis]:
        """Find trend for specific metric."""
        return next((t for t in trends if t.metric_name == metric_name), None)

    def _find_correlation(
        self, correlations: List[CorrelationResult], metric1: str, metric2: str
    ) -> Optional[CorrelationResult]:
        """Find correlation between two metrics."""
        return next(
            (
                c
                for c in correlations
                if (c.metric_1 == metric1 and c.metric_2 == metric2)
                or (c.metric_1 == metric2 and c.metric_2 == metric1)
            ),
            None,
        )

    def _score_to_level(self, score: float) -> str:
        """Convert confidence score to level."""
        if score >= settings.confidence_high_threshold:
            return "High"
        elif score >= settings.confidence_medium_threshold:
            return "Medium"
        else:
            return "Low"

    def _initialize_templates(self) -> List[HypothesisTemplate]:
        """Initialize hypothesis templates."""
        # Placeholder for future template-based generation
        return []


def get_hypothesis_generator() -> HypothesisGenerator:
    """Get hypothesis generator instance."""
    return HypothesisGenerator()
