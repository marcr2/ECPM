#!/bin/bash
echo "=== Fixing Capital Series (K1PTOTL1ES000) ==="
echo ""

echo "Step 1: Add new series to database..."
curl -X POST "http://localhost:8000/api/data/fetch" \
  -H "Content-Type: application/json" \
  -d '{"series_ids": ["K1PTOTL1ES000"]}' 2>&1 | head -20
echo ""

echo "Step 2: Clearing Redis cache..."
docker-compose exec -T redis redis-cli FLUSHALL
echo "✓ Cache cleared"
echo ""

echo "Step 3: Rebuilding and restarting backend..."
docker-compose build backend
docker-compose restart backend
echo "✓ Backend restarted"
echo ""

echo "Waiting for backend to be healthy..."
sleep 5

echo ""
echo "Step 4: Verifying new series..."
curl -s "http://localhost:8000/api/data/series/K1PTOTL1ES000" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(f\"✓ K1PTOTL1ES000: {d['metadata']['observation_count']} observations\")
    print(f\"  Status: {d['metadata']['fetch_status']}\")
except Exception as e:
    print(f\"✗ Error: {e}\")
"
echo ""

echo "Step 5: Testing indicators..."
curl -s "http://localhost:8000/api/indicators/rate_of_profit" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(f\"✓ Rate of Profit: {len(d['data'])} data points\")
    if d['latest_value']:
        print(f\"  Latest value: {d['latest_value']:.4f} ({d['latest_date'][:10]})\")
    else:
        print(\"  No valid data points (check if C series has data)\")
except Exception as e:
    print(f\"✗ Error: {e}\")
"

echo ""
echo "=== Fix Complete ==="
