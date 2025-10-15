"""
API endpoints for asynchronous task management.
"""

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException

from src.core.celery_app import celery_app
from src.core.models import (
    AsyncMetricsSyncRequest,
    AsyncMetricsSyncResponse,
    AsyncReportRequest,
    AsyncReportResponse,
    TaskStatus,
)
from src.tasks.analysis_tasks import generate_report_task, sync_metrics_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/reports/generate", response_model=AsyncReportResponse)
async def generate_report_async(request: AsyncReportRequest):
    """
    Trigger async report generation task.

    This endpoint initiates a background task to generate a retrospective report.
    Use the returned task_id to check the status and retrieve results.
    """
    try:
        # Submit task to Celery
        task = generate_report_task.delay(
            sprint_count=request.sprint_count,
            sprint_ids=request.sprint_ids,
            custom_context=request.custom_context,
            focus_metrics=request.focus_metrics,
        )

        return AsyncReportResponse(
            task_id=task.id,
            status="PENDING",
            message=f"Report generation task submitted successfully. Task ID: {task.id}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit report generation task: {str(e)}",
        )


@router.post("/metrics/sync", response_model=AsyncMetricsSyncResponse)
async def sync_metrics_async(request: AsyncMetricsSyncRequest):
    """
    Trigger async metrics sync task.

    This endpoint initiates a background task to sync metrics from the external API.
    Use the returned task_id to check the status and retrieve results.
    """
    try:
        # Submit task to Celery
        task = sync_metrics_task.delay(
            sprint_count=request.sprint_count,
            team_id=request.team_id,
            force_refresh=request.force_refresh,
        )

        return AsyncMetricsSyncResponse(
            task_id=task.id,
            status="PENDING",
            message=f"Metrics sync task submitted successfully. Task ID: {task.id}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to submit metrics sync task: {str(e)}"
        )


@router.get("/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    Get the status of a task.

    Returns the current status, result (if completed), or error (if failed).
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        response = TaskStatus(
            task_id=task_id,
            status=task_result.state,
            result=None,
            error=None,
        )

        if task_result.state == "SUCCESS":
            response.result = task_result.result
        elif task_result.state == "FAILURE":
            response.error = str(task_result.info)

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get task status: {str(e)}"
        )


@router.delete("/{task_id}")
async def revoke_task(task_id: str):
    """
    Revoke/cancel a running task.

    Attempts to cancel a task that is pending or running.
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        if task_result.state in ["PENDING", "STARTED"]:
            task_result.revoke(terminate=True)
            return {
                "task_id": task_id,
                "status": "REVOKED",
                "message": "Task revoked successfully",
            }
        else:
            return {
                "task_id": task_id,
                "status": task_result.state,
                "message": f"Task is already {task_result.state}, cannot revoke",
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke task: {str(e)}")
