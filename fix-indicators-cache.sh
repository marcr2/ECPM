#!/bin/bash
echo "=== Fixing Indicators Cache Issue ==="
echo ""

echo "Step 1: Clearing Redis cache..."
docker-compose exec -T redis redis-cli FLUSHALL
echo "✓ Redis cache cleared"
echo ""

echo "Step 2: Rebuilding backend with fixes..."
docker-compose build backend
echo "✓ Backend rebuilt"
echo ""

echo "Step 3: Restarting backend..."
docker-compose restart backend
echo "✓ Backend restarted"
echo ""

echo "Waiting for backend to be healthy..."
sleep 5

echo ""
echo "Step 4: Testing indicators endpoint..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/indicators/")
if [ "$STATUS" = "200" ]; then
  echo "✓ Indicators overview: OK (200)"
  curl -s "http://localhost:8000/api/indicators/" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(f'  Found {len(d[\"indicators\"])} indicators')
    for ind in d['indicators'][:3]:
        print(f'  - {ind[\"slug\"]}: sparkline has {len(ind[\"sparkline\"])} points')
except Exception as e:
    print(f'  Error parsing response: {e}')
"
else
  echo "✗ Indicators overview: FAILED ($STATUS)"
fi

echo ""
echo "=== Fix Complete ==="
