"""Celery application with beat schedule for daily data refresh.

The Celery app is configured to use Redis as both broker and result
backend. Beat schedule triggers daily data refresh at a configurable
time (default 6:00 AM US/Eastern).
"""

from celery import Celery
from celery.schedules import crontab

from ecpm.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ecpm",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="US/Eastern",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Beat schedule for daily data refresh (DATA-05)
celery_app.conf.beat_schedule = {
    "daily-data-refresh": {
        "task": "ecpm.tasks.fetch_tasks.fetch_all_series",
        "schedule": crontab(
            hour=settings.fetch_schedule_hour,
            minute=settings.fetch_schedule_minute,
        ),
    },
}

# Auto-discover tasks in the tasks package
celery_app.autodiscover_tasks(["ecpm.tasks"])
