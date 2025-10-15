"""Report generation and retrieval router."""

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.analysis.report_assembler import ReportAssembler
from src.api.dependencies import get_db
from src.core.database import AnalysisReportDB, MetricsSnapshot
from src.core.models import (
    GenerateReportRequest,
    ReportListResponse,
    RetrospectiveReport,
    SprintMetrics,
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate", response_model=RetrospectiveReport)
async def generate_report(
    request: GenerateReportRequest,
    db: Session = Depends(get_db),
) -> RetrospectiveReport:
    """
    Generate a retrospective insights report.

    Args:
        request: Report generation parameters
        db: Database session

    Returns:
        Generated retrospective report

    Raises:
        HTTPException: If not enough metrics data or generation fails
    """
    try:
        # Fetch metrics from database
        query = db.query(MetricsSnapshot).order_by(MetricsSnapshot.start_date.desc())

        if request.sprint_ids:
            query = query.filter(MetricsSnapshot.sprint_id.in_(request.sprint_ids))
        else:
            query = query.limit(request.sprint_count or 5)

        snapshots = query.all()

        if len(snapshots) < 2:
            raise HTTPException(
                status_code=400,
                detail="Need at least 2 sprints to generate meaningful insights",
            )

        # Convert snapshots to SprintMetrics
        sprints = [SprintMetrics(**s.metrics_data) for s in snapshots]

        # Generate report
        assembler = ReportAssembler()
        report = assembler.generate_report(
            sprints=sprints,
            custom_context=request.custom_context,
            focus_metrics=request.focus_metrics,
        )

        # Store report in database
        report_db = AnalysisReportDB(
            report_date=report.generated_at,
            sprint_ids=[s.sprint_id for s in sprints],
            headline=report.headline,
            summary=report.summary,
            report_data=report.model_dump(mode="json"),
        )
        db.add(report_db)

        # Store hypotheses
        for hypothesis in report.hypotheses:
            from src.core.database import HypothesisDB

            hyp_db = HypothesisDB(
                report=report_db,
                hypothesis_type="general",  # Default type
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
            db.add(hyp_db)

        # Store experiments
        for experiment in report.suggested_experiments:
            from src.core.database import ExperimentDB

            exp_db = ExperimentDB(
                report=report_db,
                title=experiment.title,
                description=experiment.description,
                rationale=experiment.rationale,
                duration_sprints=experiment.duration_sprints,
                implementation_steps=experiment.implementation_steps,
                success_metrics=experiment.success_metrics,
                expected_outcome=f"Expected: {experiment.rationale}",  # Use rationale as expected outcome
            )
            db.add(exp_db)

        db.commit()
        db.refresh(report_db)

        return report

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to generate report: {str(e)}"
        )


@router.get("", response_model=List[ReportListResponse])
async def list_reports(
    limit: int = Query(10, ge=1, le=50, description="Number of reports to return"),
    offset: int = Query(0, ge=0, description="Number of reports to skip"),
    db: Session = Depends(get_db),
) -> List[ReportListResponse]:
    """
    List generated reports.

    Args:
        limit: Maximum number of reports to return
        offset: Number of reports to skip
        db: Database session

    Returns:
        List of report summaries
    """
    reports = (
        db.query(AnalysisReportDB)
        .order_by(AnalysisReportDB.report_date.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return [
        ReportListResponse(
            id=r.id,
            report_date=r.report_date,
            headline=r.headline,
            summary=r.summary,
            sprint_ids=r.sprint_ids,
            created_at=r.created_at,
        )
        for r in reports
    ]


@router.get("/{report_id}", response_model=RetrospectiveReport)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
) -> RetrospectiveReport:
    """
    Get a specific report by ID.

    Args:
        report_id: Report identifier
        db: Database session

    Returns:
        Full retrospective report

    Raises:
        HTTPException: If report not found
    """
    report = db.query(AnalysisReportDB).filter(AnalysisReportDB.id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    # Return stored report data
    return RetrospectiveReport(**report.report_data)


@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """
    Delete a report by ID.

    Args:
        report_id: Report identifier
        db: Database session

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: If report not found
    """
    report = db.query(AnalysisReportDB).filter(AnalysisReportDB.id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    db.delete(report)
    db.commit()

    return {"status": "deleted", "report_id": str(report_id)}
