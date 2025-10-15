"""
Unit tests for hypothesis generation engine.
"""

from datetime import datetime

import pytest

from src.analysis.hypothesis import HypothesisGenerator, get_hypothesis_generator
from src.core.models import CorrelationResult, Evidence, SprintMetrics, TrendAnalysis


@pytest.fixture
def generator():
    """Create hypothesis generator instance."""
    return HypothesisGenerator()


@pytest.fixture
def sample_trends_review_bottleneck():
    """Sample trends indicating review bottleneck."""
    return [
        TrendAnalysis(
            metric_name="review_time",
            current_value=30.0,
            previous_value=20.0,
            change_percent=50.0,
            trend_direction="up",
            is_significant=True,
        ),
        TrendAnalysis(
            metric_name="team_happiness",
            current_value=6.5,
            previous_value=7.5,
            change_percent=-13.3,
            trend_direction="down",
            is_significant=False,
        ),
    ]


@pytest.fixture
def sample_correlations():
    """Sample correlation results."""
    return [
        CorrelationResult(
            metric_1="review_time",
            metric_2="defect_rate_production",
            correlation_coefficient=0.75,
            is_strong=True,
            interpretation="Strong positive correlation",
        )
    ]


@pytest.fixture
def sample_sprints_quality_issues():
    """Sample sprints with quality issues."""
    return [
        SprintMetrics(
            sprint_id="SPRINT-1",
            sprint_name="Sprint 1",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 14),
            defect_rate_production=0.05,
            bugs_prod=2,
            bugs_test=8,
            bugs_acc=0,
            bugs_dev=0,
            bugs_other=0,
        ),
        SprintMetrics(
            sprint_id="SPRINT-2",
            sprint_name="Sprint 2",
            start_date=datetime(2024, 2, 1),
            end_date=datetime(2024, 2, 14),
            defect_rate_production=0.08,
            bugs_prod=5,  # 50% of bugs in production
            bugs_test=3,
            bugs_acc=2,
            bugs_dev=0,
            bugs_other=0,
            bugs_missed_testing=3,
        ),
    ]


def test_generator_initialization(generator):
    """Test HypothesisGenerator initialization."""
    assert generator is not None
    assert isinstance(generator.templates, list)


def test_generate_hypotheses_empty_input(generator):
    """Test with no trends or correlations."""
    hypotheses = generator.generate_hypotheses(
        trends=[], correlations=[], sprints=[], max_hypotheses=3
    )

    assert isinstance(hypotheses, list)
    assert len(hypotheses) <= 3


def test_check_review_bottleneck_detected(
    generator, sample_trends_review_bottleneck, sample_correlations
):
    """Test review bottleneck detection."""
    hypothesis = generator._check_review_bottleneck(
        sample_trends_review_bottleneck, sample_correlations
    )

    assert hypothesis is not None
    assert "Review" in hypothesis.title
    assert hypothesis.confidence in ["High", "Medium", "Low"]
    assert len(hypothesis.evidence) >= 1
    assert hypothesis.confidence_score > 0


def test_check_review_bottleneck_not_detected(generator):
    """Test review bottleneck not detected when review time is stable."""
    trends = [
        TrendAnalysis(
            metric_name="review_time",
            current_value=20.0,
            previous_value=20.0,
            change_percent=0.0,
            trend_direction="stable",
            is_significant=False,
        )
    ]

    hypothesis = generator._check_review_bottleneck(trends, [])

    assert hypothesis is None


def test_check_story_sizing_issues(generator):
    """Test story sizing issues detection."""
    trends = [
        TrendAnalysis(
            metric_name="items_out_of_sprint_percent",
            current_value=25.0,
            previous_value=15.0,
            change_percent=66.7,
            trend_direction="up",
            is_significant=True,
        )
    ]

    sprints = [
        SprintMetrics(
            sprint_id="SPRINT-1",
            sprint_name="Sprint 1",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 14),
            story_point_distribution={
                "small": 2,
                "medium": 3,
                "large": 10,
            },  # 67% large
        )
    ]

    hypothesis = generator._check_story_sizing_issues(trends, sprints)

    assert hypothesis is not None
    assert "Sizing" in hypothesis.title or "Slicing" in hypothesis.title
    assert len(hypothesis.evidence) >= 2


