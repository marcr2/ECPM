  import asyncio
  import sys
  sys.path.insert(0, '/app')

  async def test():
      from ecpm.database import async_session
      from ecpm.indicators.computation import _fetch_series_from_db, _FINANCIAL_INDICATOR_MAPPINGS
      import pandas as pd

      async with async_session() as db:
          mapping = _FINANCIAL_INDICATOR_MAPPINGS['debt_service_ratio']
          print('Mapping:', mapping)

          data = await _fetch_series_from_db(['BOGZ1FU106130001Q', 'A445RC1Q027SBEA'], db, key_mapping=mapping)

          for key, series in data.items():
              print(f'{key}: {len(series)} total, {series.notna().sum()} non-null')

          debt = data['debt_service'] / 1000.0
          income = data['corporate_income']

          aligned = pd.DataFrame({'d': debt, 'i': income}).dropna()
          print(f'Aligned rows: {len(aligned)}')

          if len(aligned) > 0:
              result = (aligned['d'] / aligned['i']) * 100
              print(f'Sample results: {result.head(3).tolist()}')

  asyncio.run(test())
  EOF
