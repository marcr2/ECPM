"""Series metadata model for tracking FRED/BEA series configuration and status."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from ecpm.models import Base


class SeriesMetadata(Base):
    """Metadata for each ingested time series.

    Tracks source, frequency, units, fetch status, and observation counts
    for both FRED and BEA series.
    """

    __tablename__ = "series_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    series_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    source: Mapped[str] = mapped_column(String(10), nullable=False)  # "FRED" or "BEA"
    source_detail: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    units: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    frequency: Mapped[str] = mapped_column(
        String(1), nullable=False
    )  # "D", "M", "Q", "A"
    seasonal_adjustment: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    last_updated: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_fetched: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    observation_count: Mapped[int] = mapped_column(Integer, default=0)
    fetch_status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, ok, error, stale
    fetch_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<SeriesMetadata(series_id={self.series_id!r}, source={self.source!r})>"
