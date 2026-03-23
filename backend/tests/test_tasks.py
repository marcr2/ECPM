"""Tests for Celery tasks -- DATA-05.

Covers celery app existence, beat schedule configuration, and
task registration. Tests are in RED state until Plan 01-03.
"""

from __future__ import annotations

import pytest

# Import guards
try:
    from ecpm.tasks import celery_app

    _HAS_CELERY_APP = True
except ImportError:
    _HAS_CELERY_APP = False

try:
    from ecpm.tasks import fetch_all_series

    _HAS_FETCH_TASK = True
except ImportError:
    _HAS_FETCH_TASK = False

pytestmark = pytest.mark.skipif(
    not _HAS_CELERY_APP, reason="ecpm.tasks not yet implemented"
)


class TestCeleryAppExists:
    """celery_app is a Celery instance."""

    def test_celery_app_exists(self) -> None:
        from celery import Celery

        assert isinstance(celery_app, Celery), (
            "celery_app should be an instance of celery.Celery"
        )

    def test_celery_app_has_name(self) -> None:
        assert celery_app.main is not None, "Celery app should have a name"


class TestScheduledFetch:
    """beat_schedule contains 'daily-data-refresh' key."""

    def test_scheduled_fetch(self) -> None:
        beat_schedule = celery_app.conf.beat_schedule

        assert isinstance(beat_schedule, dict), (
            "beat_schedule should be a dict"
        )
        assert "daily-data-refresh" in beat_schedule, (
            "beat_schedule must contain 'daily-data-refresh' key"
        )

        entry = beat_schedule["daily-data-refresh"]
        assert "task" in entry, "Schedule entry must specify a 'task'"
        assert "schedule" in entry, "Schedule entry must specify a 'schedule'"


class TestFetchTaskRegistered:
    """fetch_all_series is a registered Celery task."""

    @pytest.mark.skipif(
        not _HAS_FETCH_TASK, reason="fetch_all_series not yet defined"
    )
    def test_fetch_task_registered(self) -> None:
        # Celery tasks have a .name attribute and .delay() method
        assert hasattr(fetch_all_series, "name"), (
            "fetch_all_series should be a registered Celery task with a .name"
        )
        assert hasattr(fetch_all_series, "delay"), (
            "fetch_all_series should have .delay() (Celery task method)"
        )
        assert callable(fetch_all_series.delay), (
            "fetch_all_series.delay should be callable"
        )
