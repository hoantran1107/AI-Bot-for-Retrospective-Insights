"""
Unit tests for experiment suggestion engine.
"""

import pytest

from src.analysis.experiments import ExperimentGenerator, get_experiment_generator
from src.core.models import Evidence, Hypothesis


@pytest.fixture
def generator():
    """Create experiment generator instance."""
    return ExperimentGenerator()


@pytest.fixture
def review_bottleneck_hypothesis():
    """Hypothesis about review bottleneck."""
    return Hypothesis(
        title="Review Process Bottleneck",
        description="Review time has increased significantly",
        confidence="High",
        confidence_score=0.85,
        evidence=[
            Evidence(metric_name="review_time", trend="up 50%", value="20 → 30 hours")
        ],
        potential_impact="Slower delivery",
        affected_metrics=["review_time", "cycle_time"],
    )


@pytest.fixture
def story_sizing_hypothesis():
    """Hypothesis about story sizing issues."""
    return Hypothesis(
        title="Story Sizing and Slicing Issues",
        description="Too many large stories",
        confidence="Medium",
        confidence_score=0.7,
        evidence=[
            Evidence(
                metric_name="items_out_of_sprint_percent",
                trend="up 30%",
                value="15% → 20%",
            )
        ],
        potential_impact="Reduced predictability",
        affected_metrics=["sprint_completion_rate"],
    )


@pytest.fixture
def quality_hypothesis():
    """Hypothesis about quality issues."""
    return Hypothesis(
        title="Quality Assurance Process Degradation",
        description="Defect rate increasing",
        confidence="High",
        confidence_score=0.8,
        evidence=[
            Evidence(
                metric_name="defect_rate_production",
                trend="up 100%",
                value="0.05 → 0.10",
            )
        ],
        potential_impact="Customer dissatisfaction",
        affected_metrics=["defect_rate_production"],
    )


def test_generator_initialization(generator):
    """Test ExperimentGenerator initialization."""
    assert generator is not None
    assert isinstance(generator.templates, list)


def test_generate_experiments_empty(generator):
    """Test with no hypotheses."""
    experiments = generator.generate_experiments([])
    assert isinstance(experiments, list)
    assert len(experiments) == 0


def test_generate_experiment_for_review_bottleneck(
    generator, review_bottleneck_hypothesis
):
    """Test generating experiment for review bottleneck."""
    experiments = generator.generate_experiments([review_bottleneck_hypothesis])

    assert len(experiments) == 1
    exp = experiments[0]

    assert "WIP" in exp.title or "Review" in exp.title
    assert exp.duration_sprints >= 1
    assert len(exp.success_metrics) > 0
    assert len(exp.implementation_steps) > 0
    assert exp.expected_outcome
    assert exp.related_hypothesis_index == 0


def test_generate_experiment_for_story_sizing(generator, story_sizing_hypothesis):
    """Test generating experiment for story sizing."""
    experiments = generator.generate_experiments([story_sizing_hypothesis])

    assert len(experiments) == 1
    exp = experiments[0]

    assert "Slicing" in exp.title or "Story" in exp.title
    assert exp.duration_sprints >= 1
    assert (
        "story_point_distribution" in exp.success_metrics
        or "items_out_of_sprint_percent" in exp.success_metrics
    )


def test_generate_experiment_for_quality(generator, quality_hypothesis):
    """Test generating experiment for quality issues."""
    experiments = generator.generate_experiments([quality_hypothesis])

    assert len(experiments) == 1
    exp = experiments[0]

    assert "Testing" in exp.title or "Quality" in exp.title
    assert "defect_rate" in str(exp.success_metrics).lower()


def test_generate_multiple_experiments(
    generator, review_bottleneck_hypothesis, story_sizing_hypothesis
):
    """Test generating multiple experiments."""
    hypotheses = [review_bottleneck_hypothesis, story_sizing_hypothesis]
    experiments = generator.generate_experiments(hypotheses, max_experiments=3)

    assert len(experiments) == 2
    assert experiments[0].related_hypothesis_index == 0
    assert experiments[1].related_hypothesis_index == 1


def test_max_experiments_limit(generator):
    """Test that max_experiments limit is respected."""
    hypotheses = [
        Hypothesis(
            title=f"Hypothesis {i}",
            description="Test",
            confidence="Medium",
            confidence_score=0.6,
            evidence=[],
            potential_impact="Test",
            affected_metrics=["test"],
        )
        for i in range(5)
    ]

    experiments = generator.generate_experiments(hypotheses, max_experiments=2)
    assert len(experiments) <= 2


