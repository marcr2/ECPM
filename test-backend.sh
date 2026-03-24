#!/bin/bash
echo "=== Testing Overview Endpoint ==="
curl -s "http://localhost:8000/api/indicators/?methodology=shaikh-tonak" | jq '.indicators[] | {slug, latest_value, trend}'

echo -e "\n=== Testing Individual OCC Endpoint ==="
curl -s "http://localhost:8000/api/indicators/occ" | jq '{slug, latest_value, latest_date, data_length: (.data | length)}'

echo -e "\n=== Backend Logs (last 50 lines) ==="
docker compose logs backend --tail=50 2>&1 | grep -E "computation\.|indicators\." | tail -20
