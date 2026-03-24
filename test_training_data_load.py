#!/usr/bin/env python3
"""Test script to reproduce training data loading issue."""
import asyncio
import sys
sys.path.insert(0, 'backend')

async def test_load():
    """Test loading indicators the same way training does."""
    from ecpm.database import async_session
    from ecpm.indicators.computation import compute_indicator
    from ecpm.indicators.definitions import IndicatorSlug

    indicator_series = {}

    async with async_session() as session:
        for slug in IndicatorSlug:
            try:
                print(f"Loading {slug.value}...", end=" ")
                series = await compute_indicator(
                    slug.value, "shaikh-tonak", session, redis=None
                )
                if series is not None and len(series) > 0:
                    indicator_series[slug.value] = series
                    print(f"✓ ({len(series)} points)")
                else:
                    print(f"✗ (empty)")
            except Exception as e:
                print(f"✗ ERROR: {e}")
                import traceback
                traceback.print_exc()

    print(f"\nTotal indicators loaded: {len(indicator_series)}")
    if not indicator_series:
        print("❌ No indicator data available")
        return False
    else:
        print("✅ Data load successful")
        return True

if __name__ == "__main__":
    success = asyncio.run(test_load())
    sys.exit(0 if success else 1)
