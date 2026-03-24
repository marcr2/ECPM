#!/bin/bash
echo "Restarting backend to apply code changes..."
docker-compose restart backend
echo "Waiting for backend to be healthy..."
sleep 3
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""
echo "Testing indicators endpoint..."
curl -s "http://localhost:8000/api/indicators/rate_of_profit" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(f'✓ Rate of Profit: {len(d[\"data\"])} data points')
    print(f'  Latest value: {d[\"latest_value\"]}')
    print(f'  Latest date: {d[\"latest_date\"]}')
except Exception as e:
    print(f'✗ Error: {e}')
"
