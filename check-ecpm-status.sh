#!/bin/bash
# ECPM Status Checker

echo "=== ECPM System Status Check ==="
echo ""

echo "1. Docker Containers:"
docker-compose ps
echo ""

echo "2. Database Connection & Data:"
docker-compose exec timescaledb psql -U ecpm -d ecpm -c "
SELECT 
  'Total Observations' as metric, 
  COUNT(*)::text as value 
FROM observations
UNION ALL
SELECT 
  'Unique Series', 
  COUNT(DISTINCT series_id)::text 
FROM observations
UNION ALL
SELECT 
  'Date Range',
  MIN(observation_date)::text || ' to ' || MAX(observation_date)::text
FROM observations;
"
echo ""

echo "3. Backend API Endpoints:"
echo -n "  Health: "
curl -s http://localhost:8000/health | python3 -m json.tool || echo "FAILED"

echo -n "  Methodology (no DB): "
curl -s http://localhost:8000/api/indicators/methodology 2>&1 | head -c 50 | grep -q "shaikh-tonak" && echo "OK" || echo "FAILED"

echo -n "  Overview (needs DB): "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/indicators/)
if [ "$STATUS" = "200" ]; then
  echo "OK (200)"
else
  echo "FAILED ($STATUS)"
fi

echo -n "  Rate of Profit (needs DB): "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/indicators/rate_of_profit?methodology=shaikh-tonak")
if [ "$STATUS" = "200" ]; then
  echo "OK (200)"
else
  echo "FAILED ($STATUS)"
fi

echo ""
echo "4. Frontend:"
echo -n "  Next.js: "
curl -s http://localhost:3000 2>&1 | head -c 50 | grep -q "DOCTYPE\|html" && echo "OK" || echo "FAILED"

echo ""
echo "=== Check Complete ==="
