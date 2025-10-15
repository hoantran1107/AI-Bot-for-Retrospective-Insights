"""
Celery application configuration and initialization.
"""

from celery import Celery

from src.core.config import settings

# Create Celery app
celery_app = Celery(
    "retro_insights",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.tasks.analysis_tasks"],
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Optional: Configure task routes
celery_app.conf.task_routes = {
    "src.tasks.analysis_tasks.generate_report_task": {"queue": "reports"},
    "src.tasks.analysis_tasks.sync_metrics_task": {"queue": "metrics"},
}
