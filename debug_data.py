#!/usr/bin/env python3
"""Debug what data is being passed to indicator computations."""
import asyncio
import sys
sys.path.insert(0, '/app')

async def debug_data():
    from ecpm.database import async_session
    from ecpm.indicators.computation import (
        _get_required_series_ids,
        _fetch_series_from_db,
        _FINANCIAL_INDICATOR_MAPPINGS,
        _is_financial_indicator
    )
    from ecpm.indicators.registry import MethodologyRegistry

    async with async_session() as db:
        # Test credit-to-GDP gap
        print("=" * 60)
        print("CREDIT-TO-GDP GAP")
        print("=" * 60)

        slug = "credit_gdp_gap"
        mapper = MethodologyRegistry.get("shaikh-tonak")
        series_ids = _get_required_series_ids(slug, mapper)

        print(f"Required series IDs: {series_ids}")
        print(f"Is financial indicator: {_is_financial_indicator(slug)}")

        if _is_financial_indicator(slug):
            mapping = _FINANCIAL_INDICATOR_MAPPINGS[slug]
            print(f"Key mapping: {mapping}")

        data = await _fetch_series_from_db(series_ids, db, key_mapping=mapping if _is_financial_indicator(slug) else None)

        print(f"\nData dict keys: {list(data.keys())}")
        for key, series in data.items():
            print(f"\n  {key}:")
            print(f"    Length: {len(series)}")
            print(f"    Non-null count: {series.notna().sum()}")
            print(f"    First 3 values: {series.head(3).tolist()}")
            print(f"    Last 3 values: {series.tail(3).tolist()}")

        # Test debt service ratio
        print("\n" + "=" * 60)
        print("DEBT SERVICE RATIO")
        print("=" * 60)

        slug = "debt_service_ratio"
        series_ids = _get_required_series_ids(slug, mapper)

        print(f"Required series IDs: {series_ids}")
        print(f"Is financial indicator: {_is_financial_indicator(slug)}")

        if _is_financial_indicator(slug):
            mapping = _FINANCIAL_INDICATOR_MAPPINGS[slug]
            print(f"Key mapping: {mapping}")

        data = await _fetch_series_from_db(series_ids, db, key_mapping=mapping if _is_financial_indicator(slug) else None)

        print(f"\nData dict keys: {list(data.keys())}")
        for key, series in data.items():
            print(f"\n  {key}:")
            print(f"    Length: {len(series)}")
            print(f"    Non-null count: {series.notna().sum()}")
            print(f"    First 3 values: {series.head(3).tolist()}")
            print(f"    Last 3 values: {series.tail(3).tolist()}")

if __name__ == "__main__":
    asyncio.run(debug_data())
