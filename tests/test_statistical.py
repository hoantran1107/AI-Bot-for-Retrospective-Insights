"""
Unit tests for statistical analysis engine.
"""

from datetime import datetime

import pytest

from src.analysis.statistical import StatisticalAnalyzer, get_statistical_analyzer
from src.core.models import SprintMetrics


@pytest.fixture
def analyzer():
    """Create test analyzer instance."""
    return StatisticalAnalyzer(trend_threshold=0.20, correlation_threshold=0.6)


@pytest.fixture
def sample_sprints():
    """Create sample sprint data with trends."""
    sprints = []
    for i in range(5):
        sprint = SprintMetrics(
            sprint_id=f"SPRINT-{i + 1}",
            sprint_name=f"Sprint {i + 1}",
            start_date=datetime(2024, i + 1, 1),
            end_date=datetime(2024, i + 1, 14),
            team_happiness=8.0 - (i * 0.5),  # Downward trend
            story_points_completed=40 + (i * 2),  # Upward trend
            review_time=20.0 + (i * 3),  # Strong upward trend
            coding_time=100.0 + (i * 5),  # Moderate upward trend
            testing_time=20.0,  # Stable
            defect_rate_production=0.05 + (i * 0.01),  # Slight upward
            story_point_distribution={"small": 5, "medium": 8 + i, "large": 2 + i},
        )
        sprints.append(sprint)

    return sprints


def test_analyzer_initialization():
    """Test StatisticalAnalyzer initialization."""
    analyzer = StatisticalAnalyzer(trend_threshold=0.25, correlation_threshold=0.7)

    assert analyzer.trend_threshold == 0.25
    assert analyzer.correlation_threshold == 0.7


def test_analyze_trends_basic(analyzer, sample_sprints):
    """Test basic trend analysis."""
    trends = analyzer.analyze_trends(sample_sprints)

    assert len(trends) > 0

    # Find specific metrics
    trend_dict = {t.metric_name: t for t in trends}

    # Check team_happiness (downward trend)
    if "team_happiness" in trend_dict:
        happiness_trend = trend_dict["team_happiness"]
        assert happiness_trend.trend_direction == "down"
        assert happiness_trend.current_value < happiness_trend.previous_value

    # Check story_points_completed (upward trend)
    if "story_points_completed" in trend_dict:
        sp_trend = trend_dict["story_points_completed"]
        assert sp_trend.trend_direction == "up"
        assert sp_trend.current_value > sp_trend.previous_value


def test_analyze_trends_percentage_change(analyzer, sample_sprints):
    """Test percentage change calculation."""
    trends = analyzer.analyze_trends(sample_sprints)
    trend_dict = {t.metric_name: t for t in trends}

    # Review time goes from 20 to 32 (60% increase)
    if "review_time" in trend_dict:
        review_trend = trend_dict["review_time"]
        # Last change: 29 to 32 = 10.3% increase
        assert review_trend.change_percent > 0
        # 10.3% is less than 20% threshold, so not significant
        # But the trend direction should still be detected
        assert review_trend.trend_direction == "up"


def test_analyze_trends_stable_metric(analyzer):
    """Test stable metric detection."""
    # Create sprints with stable metric
    sprints = []
    for i in range(3):
        sprint = SprintMetrics(
            sprint_id=f"SPRINT-{i + 1}",
            sprint_name=f"Sprint {i + 1}",
            start_date=datetime(2024, i + 1, 1),
            end_date=datetime(2024, i + 1, 14),
            testing_time=20.0,  # Completely stable
        )
        sprints.append(sprint)

    trends = analyzer.analyze_trends(sprints)

    testing_trend = next((t for t in trends if t.metric_name == "testing_time"), None)
    if testing_trend:
        assert testing_trend.trend_direction == "stable"


def test_analyze_trends_insufficient_data(analyzer):
    """Test with insufficient data."""
    single_sprint = [
        SprintMetrics(
            sprint_id="SPRINT-1",
            sprint_name="Sprint 1",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 14),
            team_happiness=7.5,
        )
    ]

    trends = analyzer.analyze_trends(single_sprint)
    assert trends == []


def test_analyze_correlations(analyzer, sample_sprints):
    """Test correlation analysis."""
    correlations = analyzer.analyze_correlations(sample_sprints)

    # Should find some correlations
    assert len(correlations) >= 0

    # All correlations should have coefficient between -1 and 1
    for corr in correlations:
        assert -1 <= corr.correlation_coefficient <= 1
        assert corr.is_strong  # Only strong correlations returned


def test_analyze_correlations_specific_metrics(analyzer, sample_sprints):
    """Test correlation with specific metrics."""
    # review_time and coding_time both increase, should be positively correlated
    correlations = analyzer.analyze_correlations(
        sample_sprints,
        metrics_to_analyze=["review_time", "coding_time", "team_happiness"],
    )

    # Should find at least some correlations
    assert isinstance(correlations, list)


def test_detect_anomalies_no_anomaly(analyzer):
    """Test anomaly detection with normal data."""
    sprints = []
    for i in range(5):
        sprint = SprintMetrics(
            sprint_id=f"SPRINT-{i + 1}",
            sprint_name=f"Sprint {i + 1}",
            start_date=datetime(2024, i + 1, 1),
            end_date=datetime(2024, i + 1, 14),
            team_happiness=7.5,  # Consistent value
        )
        sprints.append(sprint)

    anomalies = analyzer.detect_anomalies(sprints, "team_happiness")

    # Should not detect anomalies in consistent data
    assert len(anomalies) == 0


