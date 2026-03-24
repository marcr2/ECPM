"""Celery tasks for scheduled data ingestion, caching, and training.

Exports:
    celery_app: The Celery application instance.
    fetch_all_series: Celery task for fetching all configured series.
    run_training_pipeline: Celery task for model training pipeline.
    celery_precompute_all_indicators: Celery task for cache refresh.
"""

from ecpm.tasks.celery_app import celery_app
from ecpm.tasks.fetch_tasks import fetch_all_series
from ecpm.tasks.training_tasks import run_training_pipeline
from ecpm.tasks.cache_tasks import celery_precompute_all_indicators

__all__ = [
    "celery_app",
    "fetch_all_series",
    "run_training_pipeline",
    "celery_precompute_all_indicators",
]
