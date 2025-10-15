"""Metrics snapshot management router."""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_db, get_metrics_client
from src.core.database import MetricsSnapshot
from src.core.models import (
    MetricsSnapshotResponse,
    SprintMetrics,
)
from src.utils.metrics_client import MetricsClient

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.post("/fetch", response_model=List[MetricsSnapshotResponse])
async def fetch_and_store_metrics(
    count: int = Query(5, ge=1, le=20, description="Number of sprints to fetch"),
    team_id: Optional[str] = Query(None, description="Team ID to fetch metrics for"),
    db: Session = Depends(get_db),
    client: MetricsClient = Depends(get_metrics_client),
) -> List[MetricsSnapshotResponse]:
    """
    Fetch metrics from external API and store in database.

    Args:
        count: Number of sprints to fetch (1-20)
        team_id: Optional team ID
        db: Database session
        client: Metrics client

    Returns:
        List of stored metrics snapshots
    """
    try:
        # Fetch sprints from external API
        sprints_data = await client.fetch_sprints(count=count, team_id=team_id)

        # Validate and store each sprint
        stored_snapshots = []
        for sprint_data in sprints_data:
            # Validate sprint data
            sprint_metrics = SprintMetrics(**sprint_data)

            # Check if snapshot already exists
            existing = (
                db.query(MetricsSnapshot)
                .filter(MetricsSnapshot.sprint_id == sprint_metrics.sprint_id)
                .first()
            )

            if existing:
                # Update existing snapshot
                existing.metrics_data = sprint_metrics.model_dump(mode="json")
                existing.updated_at = datetime.utcnow()
                snapshot = existing
            else:
                # Create new snapshot
                snapshot = MetricsSnapshot(
                    sprint_id=sprint_metrics.sprint_id,
                    sprint_name=sprint_metrics.sprint_name,
                    start_date=sprint_metrics.start_date,
                    end_date=sprint_metrics.end_date,
                    metrics_data=sprint_metrics.model_dump(mode="json"),
                )
                db.add(snapshot)

            stored_snapshots.append(snapshot)

        db.commit()

        # Refresh and return
        for snapshot in stored_snapshots:
            db.refresh(snapshot)

        return [
            MetricsSnapshotResponse(
                id=s.id,
                sprint_id=s.sprint_id,
                sprint_name=s.sprint_name,
                start_date=s.start_date,
                end_date=s.end_date,
                metrics_data=s.metrics_data,
                fetched_at=s.fetched_at,
                updated_at=s.updated_at,
            )
            for s in stored_snapshots
        ]

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch metrics: {str(e)}"
        )


@router.get("", response_model=List[MetricsSnapshotResponse])
async def list_metrics(
    limit: int = Query(10, ge=1, le=50, description="Number of snapshots to return"),
    offset: int = Query(0, ge=0, description="Number of snapshots to skip"),
    db: Session = Depends(get_db),
) -> List[MetricsSnapshotResponse]:
    """
    List stored metrics snapshots.

    Args:
        limit: Maximum number of snapshots to return
        offset: Number of snapshots to skip
        db: Database session

    Returns:
        List of metrics snapshots
    """
    snapshots = (
        db.query(MetricsSnapshot)
        .order_by(MetricsSnapshot.start_date.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return [
        MetricsSnapshotResponse(
            id=s.id,
            sprint_id=s.sprint_id,
            sprint_name=s.sprint_name,
            start_date=s.start_date,
            end_date=s.end_date,
            metrics_data=s.metrics_data,
            fetched_at=s.fetched_at,
            updated_at=s.updated_at,
        )
        for s in snapshots
    ]


@router.get("/{sprint_id}", response_model=MetricsSnapshotResponse)
async def get_metrics(
    sprint_id: str,
    db: Session = Depends(get_db),
) -> MetricsSnapshotResponse:
    """
    Get metrics snapshot by sprint ID.

    Args:
        sprint_id: Sprint identifier
        db: Database session

    Returns:
        Metrics snapshot

    Raises:
        HTTPException: If snapshot not found
    """
    snapshot = (
        db.query(MetricsSnapshot).filter(MetricsSnapshot.sprint_id == sprint_id).first()
    )

    if not snapshot:
        raise HTTPException(status_code=404, detail=f"Sprint {sprint_id} not found")

    return MetricsSnapshotResponse(
        id=snapshot.id,
        sprint_id=snapshot.sprint_id,
        sprint_name=snapshot.sprint_name,
        start_date=snapshot.start_date,
        end_date=snapshot.end_date,
        metrics_data=snapshot.metrics_data,
        fetched_at=snapshot.fetched_at,
        updated_at=snapshot.updated_at,
    )


@router.delete("/{sprint_id}")
async def delete_metrics(
    sprint_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """
    Delete metrics snapshot by sprint ID.

    Args:
        sprint_id: Sprint identifier
        db: Database session

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: If snapshot not found
    """
    snapshot = (
        db.query(MetricsSnapshot).filter(MetricsSnapshot.sprint_id == sprint_id).first()
    )

    if not snapshot:
        raise HTTPException(status_code=404, detail=f"Sprint {sprint_id} not found")

    db.delete(snapshot)
    db.commit()

    return {"status": "deleted", "sprint_id": sprint_id}
