"""Tests for SQLAlchemy models -- DATA-04, DATA-09.

Covers SeriesMetadata fields, Observation vintage_date column,
gap_flag column, and unique constraint on series_id.
Tests are in RED state until Plan 01-02 implements the models.
"""

from __future__ import annotations

import pytest

# Import guards
try:
    from sqlalchemy import inspect as sa_inspect

    _HAS_SQLALCHEMY = True
except ImportError:
    _HAS_SQLALCHEMY = False

try:
    from ecpm.models import Observation, SeriesMetadata

    _HAS_MODELS = True
except ImportError:
    _HAS_MODELS = False

pytestmark = pytest.mark.skipif(
    not _HAS_MODELS, reason="ecpm.models not yet implemented"
)


class TestMetadataFields:
    """SeriesMetadata model has all required columns."""

    def test_metadata_fields(self) -> None:
        """Verify SeriesMetadata has: units, frequency, seasonal_adjustment,
        source, last_updated, observation_count, fetch_status."""
        mapper = sa_inspect(SeriesMetadata)
        column_names = {col.key for col in mapper.columns}

        required_fields = {
            "units",
            "frequency",
            "seasonal_adjustment",
            "source",
            "last_updated",
            "observation_count",
            "fetch_status",
        }

        missing = required_fields - column_names
        assert not missing, (
            f"SeriesMetadata missing required columns: {missing}"
        )

    def test_metadata_has_series_id(self) -> None:
        """series_id is a column on SeriesMetadata."""
        mapper = sa_inspect(SeriesMetadata)
        column_names = {col.key for col in mapper.columns}
        assert "series_id" in column_names, "SeriesMetadata must have series_id column"

    def test_metadata_has_name(self) -> None:
        """SeriesMetadata should have a human-readable name field."""
        mapper = sa_inspect(SeriesMetadata)
        column_names = {col.key for col in mapper.columns}
        assert "name" in column_names or "title" in column_names, (
            "SeriesMetadata should have a name or title column"
        )


class TestVintageDateColumn:
    """Observation model has vintage_date column (nullable)."""

    def test_vintage_date_column(self) -> None:
        mapper = sa_inspect(Observation)
        column_names = {col.key for col in mapper.columns}
        assert "vintage_date" in column_names, (
            "Observation must have vintage_date column (DATA-09)"
        )

    def test_vintage_date_nullable(self) -> None:
        """vintage_date should be nullable (no ALFRED pipeline yet)."""
        mapper = sa_inspect(Observation)
        for col in mapper.columns:
            if col.key == "vintage_date":
                assert col.nullable, "vintage_date should be nullable"
                break


class TestGapFlagColumn:
    """Observation model has gap_flag boolean column."""

    def test_gap_flag_column(self) -> None:
        mapper = sa_inspect(Observation)
        column_names = {col.key for col in mapper.columns}
        assert "gap_flag" in column_names, (
            "Observation must have gap_flag boolean column"
        )


class TestSeriesIdUnique:
    """SeriesMetadata.series_id has unique constraint."""

    def test_series_id_unique(self) -> None:
        """Verify series_id column or a unique constraint covers it."""
        mapper = sa_inspect(SeriesMetadata)

        # Check column-level unique
        for col in mapper.columns:
            if col.key == "series_id":
                # Column is either primary key or has unique=True
                if col.primary_key or col.unique:
                    return  # Constraint found
                break

        # Check table-level unique constraints
        table = SeriesMetadata.__table__
        for constraint in table.constraints:
            if hasattr(constraint, "columns"):
                col_names = {c.name for c in constraint.columns}
                if "series_id" in col_names:
                    return  # Found in a constraint

        # Check indexes for unique
        for index in table.indexes:
            if index.unique and "series_id" in {c.name for c in index.columns}:
                return

        pytest.fail("series_id must have a unique constraint (column, table, or index)")
