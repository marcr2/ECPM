"""Celery tasks for scheduled data ingestion.

Exports:
    celery_app: The Celery application instance.
    fetch_all_series: Celery task for fetching all configured series.
"""

from ecpm.tasks.celery_app import celery_app
from ecpm.tasks.fetch_tasks import fetch_all_series

__all__ = ["celery_app", "fetch_all_series"]
