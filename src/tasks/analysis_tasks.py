"""
Celery tasks for retrospective analysis.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from celery import Task
from sqlalchemy.orm import Session

from src.analysis.report_assembler import ReportAssembler
from src.core.celery_app import celery_app
from src.core.database import (
    AnalysisReportDB,
    ExperimentDB,
    HypothesisDB,
    MetricsSnapshot,
    SessionLocal,
)
from src.core.models import SprintMetrics
from src.utils.metrics_client import MetricsClient

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session management."""

    _db: Optional[Session] = None

    @property
    def db(self) -> Session:
        """Get database session."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        """Close database session after task completion."""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True, name="generate_report_task")
def generate_report_task(
    self,
    sprint_count: Optional[int] = None,
    sprint_ids: Optional[List[str]] = None,
    custom_context: Optional[str] = None,
    focus_metrics: Optional[List[str]] = None,
) -> Dict:
    """
    Generate a retrospective report asynchronously.

    Args:
        sprint_count: Number of recent sprints to analyze
        sprint_ids: Specific sprint IDs to analyze
        custom_context: Additional context for the analysis
        focus_metrics: Specific metrics to focus on

    Returns:
        Dictionary containing report data and metadata
    """
    logger.info(
        f"Starting report generation task: sprint_count={sprint_count}, "
        f"sprint_ids={sprint_ids}"
    )

    try:
        # Fetch metrics from database
        query = self.db.query(MetricsSnapshot).order_by(
            MetricsSnapshot.start_date.desc()
        )

        if sprint_ids:
            query = query.filter(MetricsSnapshot.sprint_id.in_(sprint_ids))
        else:
            query = query.limit(sprint_count or 5)

        snapshots = query.all()

        if len(snapshots) < 2:
            raise ValueError(
                f"Insufficient data: found {len(snapshots)} sprints, need at least 2"
            )

        # Convert to SprintMetrics
        sprints = [SprintMetrics(**snapshot.metrics_data) for snapshot in snapshots]

        # Generate report
        assembler = ReportAssembler()
        report = assembler.generate_report(
            sprints=sprints,
            custom_context=custom_context,
            focus_metrics=focus_metrics,
        )

        # Store report in database
        report_db = AnalysisReportDB(
            report_date=report.generated_at,
            sprint_ids=[s.sprint_id for s in sprints],
            headline=report.headline,
            summary=report.summary,
            report_data=report.model_dump(mode="json"),
        )
        self.db.add(report_db)

        # Store hypotheses
        for hypothesis in report.hypotheses:
            hyp_db = HypothesisDB(
                report=report_db,
                hypothesis_type="general",
                title=hypothesis.title,
                description=hypothesis.description,
                confidence=hypothesis.confidence,
                confidence_score=hypothesis.confidence_score,
                potential_impact=hypothesis.potential_impact,
                affected_metrics=hypothesis.affected_metrics,
                supporting_evidence=[
                    ev.model_dump(mode="json") for ev in hypothesis.evidence
                ],
            )
            self.db.add(hyp_db)

        # Store experiments
        for experiment in report.suggested_experiments:
            exp_db = ExperimentDB(
                report=report_db,
                title=experiment.title,
                description=experiment.description,
                rationale=experiment.rationale,
                duration_sprints=experiment.duration_sprints,
                implementation_steps=experiment.implementation_steps,
                success_metrics=experiment.success_metrics,
                expected_outcome=f"Expected: {experiment.rationale}",
            )
            self.db.add(exp_db)

        self.db.commit()
        self.db.refresh(report_db)

        logger.info(f"Report generated successfully with ID: {report_db.id}")

        return {
            "status": "success",
            "report_id": report_db.id,
            "headline": report.headline,
            "sprints_analyzed": len(sprints),
            "hypotheses_count": len(report.hypotheses),
            "experiments_count": len(report.suggested_experiments),
        }

    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}", exc_info=True)
        self.db.rollback()
        raise


@celery_app.task(base=DatabaseTask, bind=True, name="sync_metrics_task")
def sync_metrics_task(
    self,
    sprint_count: int = 5,
    team_id: Optional[str] = None,
    force_refresh: bool = False,
) -> Dict:
    """
    Sync metrics from external API asynchronously.

    Args:
        sprint_count: Number of recent sprints to fetch
        team_id: Optional team identifier
        force_refresh: Force refresh even if data exists

    Returns:
        Dictionary containing sync results
    """
    logger.info(
        f"Starting metrics sync task: sprint_count={sprint_count}, "
        f"team_id={team_id}, force_refresh={force_refresh}"
    )

    try:
        # Initialize metrics client
        client = MetricsClient()

        # Fetch sprints from external API
        sprints_data = client.fetch_sprints(count=sprint_count, team_id=team_id)

        created_count = 0
        updated_count = 0

        for sprint_data in sprints_data:
            sprint_metrics = SprintMetrics(**sprint_data)

            # Check if snapshot exists
            existing = (
                self.db.query(MetricsSnapshot)
                .filter(MetricsSnapshot.sprint_id == sprint_metrics.sprint_id)
                .first()
            )

            if existing:
                if force_refresh:
                    existing.metrics_data = sprint_metrics.model_dump(mode="json")
                    existing.updated_at = datetime.utcnow()
                    updated_count += 1
                    logger.info(
                        f"Updated metrics for sprint: {sprint_metrics.sprint_id}"
                    )
                else:
                    logger.info(
                        f"Skipping existing sprint: {sprint_metrics.sprint_id} "
                        "(use force_refresh=True to update)"
                    )
            else:
                snapshot = MetricsSnapshot(
                    sprint_id=sprint_metrics.sprint_id,
                    sprint_name=sprint_metrics.sprint_name,
                    start_date=sprint_metrics.start_date,
                    end_date=sprint_metrics.end_date,
                    metrics_data=sprint_metrics.model_dump(mode="json"),
                )
                self.db.add(snapshot)
                created_count += 1
                logger.info(
                    f"Created metrics snapshot for sprint: {sprint_metrics.sprint_id}"
                )

        self.db.commit()

        logger.info(
            f"Metrics sync completed: {created_count} created, {updated_count} updated"
        )

        return {
            "status": "success",
            "sprints_fetched": len(sprints_data),
            "created": created_count,
            "updated": updated_count,
            "skipped": len(sprints_data) - created_count - updated_count,
        }

    except Exception as e:
        logger.error(f"Metrics sync failed: {str(e)}", exc_info=True)
        self.db.rollback()
        raise


@celery_app.task(name="cleanup_old_reports_task")
def cleanup_old_reports_task(days_to_keep: int = 90) -> Dict:
    """
    Clean up old reports from the database.

    Args:
        days_to_keep: Number of days to keep reports

    Returns:
        Dictionary containing cleanup results
    """
    logger.info(f"Starting cleanup task: keeping reports from last {days_to_keep} days")

    db = SessionLocal()
    try:
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # Delete old reports
        deleted = (
            db.query(AnalysisReportDB)
            .filter(AnalysisReportDB.report_date < cutoff_date)
            .delete()
        )

        db.commit()

        logger.info(f"Cleanup completed: {deleted} old reports deleted")

        return {
            "status": "success",
            "deleted": deleted,
            "cutoff_date": cutoff_date.isoformat(),
        }

    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()
