  import asyncio
  import sys
  sys.path.insert(0, "/app")

  async def test():
      from ecpm.database import async_session
      from ecpm.indicators.computation import _fetch_series_from_db, _FINANCIAL_INDICATOR_MAPPINGS

      async with async_session() as db:
          slug = "debt_service_ratio"
          mapping = _FINANCIAL_INDICATOR_MAPPINGS[slug]
          series_ids = ["BOGZ1FU106130001Q", "A445RC1Q027SBEA"]

          data = await _fetch_series_from_db(series_ids, db, key_mapping=mapping)

          print("RAW DATA ANALYSIS:")
          print("="*60)

          for key, series in data.items():
              print(f"\n{key}:")
              print(f"  Total observations: {len(series)}")
              print(f"  Non-null observations: {series.notna().sum()}")
              print(f"  Null observations: {series.isna().sum()}")
              print(f"  Date range: {series.index.min()} to {series.index.max()}")

              non_null = series.dropna()
              if len(non_null) > 0:
                  print(f"  First 3 non-null values:")
                  for date, val in non_null.head(3).items():
                      print(f"    {date}: {val}")
                  print(f"  Last 3 non-null values:")
                  for date, val in non_null.tail(3).items():
                      print(f"    {date}: {val}")

          # Now try the computation manually
          print("\n" + "="*60)
          print("MANUAL COMPUTATION:")
          print("="*60)

          debt_service = data["debt_service"] / 1000.0
          corporate_income = data["corporate_income"]

          print(f"\nAfter unit conversion:")
          print(f"  debt_service non-null: {debt_service.notna().sum()}")
          print(f"  corporate_income non-null: {corporate_income.notna().sum()}")

          import pandas as pd
          aligned = pd.DataFrame({
              "debt": debt_service,
              "income": corporate_income
          }).dropna()

          print(f"\nAligned data (both non-null):")
          print(f"  Rows with both values: {len(aligned)}")
          if len(aligned) > 0:
              print(f"  Sample aligned rows:")
              print(aligned.head(3))
              print(f"\n  Latest aligned rows:")
              print(aligned.tail(3))

              result = (aligned["debt"] / aligned["income"]) * 100
              print(f"\n  Computed ratios (first 3): {result.head(3).tolist()}")
              print(f"  Computed ratios (last 3): {result.tail(3).tolist()}")
          else:
              print("  ERROR: No overlapping dates with both values!")

  asyncio.run(test())
  EOF
  
