"""Celery tasks for scheduled data ingestion, caching, and training.

Exports:
    celery_app: The Celery application instance.
    fetch_all_series: Celery task for fetching all configured series.
    run_training_pipeline: Celery task for model training pipeline.
    celery_precompute_all_indicators: Celery task for cache refresh.
    fetch_io_tables: Celery task for BEA I-O table ingestion.
    fetch_concentration_data: Celery task for Census concentration ingestion.
    refresh_edgar_concentration: Weekly SEC EDGAR concentration refresh.
"""

from ecpm.tasks.celery_app import celery_app
from ecpm.tasks.fetch_tasks import fetch_all_series
from ecpm.tasks.training_tasks import run_training_pipeline
from ecpm.tasks.cache_tasks import celery_precompute_all_indicators
from ecpm.tasks.structural_tasks import fetch_io_tables
from ecpm.tasks.concentration_tasks import fetch_concentration_data
from ecpm.tasks.edgar_tasks import refresh_edgar_concentration

__all__ = [
    "celery_app",
    "fetch_all_series",
    "run_training_pipeline",
    "celery_precompute_all_indicators",
    "fetch_io_tables",
    "fetch_concentration_data",
    "refresh_edgar_concentration",
]
