#!/bin/bash
echo "=== ECPM Training Diagnostics ==="
echo ""

echo "1. Check if Celery worker can connect to database:"
docker compose exec celery_worker python -c "
from ecpm.database import async_session
from sqlalchemy import text
import asyncio

async def test():
    async with async_session() as session:
        result = await session.execute(text('SELECT 1'))
        print('✓ Database connection works')

asyncio.run(test())
" 2>&1

echo ""
echo "2. Check if worker can load one indicator:"
docker compose exec celery_worker python -c "
import asyncio
from ecpm.database import async_session
from ecpm.indicators.computation import compute_indicator

async def test():
    async with async_session() as session:
        series = await compute_indicator('rate_of_profit', 'shaikh-tonak', session, redis=None)
        print(f'✓ Loaded indicator with {len(series)} points')

asyncio.run(test())
" 2>&1

echo ""
echo "3. Trigger training and check logs:"
curl -s -X POST http://localhost:8000/api/forecasting/train
echo ""
echo ""
echo "Watch logs with: docker compose logs celery_worker -f"
