#!/usr/bin/env python3
"""Run data ingestion pipeline manually."""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, '/app')

async def main():
    from ecpm.tasks.fetch_tasks import _run_pipeline
    result = await _run_pipeline()
    print("\n=== Ingestion Complete ===")
    print(f"Series processed: {result.get('series_processed', 0)}")
    print(f"Series failed: {result.get('series_failed', 0)}")
    print(f"Total observations: {result.get('total_observations', 0)}")
    return result

if __name__ == "__main__":
    asyncio.run(main())
