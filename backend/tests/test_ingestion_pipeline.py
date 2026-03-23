"""Tests for data ingestion pipeline -- DATA-02, DATA-06, DATA-07.

Covers FRED/BEA persistence, gap handling, native frequency storage,
error resilience, and metadata upsert. Tests are in RED state until
Plan 01-03 implements the pipeline.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# Import guards
try:
    from ecpm.pipeline import IngestionPipeline

    _HAS_PIPELINE = True
except ImportError:
    _HAS_PIPELINE = False

try:
    from ecpm.models import Observation, SeriesMetadata

    _HAS_MODELS = True
except ImportError:
    _HAS_MODELS = False

try:
    import pandas as pd

    _HAS_PANDAS = True
except ImportError:
    _HAS_PANDAS = False

pytestmark = pytest.mark.skipif(
    not _HAS_PIPELINE, reason="ecpm.pipeline not yet implemented"
)


class TestFredPersistence:
    """Pipeline stores FRED data in observations table."""

    @pytest.mark.asyncio
    async def test_fred_persistence(
        self, async_session, mock_fred_client, test_series_config
    ) -> None:
        pipeline = IngestionPipeline(
            session=async_session,
            fred_client=mock_fred_client,
            bea_client=MagicMock(),
            config=test_series_config,
        )

        await pipeline.ingest_fred_series("GDPC1")

        # Verify observations were persisted
        if _HAS_MODELS:
            from sqlalchemy import select

            result = await async_session.execute(
                select(Observation).where(Observation.series_id == "GDPC1")
            )
            observations = result.scalars().all()
            assert len(observations) > 0, "FRED data should be persisted to observations"


class TestBEAPersistence:
    """Pipeline stores BEA data in observations table."""

    @pytest.mark.asyncio
    async def test_bea_persistence(
        self, async_session, mock_bea_client, test_series_config
    ) -> None:
        pipeline = IngestionPipeline(
            session=async_session,
            fred_client=MagicMock(),
            bea_client=mock_bea_client,
            config=test_series_config,
        )

        await pipeline.ingest_bea_table("T11200")

        # Verify observations were persisted
        if _HAS_MODELS:
            from sqlalchemy import select

            result = await async_session.execute(
                select(Observation).where(
                    Observation.series_id.like("BEA:T11200:%")
                )
            )
            observations = result.scalars().all()
            assert len(observations) > 0, "BEA data should be persisted to observations"


class TestGapHandling:
    """NaN values stored as NULL with gap_flag=True, no interpolation."""

    @pytest.mark.asyncio
    async def test_gap_handling(
        self, async_session, mock_fred_client, test_series_config
    ) -> None:
        # Inject NaN into mock data
        if _HAS_PANDAS:
            import numpy as np

            data_with_gaps = pd.Series(
                [18_000.0, np.nan, 18_500.0, np.nan, 18_700.0],
                index=pd.to_datetime(
                    ["2023-01-01", "2023-04-01", "2023-07-01", "2023-10-01", "2024-01-01"]
                ),
                name="GDPC1",
            )
            mock_fred_client.get_series.return_value = data_with_gaps

        pipeline = IngestionPipeline(
            session=async_session,
            fred_client=mock_fred_client,
            bea_client=MagicMock(),
            config=test_series_config,
        )

        await pipeline.ingest_fred_series("GDPC1")

        # Verify gap handling: NaN stored as NULL with gap_flag
        if _HAS_MODELS:
            from sqlalchemy import select

            result = await async_session.execute(
                select(Observation).where(
                    Observation.series_id == "GDPC1",
                    Observation.gap_flag.is_(True),
                )
            )
            gap_rows = result.scalars().all()
            assert len(gap_rows) >= 2, (
                "NaN values should be stored with gap_flag=True"
            )

            # Verify no interpolation: gap rows should have NULL value
            for row in gap_rows:
                assert row.value is None, (
                    "Gap observations should have NULL value (no interpolation)"
                )


class TestNativeFrequency:
    """Monthly data stored as monthly, quarterly as quarterly (no resampling)."""

    @pytest.mark.asyncio
    async def test_native_frequency(
        self, async_session, mock_fred_client, test_series_config
    ) -> None:
        # Create monthly data
        if _HAS_PANDAS:
            monthly_data = pd.Series(
                [5.0, 5.1, 5.2, 5.0, 4.9, 4.8],
                index=pd.to_datetime(
                    ["2023-01-01", "2023-02-01", "2023-03-01",
                     "2023-04-01", "2023-05-01", "2023-06-01"]
                ),
                name="UNRATE",
            )
            mock_fred_client.get_series.return_value = monthly_data

        pipeline = IngestionPipeline(
            session=async_session,
            fred_client=mock_fred_client,
            bea_client=MagicMock(),
            config=test_series_config,
        )

        await pipeline.ingest_fred_series("UNRATE")

        # Verify data stored at native monthly frequency
        if _HAS_MODELS:
            from sqlalchemy import select

            result = await async_session.execute(
                select(Observation).where(Observation.series_id == "UNRATE")
            )
            observations = result.scalars().all()
            # Monthly data should have 6 observations, not resampled to quarterly (2)
            assert len(observations) == 6, (
                f"Monthly data should have 6 rows (native frequency), got {len(observations)}"
            )


class TestErrorContinues:
    """Single series error does not abort entire pipeline."""

    @pytest.mark.asyncio
    async def test_error_continues(
        self, async_session, mock_fred_client, test_series_config
    ) -> None:
        # Make first series fail
        call_count = 0
        original_get = mock_fred_client.get_series.side_effect

        def conditional_fail(series_id):
            nonlocal call_count
            call_count += 1
            if series_id == "GDPC1":
                raise ConnectionError("Simulated FRED failure")
            return mock_fred_client.get_series.return_value

        mock_fred_client.get_series.side_effect = conditional_fail

        pipeline = IngestionPipeline(
            session=async_session,
            fred_client=mock_fred_client,
            bea_client=MagicMock(),
            config=test_series_config,
        )

        # Pipeline should not raise even though GDPC1 fails
        result = await pipeline.ingest_all()

        # At least one series was attempted after the failure
        assert call_count >= 2, (
            "Pipeline should continue to next series after error"
        )
        # Result should indicate partial success
        assert hasattr(result, "errors") or isinstance(result, dict), (
            "Pipeline should return result with error information"
        )


class TestMetadataUpsert:
    """SeriesMetadata record created/updated with correct fields."""

    @pytest.mark.asyncio
    async def test_metadata_upsert(
        self, async_session, mock_fred_client, test_series_config
    ) -> None:
        pipeline = IngestionPipeline(
            session=async_session,
            fred_client=mock_fred_client,
            bea_client=MagicMock(),
            config=test_series_config,
        )

        await pipeline.ingest_fred_series("GDPC1")

        # Verify metadata record was created
        if _HAS_MODELS:
            from sqlalchemy import select

            result = await async_session.execute(
                select(SeriesMetadata).where(SeriesMetadata.series_id == "GDPC1")
            )
            metadata = result.scalar_one_or_none()
            assert metadata is not None, "SeriesMetadata should be created for GDPC1"
            assert metadata.source == "FRED"
            assert metadata.frequency is not None
            assert metadata.units is not None
