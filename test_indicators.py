#!/usr/bin/env python3
"""Test indicator computation directly."""
import asyncio
import sys
sys.path.insert(0, '/app')

async def test_indicators():
    from ecpm.database import async_session
    from ecpm.indicators.computation import compute_indicator

    async with async_session() as db:
        # Test credit-to-GDP gap
        print("Testing credit_gdp_gap...")
        try:
            result = await compute_indicator("credit_gdp_gap", "shaikh-tonak", db)
            print(f"  Series length: {len(result)}")
            if len(result) > 0:
                print(f"  Latest value: {result.iloc[-1]}")
                print(f"  Latest date: {result.index[-1]}")
                print(f"  First 3 values: {result.head(3).tolist()}")
            else:
                print("  ERROR: Empty result!")
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

        print("\nTesting debt_service_ratio...")
        try:
            result = await compute_indicator("debt_service_ratio", "shaikh-tonak", db)
            print(f"  Series length: {len(result)}")
            if len(result) > 0:
                print(f"  Latest value: {result.iloc[-1]}")
                print(f"  Latest date: {result.index[-1]}")
                print(f"  First 3 values: {result.head(3).tolist()}")
            else:
                print("  ERROR: Empty result!")
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_indicators())
