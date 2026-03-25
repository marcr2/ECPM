"""Ingestion pipeline orchestrating fetch-transform-store for FRED and BEA data.

The IngestionPipeline coordinates API clients, transforms raw data into
database models, and upserts observations with ON CONFLICT handling.
Missing data (NaN) is stored as NULL with gap_flag=True -- no interpolation
on ingestion (DATA-06).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
import pandas as pd
import structlog
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ecpm.models.observation import Observation
from ecpm.models.series_metadata import SeriesMetadata

logger = structlog.get_logger()


@dataclass
class IngestionResult:
    """Result of an ingestion run.

    Attributes:
        series_processed: Number of series successfully processed.
        series_failed: Number of series that failed.
        observations_upserted: Total observations inserted/updated.
        errors: Dict mapping series_id to error message.
    """

    series_processed: int = 0
    series_failed: int = 0
    observations_upserted: int = 0
    errors: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "series_processed": self.series_processed,
            "series_failed": self.series_failed,
            "observations_upserted": self.observations_upserted,
            "errors": self.errors,
        }


class IngestionPipeline:
    """Orchestrates fetch-transform-store for FRED and BEA data.

    Handles:
    - Fetching data from FRED/BEA API clients
    - Transforming raw data into Observation records
    - Upserting metadata and observations into the database
    - Gap detection: NaN -> value=NULL, gap_flag=True (DATA-06)
    - Error resilience: individual series failures don't abort the pipeline
    - Progress callbacks for SSE streaming

    Args:
        session: SQLAlchemy async session for database operations.
        fred_client: FRED API client instance.
        bea_client: BEA API client instance.
        config: Series configuration dict (from series_config.yaml or test fixture).
        progress_callback: Optional callback for progress updates.
    """

    def __init__(
        self,
        session: AsyncSession,
        fred_client: Any,
        bea_client: Any,
        config: dict[str, Any] | None = None,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.session = session
        self.fred_client = fred_client
        self.bea_client = bea_client
        self.config = config or {}
        self.progress_callback = progress_callback

    def _notify_progress(self, data: dict[str, Any]) -> None:
        """Send progress update if callback is registered."""
        if self.progress_callback:
            self.progress_callback(data)

    async def _upsert_metadata(
        self,
        series_id: str,
        source: str,
        name: str,
        frequency: str = "Q",
        units: str | None = None,
        seasonal_adjustment: str | None = None,
        source_detail: dict[str, Any] | None = None,
        observation_count: int = 0,
    ) -> None:
        """Create or update series metadata record.

        Uses SQLAlchemy merge for SQLite compatibility in tests,
        or ON CONFLICT for PostgreSQL.
        """
        # Check if metadata already exists
        result = await self.session.execute(
            select(SeriesMetadata).where(SeriesMetadata.series_id == series_id)
        )
        existing = result.scalar_one_or_none()
        result.close()  # Explicitly close result to free connection

        now = dt.datetime.now(dt.timezone.utc)

        if existing:
            existing.name = name
            existing.units = units
            existing.frequency = frequency
            existing.seasonal_adjustment = seasonal_adjustment
            existing.source_detail = source_detail
            existing.last_fetched = now
            existing.observation_count = observation_count
            existing.fetch_status = "ok"
            existing.fetch_error = None
        else:
            metadata = SeriesMetadata(
                series_id=series_id,
                source=source,
                name=name,
                units=units,
                frequency=frequency,
                seasonal_adjustment=seasonal_adjustment,
                source_detail=source_detail,
                last_fetched=now,
                observation_count=observation_count,
                fetch_status="ok",
                fetch_error=None,
            )
            self.session.add(metadata)

        await self.session.flush()

    async def _store_observations(
        self,
        series_id: str,
        data: pd.Series,
    ) -> int:
        """Transform and store observations from a pandas Series.

        NaN values are stored as NULL with gap_flag=True (DATA-06).
        No interpolation is performed during ingestion.

        Returns:
            Number of observations stored.
        """
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        observations = []
        for date, value in data.items():
            is_gap = pd.isna(value)

            obs_dict = {
                "observation_date": pd.Timestamp(date).to_pydatetime().replace(
                    tzinfo=dt.timezone.utc
                ),
                "series_id": series_id,
                "value": None if is_gap else float(value),
                "gap_flag": bool(is_gap),
                "vintage_date": None,
            }
            observations.append(obs_dict)

            if is_gap:
                logger.warning(
                    "gap_detected",
                    series_id=series_id,
                    date=str(date),
                )

        # Bulk upsert in batches to avoid asyncpg parameter limit (32767)
        # With 5 params per row, batch size of 6000 = 30000 params (safe margin)
        total_count = 0
        batch_size = 6000

        for i in range(0, len(observations), batch_size):
            batch = observations[i:i + batch_size]
            if batch:
                stmt = pg_insert(Observation).values(batch)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["observation_date", "series_id"],
                    set_={
                        "value": stmt.excluded.value,
                        "gap_flag": stmt.excluded.gap_flag,
                    },
                )
                await self.session.execute(stmt)
                total_count += len(batch)

        await self.session.flush()
        return total_count

    async def _store_bea_observations(
        self,
        table_name: str,
        data: pd.DataFrame,
    ) -> int:
        """Transform and store BEA table data as observations.

        Each line number in a BEA table becomes a separate series with
        the ID format: BEA:{table_name}:L{line_number}

        Returns:
            Number of observations stored.
        """
        total = 0

        # Group by line number
        if "LineNumber" not in data.columns:
            logger.warning("bea_no_line_number", table_name=table_name)
            return 0

        for line_num, group in data.groupby("LineNumber"):
            series_id = f"BEA:{table_name}:L{line_num}"

            # Upsert metadata FIRST (required for foreign key constraint)
            line_desc = ""
            if "LineDescription" in data.columns:
                descs = group["LineDescription"].unique()
                line_desc = str(descs[0]) if len(descs) > 0 else ""

            await self._upsert_metadata(
                series_id=series_id,
                source="BEA",
                name=f"{table_name} - {line_desc}",
                frequency="Q",
                source_detail={"table_name": table_name, "line_number": int(line_num)},
                observation_count=len(group),
            )

            # Store observations AFTER metadata exists
            # Collect observations for bulk upsert
            observations = []
            for _, row in group.iterrows():
                time_period = str(row.get("TimePeriod", ""))
                obs_date = self._parse_bea_time_period(time_period)
                if obs_date is None:
                    continue

                raw_value = row.get("DataValue")
                # BEA may return string values
                try:
                    value = float(str(raw_value).replace(",", ""))
                    is_gap = pd.isna(value)
                except (ValueError, TypeError):
                    value = None
                    is_gap = True

                obs_dict = {
                    "observation_date": obs_date,
                    "series_id": series_id,
                    "value": None if is_gap else value,
                    "gap_flag": bool(is_gap),
                    "vintage_date": None,
                }
                observations.append(obs_dict)

            # Bulk upsert in batches to avoid asyncpg parameter limit (32767)
            # With 5 params per row, batch size of 6000 = 30000 params (safe margin)
            if observations:
                from sqlalchemy.dialects.postgresql import insert as pg_insert

                batch_size = 6000
                for i in range(0, len(observations), batch_size):
                    batch = observations[i:i + batch_size]
                    if batch:
                        stmt = pg_insert(Observation).values(batch)
                        stmt = stmt.on_conflict_do_update(
                            index_elements=["observation_date", "series_id"],
                            set_={
                                "value": stmt.excluded.value,
                                "gap_flag": stmt.excluded.gap_flag,
                            },
                        )
                        await self.session.execute(stmt)
                        total += len(batch)

        await self.session.flush()
        return total

    @staticmethod
    def _parse_bea_time_period(time_period: str) -> dt.datetime | None:
        """Parse BEA TimePeriod format (e.g., '2023Q1', '2023') to datetime."""
        try:
            if "Q" in time_period:
                year = int(time_period[:4])
                quarter = int(time_period[-1])
                month = (quarter - 1) * 3 + 1
                return dt.datetime(year, month, 1, tzinfo=dt.timezone.utc)
            elif len(time_period) == 4:
                return dt.datetime(int(time_period), 1, 1, tzinfo=dt.timezone.utc)
            elif "M" in time_period:
                year = int(time_period[:4])
                month = int(time_period[5:])
                return dt.datetime(year, month, 1, tzinfo=dt.timezone.utc)
            else:
                return None
        except (ValueError, IndexError):
            return None

    def _infer_frequency(self, info: dict[str, Any]) -> str:
        """Infer frequency code from FRED series info.

        Returns single-char code: 'D', 'M', 'Q', 'A'.
        """
        freq = str(info.get("frequency", info.get("frequency_short", ""))).lower()
        if "daily" in freq or freq == "d":
            return "D"
        elif "monthly" in freq or freq == "m":
            return "M"
        elif "quarterly" in freq or freq == "q":
            return "Q"
        elif "annual" in freq or "yearly" in freq or freq == "a":
            return "A"
        return "Q"  # Default to quarterly

    async def ingest_fred_series(self, series_id: str) -> int:
        """Fetch and store a single FRED series.

        Args:
            series_id: FRED series identifier.

        Returns:
            Number of observations stored.
        """
        logger.info("ingest_fred_start", series_id=series_id)

        data, info_raw = await self.fred_client.fetch_series_async(series_id)

        # Convert info to dict if it's a pandas Series
        if isinstance(info_raw, pd.Series):
            info = info_raw.to_dict()
        elif isinstance(info_raw, dict):
            info = info_raw
        else:
            info = {"id": series_id}

        # Upsert metadata FIRST (required for foreign key constraint)
        await self._upsert_metadata(
            series_id=series_id,
            source="FRED",
            name=str(info.get("title", info.get("name", series_id))),
            frequency=self._infer_frequency(info),
            units=info.get("units"),
            seasonal_adjustment=info.get("seasonal_adjustment"),
            observation_count=0,  # Will be updated after storing observations
        )

        # Store observations AFTER metadata exists
        count = await self._store_observations(series_id, data)

        # Update observation count in metadata
        await self._upsert_metadata(
            series_id=series_id,
            source="FRED",
            name=str(info.get("title", info.get("name", series_id))),
            frequency=self._infer_frequency(info),
            units=info.get("units"),
            seasonal_adjustment=info.get("seasonal_adjustment"),
            observation_count=count,
        )

        logger.info("fred_fetch_success", series_id=series_id, count=count)
        return count

    async def ingest_bea_table(self, table_name: str) -> int:
        """Fetch and store a single BEA table.

        Args:
            table_name: BEA table name code.

        Returns:
            Number of observations stored.
        """
        logger.info("ingest_bea_start", table_name=table_name)

        data = self.bea_client.fetch_nipa_table(table_name)
        count = await self._store_bea_observations(table_name, data)

        logger.info("ingest_bea_complete", table_name=table_name, count=count)
        return count

    async def ingest_all(self) -> IngestionResult:
        """Run full ingestion for all configured series and tables.

        Errors on individual series do not abort the pipeline. Failed
        series are recorded in the result with error messages.

        Returns:
            IngestionResult with counts and error details.
        """
        result = IngestionResult()

        # Get FRED series from config
        fred_config = self.config.get("fred", {})
        if isinstance(fred_config, list):
            # YAML format: list of {id, name, ...}
            fred_series = [s["id"] for s in fred_config]
        elif isinstance(fred_config, dict):
            # Test fixture format: {series: [{id, name, ...}]}
            fred_series = [s["id"] for s in fred_config.get("series", [])]
        else:
            fred_series = []

        total = len(fred_series)
        self._notify_progress({"event": "start", "total_series": total})

        # Ingest FRED series
        for i, series_id in enumerate(fred_series):
            try:
                count = await self.ingest_fred_series(series_id)
                # Commit after each successful series to isolate failures
                await self.session.commit()
                result.series_processed += 1
                result.observations_upserted += count
                self._notify_progress({
                    "event": "progress",
                    "series_id": series_id,
                    "status": "ok",
                    "current": i + 1,
                    "total": total,
                })
            except Exception as e:
                result.series_failed += 1
                result.errors[series_id] = str(e)
                logger.error(
                    "ingest_fred_error",
                    series_id=series_id,
                    error=str(e),
                )
                # Rollback to clear the failed transaction state
                await self.session.rollback()
                # Set metadata error status in a new transaction
                try:
                    await self._set_error_status(series_id, str(e))
                    await self.session.commit()
                except Exception:
                    await self.session.rollback()
                self._notify_progress({
                    "event": "progress",
                    "series_id": series_id,
                    "status": "error",
                    "error": str(e),
                    "current": i + 1,
                    "total": total,
                })

        # Ingest BEA tables
        bea_config = self.config.get("bea", {})
        if isinstance(bea_config, dict):
            bea_tables = bea_config.get("tables", [])
            # Also check YAML format
            if not bea_tables:
                nipa = bea_config.get("nipa", [])
                fa = bea_config.get("fixed_assets", [])
                bea_tables = [
                    {"id": t.get("table", t.get("id")), "dataset": "NIPA"}
                    for t in nipa
                ] + [
                    {"id": t.get("table", t.get("id")), "dataset": "FixedAssets"}
                    for t in fa
                ]
        else:
            bea_tables = []

        for table_entry in bea_tables:
            table_id = table_entry.get("id", table_entry.get("table", ""))
            try:
                dataset = table_entry.get("dataset", "NIPA")
                if dataset == "FixedAssets":
                    data = self.bea_client.fetch_fixed_assets(table_id)
                    count = await self._store_bea_observations(table_id, data)
                else:
                    count = await self.ingest_bea_table(table_id)
                # Commit after each successful table
                await self.session.commit()
                result.series_processed += 1
                result.observations_upserted += count
            except Exception as e:
                result.series_failed += 1
                result.errors[table_id] = str(e)
                logger.error(
                    "ingest_bea_error",
                    table_id=table_id,
                    error=str(e),
                )
                # Rollback to clear the failed transaction state
                await self.session.rollback()

        self._notify_progress({"event": "complete", "result": result.to_dict()})

        logger.info(
            "ingest_all_complete",
            processed=result.series_processed,
            failed=result.series_failed,
            observations=result.observations_upserted,
        )
        return result

    async def _set_error_status(self, series_id: str, error: str) -> None:
        """Set fetch_status='error' on a series metadata record."""
        result = await self.session.execute(
            select(SeriesMetadata).where(SeriesMetadata.series_id == series_id)
        )
        metadata = result.scalar_one_or_none()
        result.close()  # Explicitly close result to free connection
        if metadata:
            metadata.fetch_status = "error"
            metadata.fetch_error = error
            await self.session.flush()

    # Alias for compatibility
    run_full_fetch = ingest_all
