"""SQLAlchemy 2.0 models for ECPM."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# Import models so Alembic can discover them via Base.metadata
from ecpm.models.series_metadata import SeriesMetadata  # noqa: E402, F401
from ecpm.models.observation import Observation  # noqa: E402, F401
from ecpm.models.io_table import IOMetadata, IOCell  # noqa: E402, F401
from ecpm.models.concentration import (  # noqa: E402, F401
    IndustryConcentration,
    FirmMarketShare,
    ConcentrationTrend,
)

__all__ = [
    "Base",
    "SeriesMetadata",
    "Observation",
    "IOMetadata",
    "IOCell",
    "IndustryConcentration",
    "FirmMarketShare",
    "ConcentrationTrend",
]
