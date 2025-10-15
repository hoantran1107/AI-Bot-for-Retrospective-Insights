"""
Report assembler to create complete retrospective reports.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from src.analysis.experiments import ExperimentGenerator, get_experiment_generator
from src.analysis.hypothesis import HypothesisGenerator, get_hypothesis_generator
from src.analysis.llm_integration import LLMClient, get_llm_client
from src.analysis.statistical import StatisticalAnalyzer, get_statistical_analyzer
from src.charts.generators import ChartGenerator, get_chart_generator
from src.core.models import FacilitationGuide, RetrospectiveReport, SprintMetrics

logger = logging.getLogger(__name__)


class ReportAssembler:
    """Assemble complete retrospective insight reports."""

    def __init__(
        self,
        statistical_analyzer: Optional[StatisticalAnalyzer] = None,
        hypothesis_generator: Optional[HypothesisGenerator] = None,
        experiment_generator: Optional[ExperimentGenerator] = None,
        llm_client: Optional[LLMClient] = None,
        chart_generator: Optional[ChartGenerator] = None,
    ):
        """
        Initialize report assembler with analysis components.

        Args:
            statistical_analyzer: Statistical analysis engine
            hypothesis_generator: Hypothesis generation engine
            experiment_generator: Experiment suggestion engine
            llm_client: LLM integration client
            chart_generator: Chart generation engine
        """
        self.statistical_analyzer = statistical_analyzer or get_statistical_analyzer()
        self.hypothesis_generator = hypothesis_generator or get_hypothesis_generator()
        self.experiment_generator = experiment_generator or get_experiment_generator()
        self.llm_client = llm_client or get_llm_client()
        self.chart_generator = chart_generator or get_chart_generator()

    def generate_report(
        self,
        sprints: List[SprintMetrics],
        custom_context: Optional[str] = None,
        focus_metrics: Optional[List[str]] = None,
    ) -> RetrospectiveReport:
        """
        Generate complete retrospective insight report.

        Args:
            sprints: List of sprint metrics (chronologically ordered)
            custom_context: Optional additional context for LLM
            focus_metrics: Optional list of metrics to focus on

        Returns:
            Complete RetrospectiveReport
        """
        logger.info(f"Generating retrospective report for {len(sprints)} sprints")
        start_time = datetime.utcnow()

        # Step 1: Statistical Analysis
        logger.info("Step 1: Running statistical analysis")
        trends = self.statistical_analyzer.analyze_trends(sprints, focus_metrics)
        correlations = self.statistical_analyzer.analyze_correlations(
            sprints, focus_metrics
        )

        logger.info(f"Found {len(trends)} trends and {len(correlations)} correlations")

        # Step 2: Generate Hypotheses
        logger.info("Step 2: Generating hypotheses")
        hypotheses = self.hypothesis_generator.generate_hypotheses(
            trends=trends, correlations=correlations, sprints=sprints, max_hypotheses=3
        )

        logger.info(f"Generated {len(hypotheses)} hypotheses")

        # Step 3: Generate Experiments
        logger.info("Step 3: Generating experiment suggestions")
        experiments = self.experiment_generator.generate_experiments(
            hypotheses=hypotheses, max_experiments=3
        )

        logger.info(f"Generated {len(experiments)} experiments")

        # Step 4: Generate Charts
        logger.info("Step 4: Generating charts")
        charts = self.chart_generator.generate_all_charts(
            sprints=sprints, trends=trends, correlations=correlations
        )

        logger.info(f"Generated {len(charts)} charts")

        # Step 5: Generate Headline with LLM
        logger.info("Step 5: Generating headline")
        headline = self.llm_client.generate_headline(trends, hypotheses)

        # Step 6: Generate Facilitation Notes
        logger.info("Step 6: Generating facilitation notes")
        retro_questions = self.llm_client.generate_retro_questions(hypotheses)
        facilitation_notes = self._create_facilitation_notes(
            hypotheses, retro_questions
        )

        # Step 7: Determine Overall Confidence
        overall_confidence = self._calculate_overall_confidence(hypotheses)

        # Step 8: Create Sprint Period String
        sprint_period = self._format_sprint_period(sprints)

        # Create summary
        summary = f"Analysis of {len(sprints)} sprints ({sprint_period})"

        # Create report
        report = RetrospectiveReport(
            report_id=f"RPT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
            headline=headline,
            summary=summary,
            sprint_period=sprint_period,
            generated_at=datetime.utcnow(),
            trends=trends,
            correlations=correlations,
            charts=charts,
            hypotheses=hypotheses,
            suggested_experiments=experiments,
            facilitation_guide=facilitation_notes,
            sprints_analyzed=len(sprints),
            confidence_overall=overall_confidence,
        )

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Report generation completed in {duration:.2f} seconds")

        return report

    def _create_facilitation_notes(
        self, hypotheses: List, retro_questions: List[str]
    ) -> FacilitationGuide:
        """Create facilitation guide for retrospective meeting."""
        # 15-minute agenda
        agenda = [
            "0-2 min: Review metrics dashboard and headline (silent read)",
            "2-7 min: Discuss top 2 hypotheses - do they resonate? What are we missing?",
            "7-12 min: Review experiment suggestions - which feels most impactful?",
            "12-15 min: Commit to one experiment and assign owners",
        ]

        # Focus areas from hypotheses
        focus_areas = [h.title for h in hypotheses[:3]]

        return FacilitationGuide(
            retro_questions=retro_questions,
            agenda_15min=agenda,
            focus_areas=focus_areas,
        )

    def _calculate_overall_confidence(self, hypotheses: List) -> str:
        """Calculate overall confidence from hypotheses."""
        if not hypotheses:
            return "Low"

        avg_score = sum(h.confidence_score for h in hypotheses) / len(hypotheses)

        if avg_score >= 0.75:
            return "High"
        elif avg_score >= 0.55:
            return "Medium"
        else:
            return "Low"

    def _format_sprint_period(self, sprints: List[SprintMetrics]) -> str:
        """Format sprint period string."""
        if not sprints:
            return "No sprints"

        if len(sprints) == 1:
            return sprints[0].sprint_name

        return f"{sprints[0].sprint_name} - {sprints[-1].sprint_name}"


def get_report_assembler() -> ReportAssembler:
    """Get report assembler instance."""
    return ReportAssembler()
