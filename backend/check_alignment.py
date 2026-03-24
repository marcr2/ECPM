#!/usr/bin/env python3
"""Check date alignment of real data."""
import asyncio
import sys
sys.path.insert(0, '/app')

async def check_alignment():
    from ecpm.database import async_session
    from ecpm.indicators.computation import (
        _get_required_series_ids,
        _fetch_series_from_db,
        _FINANCIAL_INDICATOR_MAPPINGS,
        _is_financial_indicator
    )
    from ecpm.indicators.registry import MethodologyRegistry

    async with async_session() as db:
        # Credit-GDP gap
        print("=" * 60)
        print("CREDIT-TO-GDP GAP DATE ALIGNMENT")
        print("=" * 60)

        slug = "credit_gdp_gap"
        mapper = MethodologyRegistry.get("shaikh-tonak")
        series_ids = _get_required_series_ids(slug, mapper)
        mapping = _FINANCIAL_INDICATOR_MAPPINGS[slug]
        data = await _fetch_series_from_db(series_ids, db, key_mapping=mapping)

        credit = data["credit_total"]
        gdp = data["nominal_gdp"]

        print(f"Credit dates: {credit.index.min()} to {credit.index.max()}")
        print(f"GDP dates: {gdp.index.min()} to {gdp.index.max()}")

        # Find overlapping dates
        credit_non_null = credit.dropna()
        gdp_non_null = gdp.dropna()

        print(f"\nCredit non-null dates: {credit_non_null.index.min()} to {credit_non_null.index.max()} ({len(credit_non_null)} values)")
        print(f"GDP non-null dates: {gdp_non_null.index.min()} to {gdp_non_null.index.max()} ({len(gdp_non_null)} values)")

        # Check for common dates
        common_dates = credit_non_null.index.intersection(gdp_non_null.index)
        print(f"\nCommon non-null dates: {len(common_dates)}")
        if len(common_dates) > 0:
            print(f"  Range: {common_dates.min()} to {common_dates.max()}")
            print(f"  First 5: {common_dates[:5].tolist()}")
        else:
            print("  NO COMMON DATES!")
            print(f"\n  Credit first 5 dates: {credit_non_null.index[:5].tolist()}")
            print(f"  GDP first 5 dates: {gdp_non_null.index[:5].tolist()}")

        # Debt service ratio
        print("\n" + "=" * 60)
        print("DEBT SERVICE RATIO DATE ALIGNMENT")
        print("=" * 60)

        slug = "debt_service_ratio"
        series_ids = _get_required_series_ids(slug, mapper)
        mapping = _FINANCIAL_INDICATOR_MAPPINGS[slug]
        data = await _fetch_series_from_db(series_ids, db, key_mapping=mapping)

        debt = data["debt_service"]
        income = data["corporate_income"]

        print(f"Debt service dates: {debt.index.min()} to {debt.index.max()}")
        print(f"Corporate income dates: {income.index.min()} to {income.index.max()}")

        debt_non_null = debt.dropna()
        income_non_null = income.dropna()

        print(f"\nDebt service non-null dates: {debt_non_null.index.min()} to {debt_non_null.index.max()} ({len(debt_non_null)} values)")
        print(f"Corporate income non-null dates: {income_non_null.index.min()} to {income_non_null.index.max()} ({len(income_non_null)} values)")

        common_dates = debt_non_null.index.intersection(income_non_null.index)
        print(f"\nCommon non-null dates: {len(common_dates)}")
        if len(common_dates) > 0:
            print(f"  Range: {common_dates.min()} to {common_dates.max()}")
            print(f"  First 5: {common_dates[:5].tolist()}")
        else:
            print("  NO COMMON DATES!")
            print(f"\n  Debt first 5 dates: {debt_non_null.index[:5].tolist()}")
            print(f"  Income first 5 dates: {income_non_null.index[:5].tolist()}")

if __name__ == "__main__":
    asyncio.run(check_alignment())
