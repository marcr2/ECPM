"""Pydantic v2 response models for series data, status, and fetch endpoints."""

from __future__ import annotations

import datetime as dt
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SeriesMetadataResponse(BaseModel):
    """Metadata for a single time series."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    series_id: str
    source: str
    source_detail: Optional[dict] = None
    name: str
    units: Optional[str] = None
    frequency: str
    seasonal_adjustment: Optional[str] = None
    last_updated: Optional[dt.datetime] = None
    last_fetched: Optional[dt.datetime] = None
    observation_count: int = 0
    fetch_status: str = "pending"
    fetch_error: Optional[str] = None
    created_at: Optional[dt.datetime] = None


class ObservationResponse(BaseModel):
    """A single time-series observation data point."""

    model_config = ConfigDict(from_attributes=True)

    observation_date: dt.datetime
    series_id: str
    value: Optional[float] = None
    vintage_date: Optional[dt.date] = None
    gap_flag: bool = False


class SeriesDataResponse(BaseModel):
    """Series metadata combined with its observations."""

    metadata: SeriesMetadataResponse
    observations: list[ObservationResponse]
    total_observations: int


class SeriesListResponse(BaseModel):
    """Paginated list of series metadata."""

    series: list[SeriesMetadataResponse]
    total: int


class FetchStatusResponse(BaseModel):
    """Pipeline health and status information."""

    total_series: int = 0
    ok_count: int = 0
    error_count: int = 0
    pending_count: int = 0
    stale_count: int = 0
    last_fetch_time: Optional[dt.datetime] = None
    next_scheduled_run: Optional[str] = None
    errors: list[dict] = []


class FetchTriggerResponse(BaseModel):
    """Response after triggering a data fetch task."""

    task_id: str
    status: str = "submitted"