def test_check_quality_issues(generator):
    """Test quality issues detection."""
    trends = [
        TrendAnalysis(
            metric_name="defect_rate_production",
            current_value=0.10,
            previous_value=0.05,
            change_percent=100.0,
            trend_direction="up",
            is_significant=True,
        ),
        TrendAnalysis(
            metric_name="testing_time",
            current_value=15.0,
            previous_value=20.0,
            change_percent=-25.0,
            trend_direction="down",
            is_significant=True,
        ),
    ]

    hypothesis = generator._check_quality_issues(trends, [])

    assert hypothesis is not None
    assert "Quality" in hypothesis.title
    assert len(hypothesis.evidence) >= 1


def test_check_team_morale(generator):
    """Test team morale detection."""
    trends = [
        TrendAnalysis(
            metric_name="team_happiness",
            current_value=6.0,
            previous_value=8.0,
            change_percent=-25.0,
            trend_direction="down",
            is_significant=True,
        ),
        TrendAnalysis(
            metric_name="review_time",
            current_value=30.0,
            previous_value=20.0,
            change_percent=50.0,
            trend_direction="up",
            is_significant=True,
        ),
    ]

    hypothesis = generator._check_team_morale(trends, [])

    assert hypothesis is not None
    assert "Morale" in hypothesis.title or "Engagement" in hypothesis.title
    assert hypothesis.confidence_score > 0.5


def test_check_workflow_efficiency(generator):
    """Test workflow efficiency issues detection."""
    trends = [
        TrendAnalysis(
            metric_name="coding_time",
            current_value=150.0,
            previous_value=100.0,
            change_percent=50.0,
            trend_direction="up",
            is_significant=True,
        ),
        TrendAnalysis(
            metric_name="review_time",
            current_value=40.0,
            previous_value=25.0,
            change_percent=60.0,
            trend_direction="up",
            is_significant=True,
        ),
        TrendAnalysis(
            metric_name="testing_time",
            current_value=30.0,
            previous_value=20.0,
            change_percent=50.0,
            trend_direction="up",
            is_significant=True,
        ),
    ]

    hypothesis = generator._check_workflow_efficiency(trends, [])

    assert hypothesis is not None
    assert "Workflow" in hypothesis.title or "Efficiency" in hypothesis.title
    assert len(hypothesis.evidence) >= 2  # Multiple phases


def test_check_defect_patterns(generator, sample_sprints_quality_issues):
    """Test defect pattern detection."""
    hypothesis = generator._check_defect_patterns([], sample_sprints_quality_issues)

    assert hypothesis is not None
    assert "Testing" in hypothesis.title or "Coverage" in hypothesis.title
    assert "production" in hypothesis.description.lower()


def test_generate_multiple_hypotheses(generator):
    """Test generating multiple hypotheses and ranking."""
    trends = [
        TrendAnalysis(
            metric_name="review_time",
            current_value=30.0,
            previous_value=20.0,
            change_percent=50.0,
            trend_direction="up",
            is_significant=True,
        ),
        TrendAnalysis(
            metric_name="team_happiness",
            current_value=6.0,
            previous_value=8.0,
            change_percent=-25.0,
            trend_direction="down",
            is_significant=True,
        ),
        TrendAnalysis(
            metric_name="defect_rate_production",
            current_value=0.10,
            previous_value=0.05,
            change_percent=100.0,
            trend_direction="up",
            is_significant=True,
        ),
    ]

    sprints = [
        SprintMetrics(
            sprint_id="SPRINT-1",
            sprint_name="Sprint 1",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 14),
        )
    ]

    hypotheses = generator.generate_hypotheses(
        trends=trends, correlations=[], sprints=sprints, max_hypotheses=3
    )

    assert len(hypotheses) <= 3

    # Check they're sorted by confidence
    if len(hypotheses) >= 2:
        assert hypotheses[0].confidence_score >= hypotheses[1].confidence_score


