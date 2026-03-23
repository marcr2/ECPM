"""Observation model for time-series data points stored in TimescaleDB hypertable."""

import datetime as dt
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ecpm.models import Base


class Observation(Base):
    """Individual time-series observation.

    Stored in a TimescaleDB hypertable partitioned by observation_date.
    Each row represents a single data point for a series at a specific date,
    with optional vintage_date for revision tracking (DATA-09).
    """

    __tablename__ = "observations"

    observation_date: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True
    )
    series_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("series_metadata.series_id"),
        primary_key=True,
    )
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vintage_date: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    gap_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<Observation(series_id={self.series_id!r}, "
            f"date={self.observation_date!r}, value={self.value!r})>"
        )
