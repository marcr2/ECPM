"""CLI entry point for ECPM: python -m ecpm.

Supports:
    python -m ecpm fetch           -- Fetch all configured series
    python -m ecpm fetch --series GDPC1  -- Fetch a specific series
"""

from __future__ import annotations

import argparse
import asyncio
import sys

import structlog

from ecpm.core.logging import setup_logging

logger = structlog.get_logger()


def main() -> None:
    """Parse CLI arguments and dispatch subcommands."""
    setup_logging()

    parser = argparse.ArgumentParser(
        prog="ecpm",
        description="Economic Crisis Prediction Model CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    # fetch subcommand
    fetch_parser = subparsers.add_parser("fetch", help="Trigger data fetch")
    fetch_parser.add_argument(
        "--series",
        type=str,
        default=None,
        help="Specific series ID to fetch (default: all)",
    )
    fetch_parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to series_config.yaml (default: auto-detect)",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "fetch":
        asyncio.run(_run_fetch(series_id=args.series, config_path=args.config))


async def _run_fetch(
    series_id: str | None = None,
    config_path: str | None = None,
) -> None:
    """Execute the data fetch command.

    If series_id is provided, fetches only that series.
    Otherwise, runs the full ingestion pipeline.
    """
    from ecpm.config import get_settings
    from ecpm.database import async_session
    from ecpm.ingestion.bea_client import BEAClient
    from ecpm.ingestion.fred_client import FredClient
    from ecpm.ingestion.pipeline import IngestionPipeline
    from ecpm.ingestion.series_config import load_series_config

    settings = get_settings()

    if not settings.fred_api_key:
        logger.error("missing_fred_api_key", hint="Set FRED_API_KEY in .env")
        print("Error: FRED_API_KEY not set. Add it to your .env file.")
        sys.exit(1)

    if not settings.bea_api_key:
        logger.error("missing_bea_api_key", hint="Set BEA_API_KEY in .env")
        print("Error: BEA_API_KEY not set. Add it to your .env file.")
        sys.exit(1)

    config = load_series_config(config_path)
    fred_client = FredClient(api_key=settings.fred_api_key)
    bea_client = BEAClient(api_key=settings.bea_api_key)

    async with async_session() as session:
        pipeline = IngestionPipeline(
            session=session,
            fred_client=fred_client,
            bea_client=bea_client,
            config=config,
        )

        if series_id:
            print(f"Fetching series: {series_id}")
            try:
                count = await pipeline.ingest_fred_series(series_id)
                await session.commit()
                print(f"Success: {count} observations stored for {series_id}")
            except Exception as e:
                logger.error("fetch_error", series_id=series_id, error=str(e))
                print(f"Error fetching {series_id}: {e}")
                sys.exit(1)
        else:
            print("Starting full data fetch...")
            result = await pipeline.ingest_all()
            await session.commit()
            print(
                f"Complete: {result.series_processed} series processed, "
                f"{result.series_failed} failed, "
                f"{result.observations_upserted} observations stored"
            )
            if result.errors:
                print("\nErrors:")
                for sid, err in result.errors.items():
                    print(f"  {sid}: {err}")


if __name__ == "__main__":
    main()