def test_hypothesis_has_required_fields(generator, sample_trends_review_bottleneck):
    """Test that generated hypothesis has all required fields."""
    hypothesis = generator._check_review_bottleneck(sample_trends_review_bottleneck, [])

    assert hypothesis is not None
    assert hypothesis.title
    assert hypothesis.description
    assert hypothesis.confidence in ["High", "Medium", "Low"]
    assert 0 <= hypothesis.confidence_score <= 1
    assert len(hypothesis.evidence) > 0
    assert hypothesis.potential_impact
    assert len(hypothesis.affected_metrics) > 0


def test_evidence_structure(generator, sample_trends_review_bottleneck):
    """Test evidence has proper structure."""
    hypothesis = generator._check_review_bottleneck(sample_trends_review_bottleneck, [])

    assert hypothesis is not None
    for evidence in hypothesis.evidence:
        assert isinstance(evidence, Evidence)
        assert evidence.metric_name
        assert evidence.trend
        assert evidence.value


def test_find_trend_helper(generator):
    """Test _find_trend helper method."""
    trends = [
        TrendAnalysis(
            metric_name="review_time",
            current_value=30.0,
            previous_value=20.0,
            change_percent=50.0,
            trend_direction="up",
            is_significant=True,
        )
    ]

    found = generator._find_trend(trends, "review_time")
    assert found is not None
    assert found.metric_name == "review_time"

    not_found = generator._find_trend(trends, "nonexistent_metric")
    assert not_found is None


def test_find_correlation_helper(generator, sample_correlations):
    """Test _find_correlation helper method."""
    found = generator._find_correlation(
        sample_correlations, "review_time", "defect_rate_production"
    )
    assert found is not None

    # Should work in reverse order too
    found_reverse = generator._find_correlation(
        sample_correlations, "defect_rate_production", "review_time"
    )
    assert found_reverse is not None


def test_score_to_level_conversion(generator):
    """Test confidence score to level conversion."""
    assert generator._score_to_level(0.9) == "High"
    assert generator._score_to_level(0.7) == "Medium"
    assert generator._score_to_level(0.3) == "Low"


def test_get_hypothesis_generator_factory():
    """Test factory function."""
    generator = get_hypothesis_generator()
    assert isinstance(generator, HypothesisGenerator)


def test_no_false_positives(generator):
    """Test that good metrics don't generate hypotheses."""
    # All metrics stable and healthy
    trends = [
        TrendAnalysis(
            metric_name="team_happiness",
            current_value=8.0,
            previous_value=8.0,
            change_percent=0.0,
            trend_direction="stable",
            is_significant=False,
        ),
        TrendAnalysis(
            metric_name="defect_rate_production",
            current_value=0.02,
            previous_value=0.02,
            change_percent=0.0,
            trend_direction="stable",
            is_significant=False,
        ),
    ]

    sprints = [
        SprintMetrics(
            sprint_id="SPRINT-1",
            sprint_name="Sprint 1",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 14),
            bugs_prod=1,
            bugs_test=9,  # Good ratio
        )
    ]

    hypotheses = generator.generate_hypotheses(trends, [], sprints)

    # Should generate few or no hypotheses for healthy metrics
    assert len(hypotheses) <= 1


def test_confidence_score_ranges(generator, sample_trends_review_bottleneck):
    """Test that confidence scores are within valid range."""
    hypotheses = generator.generate_hypotheses(
        trends=sample_trends_review_bottleneck,
        correlations=[],
        sprints=[],
        max_hypotheses=5,
    )

    for hypothesis in hypotheses:
        assert 0 <= hypothesis.confidence_score <= 1.0