def test_experiment_has_required_fields(generator, review_bottleneck_hypothesis):
    """Test that experiments have all required fields."""
    experiments = generator.generate_experiments([review_bottleneck_hypothesis])
    exp = experiments[0]

    assert exp.title
    assert exp.description
    assert exp.rationale
    assert exp.duration_sprints > 0
    assert len(exp.success_metrics) > 0
    assert len(exp.implementation_steps) > 0
    assert exp.expected_outcome
    assert exp.related_hypothesis_index is not None


def test_create_morale_experiment(generator):
    """Test morale experiment creation."""
    hypothesis = Hypothesis(
        title="Team Morale and Engagement Concerns",
        description="Team happiness declining",
        confidence="Medium",
        confidence_score=0.7,
        evidence=[],
        potential_impact="Reduced productivity",
        affected_metrics=["team_happiness"],
    )

    experiments = generator.generate_experiments([hypothesis])
    exp = experiments[0]

    assert "Health Check" in exp.title or "Morale" in exp.title or "Team" in exp.title
    assert "team_happiness" in exp.success_metrics


def test_create_workflow_experiment(generator):
    """Test workflow efficiency experiment creation."""
    hypothesis = Hypothesis(
        title="Workflow Efficiency Degradation",
        description="All phases taking longer",
        confidence="Medium",
        confidence_score=0.65,
        evidence=[],
        potential_impact="Longer cycle times",
        affected_metrics=["cycle_time"],
    )

    experiments = generator.generate_experiments([hypothesis])
    exp = experiments[0]

    assert exp.title
    assert len(exp.implementation_steps) >= 3


def test_generic_experiment_fallback(generator):
    """Test generic experiment creation for unmatched patterns."""
    hypothesis = Hypothesis(
        title="Unknown Pattern Issue",
        description="Some other issue",
        confidence="Low",
        confidence_score=0.5,
        evidence=[],
        potential_impact="Unknown",
        affected_metrics=["metric1", "metric2"],
    )

    experiments = generator.generate_experiments([hypothesis])

    assert len(experiments) == 1
    assert experiments[0].title
    assert len(experiments[0].implementation_steps) > 0


def test_experiment_rationale_includes_hypothesis(
    generator, review_bottleneck_hypothesis
):
    """Test that experiment rationale references the hypothesis."""
    experiments = generator.generate_experiments([review_bottleneck_hypothesis])
    exp = experiments[0]

    assert "Addressing:" in exp.rationale
    assert review_bottleneck_hypothesis.title in exp.rationale


def test_implementation_steps_are_actionable(generator, review_bottleneck_hypothesis):
    """Test that implementation steps are concrete and actionable."""
    experiments = generator.generate_experiments([review_bottleneck_hypothesis])
    exp = experiments[0]

    # Should have multiple steps
    assert len(exp.implementation_steps) >= 3

    # Each step should be a non-empty string
    for step in exp.implementation_steps:
        assert isinstance(step, str)
        assert len(step) > 10  # Meaningful length


def test_success_metrics_are_measurable(generator, story_sizing_hypothesis):
    """Test that success metrics are appropriate."""
    experiments = generator.generate_experiments([story_sizing_hypothesis])
    exp = experiments[0]

    assert len(exp.success_metrics) > 0

    # Metrics should be lowercase with underscores (standard naming)
    for metric in exp.success_metrics:
        assert isinstance(metric, str)
        assert "_" in metric or metric.islower()


def test_experiment_duration_realistic(
    generator, review_bottleneck_hypothesis, story_sizing_hypothesis
):
    """Test that experiment durations are realistic."""
    experiments = generator.generate_experiments(
        [review_bottleneck_hypothesis, story_sizing_hypothesis]
    )

    for exp in experiments:
        assert 1 <= exp.duration_sprints <= 3  # 1-3 sprints is reasonable


def test_get_experiment_generator_factory():
    """Test factory function."""
    generator = get_experiment_generator()
    assert isinstance(generator, ExperimentGenerator)


def test_multiple_hypothesis_types_together(
    generator, review_bottleneck_hypothesis, quality_hypothesis, story_sizing_hypothesis
):
    """Test handling multiple different hypothesis types."""
    hypotheses = [
        review_bottleneck_hypothesis,
        quality_hypothesis,
        story_sizing_hypothesis,
    ]

    experiments = generator.generate_experiments(hypotheses, max_experiments=3)

    assert len(experiments) == 3

    # Each should be different
    titles = [e.title for e in experiments]
    assert len(set(titles)) == 3  # All unique


def test_experiment_expected_outcome_specific(generator, quality_hypothesis):
    """Test that expected outcomes include specific targets."""
    experiments = generator.generate_experiments([quality_hypothesis])
    exp = experiments[0]

    # Should mention a percentage or specific improvement
    assert (
        "%" in exp.expected_outcome
        or "reduce" in exp.expected_outcome.lower()
        or "improve" in exp.expected_outcome.lower()
    )