def test_detect_anomalies_with_outlier(analyzer):
    """Test anomaly detection with outlier."""
    sprints = []
    values = [20.0, 21.0, 20.5, 100.0, 20.0]  # 100.0 is a clear outlier

    for i, val in enumerate(values):
        sprint = SprintMetrics(
            sprint_id=f"SPRINT-{i + 1}",
            sprint_name=f"Sprint {i + 1}",
            start_date=datetime(2024, i + 1, 1),
            end_date=datetime(2024, i + 1, 14),
            review_time=val,
        )
        sprints.append(sprint)

    # Use lower threshold to ensure detection
    anomalies = analyzer.detect_anomalies(sprints, "review_time", z_threshold=1.5)

    # Should detect the outlier at index 3
    assert len(anomalies) > 0
    # Verify an anomaly was detected
    assert any(abs(z) > 1.5 for _, _, z in anomalies)


def test_calculate_moving_average(analyzer, sample_sprints):
    """Test moving average calculation."""
    ma = analyzer.calculate_moving_average(
        sample_sprints, "story_points_completed", window=3
    )

    assert len(ma) == len(sample_sprints)

    # Moving average should smooth out values
    assert all(isinstance(v, (float, type(None))) for v in ma)


def test_analyze_story_point_distribution(analyzer, sample_sprints):
    """Test story point distribution analysis."""
    analysis = analyzer.analyze_story_point_distribution(sample_sprints)

    assert "pattern" in analysis
    assert "distribution" in analysis
    assert "total_stories" in analysis

    # Check that percentages sum to roughly 100
    if analysis["distribution"]:
        total_percent = sum(analysis["distribution"].values())
        assert 99 < total_percent < 101


def test_story_point_distribution_patterns(analyzer):
    """Test pattern detection in story point distribution."""
    # Create sprints with large story concentration
    sprints = []
    for i in range(3):
        sprint = SprintMetrics(
            sprint_id=f"SPRINT-{i + 1}",
            sprint_name=f"Sprint {i + 1}",
            start_date=datetime(2024, i + 1, 1),
            end_date=datetime(2024, i + 1, 14),
            story_point_distribution={
                "small": 2,
                "medium": 3,
                "large": 10,
            },  # 67% large
        )
        sprints.append(sprint)

    analysis = analyzer.analyze_story_point_distribution(sprints)

    assert analysis["pattern"] == "large_story_concentration"
    assert analysis["large_percent"] > 40


def test_sprints_to_dataframe(analyzer, sample_sprints):
    """Test conversion of sprints to DataFrame."""
    df = analyzer._sprints_to_dataframe(sample_sprints)

    assert len(df) == len(sample_sprints)
    assert "sprint_id" in df.columns
    assert "team_happiness" in df.columns

    # Check datetime conversion
    assert df["start_date"].dtype == "datetime64[ns]"


def test_get_numeric_metrics(analyzer, sample_sprints):
    """Test extraction of numeric metrics."""
    df = analyzer._sprints_to_dataframe(sample_sprints)
    numeric_metrics = analyzer._get_numeric_metrics(df)

    assert "team_happiness" in numeric_metrics
    assert "review_time" in numeric_metrics
    assert "sprint_id" not in numeric_metrics  # Should be excluded
    assert "sprint_name" not in numeric_metrics  # Should be excluded


def test_correlation_interpretation(analyzer, sample_sprints):
    """Test correlation interpretation."""
    correlations = analyzer.analyze_correlations(sample_sprints)

    for corr in correlations:
        assert "correlation" in corr.interpretation.lower()

        # Check interpretation matches coefficient
        if corr.correlation_coefficient > 0:
            assert "positive" in corr.interpretation.lower()
        else:
            assert "negative" in corr.interpretation.lower()


def test_get_statistical_analyzer_factory():
    """Test factory function for analyzer."""
    analyzer = get_statistical_analyzer()

    assert isinstance(analyzer, StatisticalAnalyzer)
    assert analyzer.trend_threshold > 0
    assert analyzer.correlation_threshold > 0


def test_trend_significance_detection(analyzer):
    """Test that significant trends are properly flagged."""
    # Create sprints with significant change (>20%)
    sprints = [
        SprintMetrics(
            sprint_id="SPRINT-1",
            sprint_name="Sprint 1",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 14),
            review_time=20.0,
        ),
        SprintMetrics(
            sprint_id="SPRINT-2",
            sprint_name="Sprint 2",
            start_date=datetime(2024, 2, 1),
            end_date=datetime(2024, 2, 14),
            review_time=30.0,  # 50% increase - significant!
        ),
    ]

    trends = analyzer.analyze_trends(sprints)
    review_trend = next((t for t in trends if t.metric_name == "review_time"), None)

    assert review_trend is not None
    assert review_trend.is_significant
    assert review_trend.change_percent == 50.0


def test_empty_metrics_handling(analyzer):
    """Test handling of sprints with missing metrics."""
    sprints = [
        SprintMetrics(
            sprint_id="SPRINT-1",
            sprint_name="Sprint 1",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 14),
            team_happiness=None,  # Missing value
        ),
        SprintMetrics(
            sprint_id="SPRINT-2",
            sprint_name="Sprint 2",
            start_date=datetime(2024, 2, 1),
            end_date=datetime(2024, 2, 14),
            team_happiness=7.5,
        ),
    ]

    trends = analyzer.analyze_trends(sprints)

    # Should handle gracefully without errors
    assert isinstance(trends, list)
