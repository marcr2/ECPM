import asyncio
from sqlalchemy import select, func
import sys
sys.path.insert(0, '/home/marcellinor/Desktop/ECPM/backend')

from ecpm.database import get_async_session
from ecpm.models.observation import Observation

async def check_series():
    async for db in get_async_session():
        print("Checking required series for credit-to-GDP gap:")
        for series_id in ['BOGZ1FL073164003Q', 'GDP']:
            stmt = select(func.count(Observation.value)).where(Observation.series_id == series_id)
            result = await db.execute(stmt)
            count = result.scalar()
            print(f'  {series_id}: {count} observations')
        
        print("\nChecking required series for debt service ratio:")
        for series_id in ['BOGZ1FU106130001Q', 'A445RC1Q027SBEA']:
            stmt = select(func.count(Observation.value)).where(Observation.series_id == series_id)
            result = await db.execute(stmt)
            count = result.scalar()
            print(f'  {series_id}: {count} observations')
        
        print("\nSample of available series:")
        stmt = select(Observation.series_id, func.count(Observation.value)).group_by(Observation.series_id).limit(10)
        result = await db.execute(stmt)
        for row in result.all():
            print(f'  {row[0]}: {row[1]} observations')
        break

asyncio.run(check_series())
