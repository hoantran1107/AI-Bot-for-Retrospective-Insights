"""
Chart generation using Plotly for interactive visualizations.
"""

import logging
from typing import List, Optional

import plotly.graph_objects as go

from src.core.models import ChartData, CorrelationResult, SprintMetrics, TrendAnalysis

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generate interactive charts for retrospective dashboard."""

    def __init__(self):
        """Initialize chart generator."""
        self.default_height = 400
        self.default_width = 800
        self.color_scheme = {
            "primary": "#3B82F6",
            "success": "#10B981",
            "warning": "#F59E0B",
            "danger": "#EF4444",
            "secondary": "#6B7280",
        }

    def generate_all_charts(
        self,
        sprints: List[SprintMetrics],
        trends: List[TrendAnalysis],
        correlations: List[CorrelationResult],
    ) -> List[ChartData]:
        """
        Generate all charts for the retrospective report.

        Args:
            sprints: List of sprint metrics
            trends: List of trend analyses
            correlations: List of correlation results

        Returns:
            List of ChartData objects
        """
        logger.info("Generating all charts for retrospective")

        charts = []

        # Trend line charts
        charts.append(self.create_happiness_trend_chart(sprints))
        charts.append(self.create_time_metrics_chart(sprints))
        charts.append(self.create_defect_rate_chart(sprints))

        # Distribution charts
        if sprints and sprints[-1].story_point_distribution:
            charts.append(self.create_story_point_distribution_chart(sprints))

        charts.append(self.create_bugs_by_environment_chart(sprints))

        # Correlation heatmap
        if correlations:
            charts.append(self.create_correlation_heatmap(correlations))

        logger.info(f"Generated {len(charts)} charts")
        return charts

    def create_happiness_trend_chart(self, sprints: List[SprintMetrics]) -> ChartData:
        """Create team happiness trend chart."""
        sprint_names = [s.sprint_name for s in sprints]
        happiness_values = [
            s.team_happiness for s in sprints if s.team_happiness is not None
        ]

        if not happiness_values:
            happiness_values = [None] * len(sprints)

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=sprint_names,
                y=happiness_values,
                mode="lines+markers",
                name="Team Happiness",
                line=dict(color=self.color_scheme["primary"], width=3),
                marker=dict(size=10),
            )
        )

        # Add target line at 7.0
        fig.add_hline(
            y=7.0,
            line_dash="dash",
            line_color=self.color_scheme["success"],
            annotation_text="Target",
            annotation_position="right",
        )

        fig.update_layout(
            title="Team Happiness Trend",
            xaxis_title="Sprint",
            yaxis_title="Happiness Score (0-10)",
            yaxis=dict(range=[0, 10]),
            hovermode="x unified",
        )

        return ChartData(
            chart_id="happiness_trend",
            chart_type="line",
            title="Team Happiness Trend",
            data=fig.to_dict(),
            annotations=self._detect_chart_annotations(happiness_values, "happiness"),
        )

    def create_time_metrics_chart(self, sprints: List[SprintMetrics]) -> ChartData:
        """Create time metrics (coding, review, testing) trend chart."""
        sprint_names = [s.sprint_name for s in sprints]

        fig = go.Figure()

        # Coding time
        coding_times = [s.coding_time for s in sprints if s.coding_time is not None]
        if coding_times:
            fig.add_trace(
                go.Scatter(
                    x=sprint_names[: len(coding_times)],
                    y=coding_times,
                    mode="lines+markers",
                    name="Coding Time",
                    line=dict(color=self.color_scheme["primary"]),
                )
            )

        # Review time
        review_times = [s.review_time for s in sprints if s.review_time is not None]
        if review_times:
            fig.add_trace(
                go.Scatter(
                    x=sprint_names[: len(review_times)],
                    y=review_times,
                    mode="lines+markers",
                    name="Review Time",
                    line=dict(color=self.color_scheme["warning"]),
                )
            )

        # Testing time
        testing_times = [s.testing_time for s in sprints if s.testing_time is not None]
        if testing_times:
            fig.add_trace(
                go.Scatter(
                    x=sprint_names[: len(testing_times)],
                    y=testing_times,
                    mode="lines+markers",
                    name="Testing Time",
                    line=dict(color=self.color_scheme["success"]),
                )
            )

        fig.update_layout(
            title="Workflow Time Metrics",
            xaxis_title="Sprint",
            yaxis_title="Time (hours)",
            hovermode="x unified",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )

        return ChartData(
            chart_id="time_metrics",
            chart_type="line",
            title="Workflow Time Metrics",
            data=fig.to_dict(),
        )

    def create_defect_rate_chart(self, sprints: List[SprintMetrics]) -> ChartData:
        """Create defect rate trend chart."""
        sprint_names = [s.sprint_name for s in sprints]

        prod_defect_rates = [
            s.defect_rate_production * 100
            if s.defect_rate_production is not None
            else None
            for s in sprints
        ]

        all_defect_rates = [
            s.defect_rate_all * 100 if s.defect_rate_all is not None else None
            for s in sprints
        ]

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=sprint_names,
                y=prod_defect_rates,
                mode="lines+markers",
                name="Production Defect Rate",
                line=dict(color=self.color_scheme["danger"], width=3),
                marker=dict(size=10),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=sprint_names,
                y=all_defect_rates,
                mode="lines+markers",
                name="All Defect Rate",
                line=dict(color=self.color_scheme["secondary"], width=2, dash="dash"),
                marker=dict(size=8),
            )
        )

        fig.update_layout(
            title="Defect Rate Trends",
            xaxis_title="Sprint",
            yaxis_title="Defect Rate (%)",
            hovermode="x unified",
        )

        return ChartData(
            chart_id="defect_rates",
            chart_type="line",
            title="Defect Rate Trends",
            data=fig.to_dict(),
            annotations=self._detect_chart_annotations(prod_defect_rates, "defects"),
        )

    def create_story_point_distribution_chart(
        self, sprints: List[SprintMetrics]
    ) -> ChartData:
        """Create story point distribution bar chart."""
        # Use latest sprint for distribution
        latest_sprint = sprints[-1]
        dist = latest_sprint.story_point_distribution

        if not dist:
            return self._create_empty_chart(
                "story_point_dist", "Story Point Distribution"
            )

        sizes = list(dist.keys())
        counts = list(dist.values())

        fig = go.Figure(
            data=[
                go.Bar(
                    x=sizes,
                    y=counts,
                    marker_color=[
                        self.color_scheme["success"],
                        self.color_scheme["primary"],
                        self.color_scheme["warning"],
                    ],
                    text=counts,
                    textposition="auto",
                )
            ]
        )

        fig.update_layout(
            title=f"Story Point Distribution - {latest_sprint.sprint_name}",
            xaxis_title="Story Size",
            yaxis_title="Count",
            showlegend=False,
        )

        return ChartData(
            chart_id="story_point_dist",
            chart_type="bar",
            title="Story Point Distribution",
            data=fig.to_dict(),
        )

    def create_bugs_by_environment_chart(
        self, sprints: List[SprintMetrics]
    ) -> ChartData:
        """Create bugs by environment stacked bar chart."""
        sprint_names = [s.sprint_name for s in sprints]

        environments = ["PROD", "ACC", "TEST", "DEV", "OTHER"]
        bug_data = {
            "PROD": [s.bugs_prod or 0 for s in sprints],
            "ACC": [s.bugs_acc or 0 for s in sprints],
            "TEST": [s.bugs_test or 0 for s in sprints],
            "DEV": [s.bugs_dev or 0 for s in sprints],
            "OTHER": [s.bugs_other or 0 for s in sprints],
        }

        fig = go.Figure()

        colors = {
            "PROD": self.color_scheme["danger"],
            "ACC": self.color_scheme["warning"],
            "TEST": self.color_scheme["primary"],
            "DEV": self.color_scheme["success"],
            "OTHER": self.color_scheme["secondary"],
        }

        for env in environments:
            fig.add_trace(
                go.Bar(
                    name=env, x=sprint_names, y=bug_data[env], marker_color=colors[env]
                )
            )

        fig.update_layout(
            title="Bugs by Environment",
            xaxis_title="Sprint",
            yaxis_title="Bug Count",
            barmode="stack",
            hovermode="x unified",
        )

        return ChartData(
            chart_id="bugs_by_env",
            chart_type="bar",
            title="Bugs by Environment",
            data=fig.to_dict(),
        )

    def create_correlation_heatmap(
        self, correlations: List[CorrelationResult]
    ) -> ChartData:
        """Create correlation heatmap."""
        # Extract unique metrics
        metrics = set()
        for corr in correlations:
            metrics.add(corr.metric_1)
            metrics.add(corr.metric_2)

        metrics_list = sorted(list(metrics))
        n = len(metrics_list)

        # Create correlation matrix
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]

        # Diagonal is 1.0
        for i in range(n):
            matrix[i][i] = 1.0

        # Fill in correlations
        for corr in correlations:
            i = metrics_list.index(corr.metric_1)
            j = metrics_list.index(corr.metric_2)
            matrix[i][j] = corr.correlation_coefficient
            matrix[j][i] = corr.correlation_coefficient

        fig = go.Figure(
            data=go.Heatmap(
                z=matrix,
                x=metrics_list,
                y=metrics_list,
                colorscale="RdBu_r",
                zmid=0,
                zmin=-1,
                zmax=1,
                text=[[f"{val:.2f}" for val in row] for row in matrix],
                texttemplate="%{text}",
                textfont={"size": 10},
                colorbar=dict(title="Correlation"),
            )
        )

        fig.update_layout(
            title="Metric Correlations", xaxis_title="", yaxis_title="", height=500
        )

        return ChartData(
            chart_id="correlation_heatmap",
            chart_type="heatmap",
            title="Metric Correlations",
            data=fig.to_dict(),
        )

    def _detect_chart_annotations(
        self, values: List[Optional[float]], metric_type: str
    ) -> List[str]:
        """Detect noteworthy patterns in chart data."""
        annotations = []

        if not values or len(values) < 2:
            return annotations

        # Clean values
        clean_values = [v for v in values if v is not None]

        if len(clean_values) < 2:
            return annotations

        # Check for trend
        first_val = clean_values[0]
        last_val = clean_values[-1]

        if last_val > first_val * 1.2:
            annotations.append(f"Increasing trend: {first_val:.1f} → {last_val:.1f}")
        elif last_val < first_val * 0.8:
            annotations.append(f"Decreasing trend: {first_val:.1f} → {last_val:.1f}")

        return annotations

    def _create_empty_chart(self, chart_id: str, title: str) -> ChartData:
        """Create empty placeholder chart."""
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20, color="gray"),
        )

        fig.update_layout(
            title=title, xaxis=dict(visible=False), yaxis=dict(visible=False)
        )

        return ChartData(
            chart_id=chart_id, chart_type="line", title=title, data=fig.to_dict()
        )


def get_chart_generator() -> ChartGenerator:
    """Get chart generator instance."""
    return ChartGenerator()
