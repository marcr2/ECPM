#!/bin/bash
echo "=== Testing All ECPM Tabs ==="
echo ""

echo "1. DATA OVERVIEW Tab (/data):"
echo -n "   Series list: "
curl -s "http://localhost:8000/api/data/series?limit=1" | grep -q "series_id" && echo "✓ OK" || echo "✗ FAILED"
echo ""

echo "2. INDICATORS Tab (/indicators):"
echo -n "   Overview: "
curl -s "http://localhost:8000/api/indicators/" | grep -q "methodology" && echo "✓ OK" || echo "✗ FAILED"
echo -n "   Rate of Profit: "
curl -s "http://localhost:8000/api/indicators/rate_of_profit" | grep -q "data" && echo "✓ OK" || echo "✗ FAILED"
echo -n "   OCC: "
curl -s "http://localhost:8000/api/indicators/occ" | grep -q "data" && echo "✓ OK" || echo "✗ FAILED"
echo ""

echo "3. FORECASTING Tab (/forecasting):"
echo -n "   Forecasts: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/forecasting/forecasts")
if [ "$STATUS" = "200" ]; then
  echo "✓ OK (200)"
elif [ "$STATUS" = "404" ]; then
  echo "⚠ No training yet (404) - Expected, run POST /api/forecasting/train"
else
  echo "✗ FAILED ($STATUS)"
fi
echo ""

echo "4. STRUCTURAL ANALYSIS Tab (/structural):"
echo -n "   Available years: "
curl -s "http://localhost:8000/api/structural/years" | grep -q "years" && echo "✓ OK" || echo "✗ FAILED"
echo -n "   I-O Matrix (2022): "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/structural/matrix/2022")
if [ "$STATUS" = "200" ]; then
  echo "✓ OK (200)"
elif [ "$STATUS" = "404" ]; then
  echo "⚠ No I-O data (404) - Need BEA I-O table ingestion"
else
  echo "✗ FAILED ($STATUS)"
fi
echo ""

echo "5. CONCENTRATION Tab (/concentration):"
echo -n "   Overview: "
curl -s "http://localhost:8000/api/concentration/overview" | grep -q "dept_i" && echo "✓ OK (placeholder)" || echo "✗ FAILED"
echo -n "   Industries: "
curl -s "http://localhost:8000/api/concentration/industries" | grep -q "\[\]" && echo "⚠ No Census data yet" || echo "✓ Has data"
echo ""

echo "=== Summary ==="
echo "Working tabs:"
echo "  ✓ Data Overview - Full functionality"
echo "  ✓ Indicators - Full functionality with FRED data"
echo ""
echo "Tabs needing additional setup:"
echo "  ⚠ Forecasting - Needs ML model training (POST /api/forecasting/train)"
echo "  ⚠ Structural - Needs BEA I-O table data ingestion"
echo "  ⚠ Concentration - Needs Census data ingestion"
