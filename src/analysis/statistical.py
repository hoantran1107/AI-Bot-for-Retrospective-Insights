"""
Statistical analysis engine for team metrics.
Performs trend analysis, correlation analysis, and pattern recognition.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from src.core.config import settings
from src.core.models import CorrelationResult, SprintMetrics, TrendAnalysis

logger = logging.getLogger(__name__)


@dataclass
class TrendResult:
    """Internal result of trend calculation."""

    metric_name: str
    values: List[float]
    current_value: Optional[float]
    previous_value: Optional[float]
    change_percent: Optional[float]
    mean: float
    std: float
    z_score: Optional[float]


class StatisticalAnalyzer:
    """Statistical analysis engine for retrospective insights."""

    def __init__(
        self,
        trend_threshold: float = 0.20,
        correlation_threshold: float = 0.6,
        significance_level: float = 0.05,
    ):
        """
        Initialize statistical analyzer.

        Args:
            trend_threshold: Percentage change considered significant (0.20 = 20%)
            correlation_threshold: Correlation coefficient threshold for "strong"
            significance_level: P-value threshold for statistical significance
        """
        self.trend_threshold = trend_threshold
        self.correlation_threshold = correlation_threshold
        self.significance_level = significance_level

    def analyze_trends(
        self,
        sprints: List[SprintMetrics],
        metrics_to_analyze: Optional[List[str]] = None,
    ) -> List[TrendAnalysis]:
        """
        Analyze month-over-month trends for metrics.

        Args:
            sprints: List of sprint metrics (ordered chronologically)
            metrics_to_analyze: Optional list of specific metrics to analyze

        Returns:
            List of TrendAnalysis objects
        """
        if len(sprints) < 2:
            logger.warning("Need at least 2 sprints for trend analysis")
            return []

        # Convert to DataFrame for easier manipulation
        df = self._sprints_to_dataframe(sprints)

        if metrics_to_analyze is None:
            # Analyze all numeric metrics
            metrics_to_analyze = self._get_numeric_metrics(df)

        trends = []
        for metric in metrics_to_analyze:
            if metric not in df.columns:
                continue

            trend = self._calculate_trend(df, metric)
            if trend:
                trends.append(trend)

        logger.info(f"Analyzed trends for {len(trends)} metrics")
        return trends

    def _calculate_trend(
        self, df: pd.DataFrame, metric_name: str
    ) -> Optional[TrendAnalysis]:
        """Calculate trend for a single metric."""
        values = df[metric_name].dropna()

        if len(values) < 2:
            return None

        current_value = float(values.iloc[-1])
        previous_value = float(values.iloc[-2])

        # Calculate percentage change
        if previous_value != 0:
            change_percent = ((current_value - previous_value) / previous_value) * 100
        else:
            change_percent = 0.0

        # Determine trend direction
        if abs(change_percent) < 1.0:  # Less than 1% change
            trend_direction = "stable"
        elif change_percent > 0:
            trend_direction = "up"
        else:
            trend_direction = "down"

        # Check if change is significant (exceeds threshold)
        is_significant = abs(change_percent / 100) >= self.trend_threshold

        # Calculate z-score for anomaly detection
        mean_val = float(values.mean())
        std_val = float(values.std())
        z_score = None

        if std_val > 0:
            z_score = (current_value - mean_val) / std_val

        # Determine statistical significance if applicable
        significance_level = None
        if len(values) >= 3:
            # Simple trend test using correlation with time
            time_series = np.arange(len(values))
            correlation, p_value = stats.pearsonr(time_series, values)

            if p_value < 0.01:
                significance_level = "p < 0.01"
            elif p_value < 0.05:
                significance_level = "p < 0.05"

        return TrendAnalysis(
            metric_name=metric_name,
            current_value=current_value,
            previous_value=previous_value,
            change_percent=round(change_percent, 2),
            trend_direction=trend_direction,
            is_significant=is_significant,
            significance_level=significance_level,
        )

    def analyze_correlations(
        self,
        sprints: List[SprintMetrics],
        metrics_to_analyze: Optional[List[str]] = None,
    ) -> List[CorrelationResult]:
        """
        Analyze correlations between metrics.

        Args:
            sprints: List of sprint metrics
            metrics_to_analyze: Optional list of specific metrics

        Returns:
            List of CorrelationResult objects for strong correlations
        """
        if len(sprints) < 3:
            logger.warning("Need at least 3 sprints for correlation analysis")
            return []

        df = self._sprints_to_dataframe(sprints)

        if metrics_to_analyze is None:
            metrics_to_analyze = self._get_numeric_metrics(df)

        # Calculate correlation matrix
        correlations = []

        for i, metric1 in enumerate(metrics_to_analyze):
            if metric1 not in df.columns:
                continue

            for metric2 in metrics_to_analyze[i + 1 :]:
                if metric2 not in df.columns:
                    continue

                corr_result = self._calculate_correlation(df, metric1, metric2)
                if corr_result and corr_result.is_strong:
                    correlations.append(corr_result)

        # Sort by absolute correlation strength
        correlations.sort(key=lambda x: abs(x.correlation_coefficient), reverse=True)

        logger.info(f"Found {len(correlations)} strong correlations")
        return correlations

    def _calculate_correlation(
        self, df: pd.DataFrame, metric1: str, metric2: str
    ) -> Optional[CorrelationResult]:
        """Calculate correlation between two metrics."""
        # Get non-null values for both metrics
        data = df[[metric1, metric2]].dropna()

        if len(data) < 3:
            return None

        # Check for constant arrays (no variance)
        if data[metric1].std() == 0 or data[metric2].std() == 0:
            return None

        # Calculate Pearson correlation
        correlation, p_value = stats.pearsonr(data[metric1], data[metric2])

        # Check for NaN (shouldn't happen after std check, but be safe)
        if np.isnan(correlation):
            return None

        # Check if correlation is strong
        is_strong = abs(correlation) >= self.correlation_threshold

        # Interpret correlation
        if abs(correlation) < 0.3:
            strength = "weak"
        elif abs(correlation) < 0.6:
            strength = "moderate"
        else:
            strength = "strong"

        direction = "positive" if correlation > 0 else "negative"

        interpretation = (
            f"{strength.capitalize()} {direction} correlation (r={correlation:.2f})"
        )

        if p_value < 0.05:
            interpretation += " (statistically significant)"

        return CorrelationResult(
            metric_1=metric1,
            metric_2=metric2,
            correlation_coefficient=round(correlation, 3),
            is_strong=is_strong,
            interpretation=interpretation,
        )

    def detect_anomalies(
        self, sprints: List[SprintMetrics], metric_name: str, z_threshold: float = 2.0
    ) -> List[Tuple[int, float, float]]:
        """
        Detect anomalies in a metric using Z-score method.

        Args:
            sprints: List of sprint metrics
            metric_name: Name of metric to check
            z_threshold: Z-score threshold for anomaly (default 2.0)

        Returns:
            List of tuples (sprint_index, value, z_score) for anomalies
        """
        df = self._sprints_to_dataframe(sprints)

        if metric_name not in df.columns:
            return []

        values = df[metric_name].dropna()

        if len(values) < 3:
            return []

        mean = values.mean()
        std = values.std()

        if std == 0:
            return []

        anomalies = []
        for idx, value in enumerate(values):
            z_score = (value - mean) / std
            if abs(z_score) >= z_threshold:
                anomalies.append((idx, float(value), float(z_score)))

        return anomalies

    def calculate_moving_average(
        self, sprints: List[SprintMetrics], metric_name: str, window: int = 3
    ) -> List[Optional[float]]:
        """
        Calculate moving average for a metric.

        Args:
            sprints: List of sprint metrics
            metric_name: Name of metric
            window: Window size for moving average

        Returns:
            List of moving average values
        """
        df = self._sprints_to_dataframe(sprints)

        if metric_name not in df.columns:
            return []

        values = df[metric_name]
        ma = values.rolling(window=window, min_periods=1).mean()

        return [float(v) if pd.notna(v) else None for v in ma]

    def analyze_story_point_distribution(
        self, sprints: List[SprintMetrics]
    ) -> Dict[str, Any]:
        """
        Analyze patterns in story point distribution.

        Args:
            sprints: List of sprint metrics

        Returns:
            Dictionary with distribution analysis
        """
        distributions = []

        for sprint in sprints:
            if sprint.story_point_distribution:
                distributions.append(sprint.story_point_distribution)

        if not distributions:
            return {"pattern": "No distribution data available"}

        # Aggregate across all sprints
        total_counts = {}
        for dist in distributions:
            for size, count in dist.items():
                total_counts[size] = total_counts.get(size, 0) + count

        total = sum(total_counts.values())
        percentages = {k: (v / total) * 100 for k, v in total_counts.items()}

        # Identify patterns
        large_percent = percentages.get("large", 0)
        small_percent = percentages.get("small", 0)

        pattern = "balanced"
        if large_percent > 40:
            pattern = "large_story_concentration"
        elif small_percent > 60:
            pattern = "small_story_concentration"

        return {
            "pattern": pattern,
            "distribution": percentages,
            "total_stories": total,
            "large_percent": large_percent,
        }

    def _sprints_to_dataframe(self, sprints: List[SprintMetrics]) -> pd.DataFrame:
        """Convert list of SprintMetrics to pandas DataFrame."""
        data = []
        for sprint in sprints:
            data.append(sprint.model_dump())

        df = pd.DataFrame(data)

        # Convert datetime columns
        if "start_date" in df.columns:
            df["start_date"] = pd.to_datetime(df["start_date"])
        if "end_date" in df.columns:
            df["end_date"] = pd.to_datetime(df["end_date"])

        return df

    def _get_numeric_metrics(self, df: pd.DataFrame) -> List[str]:
        """Get list of numeric metric column names."""
        # Exclude non-metric columns
        exclude = [
            "sprint_id",
            "sprint_name",
            "start_date",
            "end_date",
            "story_point_distribution",
        ]

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        return [col for col in numeric_cols if col not in exclude]


# Global analyzer instance
def get_statistical_analyzer() -> StatisticalAnalyzer:
    """Get statistical analyzer with configured thresholds."""
    return StatisticalAnalyzer(
        trend_threshold=settings.trend_threshold,
        correlation_threshold=settings.correlation_threshold,
    )
