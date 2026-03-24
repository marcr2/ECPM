#!/usr/bin/env python3
"""Test computation with actual real data."""
import asyncio
import sys
sys.path.insert(0, '/app')

async def test_real_computation():
    from ecpm.database import async_session
    from ecpm.indicators.computation import (
        _get_required_series_ids,
        _fetch_series_from_db,
        _FINANCIAL_INDICATOR_MAPPINGS,
        _is_financial_indicator
    )
    from ecpm.indicators.registry import MethodologyRegistry
    from ecpm.indicators.financial import compute_credit_gdp_gap, compute_debt_service_ratio

    async with async_session() as db:
        # Test credit-GDP gap with real data
        print("=" * 60)
        print("CREDIT-GDP GAP WITH REAL DATA")
        print("=" * 60)

        slug = "credit_gdp_gap"
        mapper = MethodologyRegistry.get("shaikh-tonak")
        series_ids = _get_required_series_ids(slug, mapper)
        mapping = _FINANCIAL_INDICATOR_MAPPINGS[slug]
        data = await _fetch_series_from_db(series_ids, db, key_mapping=mapping)

        print(f"Data keys: {list(data.keys())}")

        # Show what we're passing to the function
        credit = data["credit_total"]
        gdp = data["nominal_gdp"]

        print(f"\nBefore computation:")
        print(f"  credit_total length: {len(credit)}, non-null: {credit.notna().sum()}")
        print(f"  nominal_gdp length: {len(gdp)}, non-null: {gdp.notna().sum()}")
        print(f"  credit_total sample: {credit.dropna().head(3).tolist()}")
        print(f"  nominal_gdp sample: {gdp.dropna().head(3).tolist()}")

        # Step through computation manually
        print(f"\nStep 1: Unit conversion")
        credit_converted = credit / 1000.0
        print(f"  credit_converted (first 3 non-null): {credit_converted.dropna().head(3).tolist()}")

        print(f"\nStep 2: Compute ratio")
        ratio = (credit_converted / gdp) * 100
        print(f"  ratio length: {len(ratio)}, non-null: {ratio.notna().sum()}")
        print(f"  ratio (first 5 non-null): {ratio.dropna().head(5).tolist()}")
        print(f"  ratio (last 5 non-null): {ratio.dropna().tail(5).tolist()}")

        print(f"\nStep 3: Apply HP filter")
        try:
            from ecpm.indicators.base import _one_sided_hp_filter
            import pandas as pd
            trend = _one_sided_hp_filter(ratio.values, lamb=400_000)
            print(f"  trend length: {len(trend)}")
            print(f"  trend (first 5): {trend[:5].tolist()}")
            gap = ratio - pd.Series(trend, index=ratio.index)
            print(f"  gap length: {len(gap)}, non-null: {gap.notna().sum()}")
            print(f"  gap (first 5 non-null): {gap.dropna().head(5).tolist()}")
            print(f"  gap (last 5 non-null): {gap.dropna().tail(5).tolist()}")
        except Exception as e:
            print(f"  HP filter error: {e}")
            import traceback
            traceback.print_exc()

        # Now test with the actual function
        print(f"\nCalling compute_credit_gdp_gap function:")
        result = compute_credit_gdp_gap(data)
        print(f"  Result length: {len(result)}, non-null: {result.notna().sum()}")
        print(f"  Result (first 5 non-null): {result.dropna().head(5).tolist()}")
        print(f"  Result (last 5 non-null): {result.dropna().tail(5).tolist()}")

        # Test debt service ratio
        print("\n" + "=" * 60)
        print("DEBT SERVICE RATIO WITH REAL DATA")
        print("=" * 60)

        slug = "debt_service_ratio"
        series_ids = _get_required_series_ids(slug, mapper)
        mapping = _FINANCIAL_INDICATOR_MAPPINGS[slug]
        data = await _fetch_series_from_db(series_ids, db, key_mapping=mapping)

        debt = data["debt_service"]
        income = data["corporate_income"]

        print(f"\nBefore computation:")
        print(f"  debt_service length: {len(debt)}, non-null: {debt.notna().sum()}")
        print(f"  corporate_income length: {len(income)}, non-null: {income.notna().sum()}")

        # Manual computation
        debt_converted = debt / 1000.0
        ratio = (debt_converted / income) * 100
        print(f"\nManual computation:")
        print(f"  ratio length: {len(ratio)}, non-null: {ratio.notna().sum()}")
        print(f"  ratio (first 5 non-null): {ratio.dropna().head(5).tolist()}")
        print(f"  ratio (last 5 non-null): {ratio.dropna().tail(5).tolist()}")

        # Function call
        result = compute_debt_service_ratio(data)
        print(f"\nFunction result:")
        print(f"  Result length: {len(result)}, non-null: {result.notna().sum()}")
        print(f"  Result (first 5 non-null): {result.dropna().head(5).tolist()}")
        print(f"  Result (last 5 non-null): {result.dropna().tail(5).tolist()}")

if __name__ == "__main__":
    asyncio.run(test_real_computation())
