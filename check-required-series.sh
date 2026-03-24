#!/bin/bash
echo "=== Checking Required FRED Series for Indicators ==="
echo ""

# Core series needed for Shaikh-Tonak methodology
REQUIRED_SERIES=(
  "A053RC1Q027SBEA"  # National income
  "A576RC1"          # Compensation
  "K1NTOTL1SI000"    # Net fixed assets (current)
  "K1NTOTL1HI000"    # Net fixed assets (historical)
)

echo "Core methodology series:"
for series in "${REQUIRED_SERIES[@]}"; do
  echo -n "  $series: "
  COUNT=$(docker-compose exec -T timescaledb psql -U ecpm -d ecpm -tAc "SELECT COUNT(*) FROM observations WHERE series_id='$series';" 2>/dev/null)
  if [ -n "$COUNT" ] && [ "$COUNT" -gt 0 ]; then
    echo "✓ $COUNT observations"
  else
    echo "✗ MISSING"
  fi
done

echo ""
echo "Financial indicator series:"
FINANCIAL_SERIES=(
  "OPHNFB"              # Output per hour
  "PRS85006092"         # Real compensation per hour
  "BOGZ1FL073164003Q"   # Credit/Financial assets
  "GDP"                 # GDP
  "BOGZ1FU106130001Q"   # Debt service
  "A445RC1Q027SBEA"     # Corporate income
)

for series in "${FINANCIAL_SERIES[@]}"; do
  echo -n "  $series: "
  COUNT=$(docker-compose exec -T timescaledb psql -U ecpm -d ecpm -tAc "SELECT COUNT(*) FROM observations WHERE series_id='$series';" 2>/dev/null)
  if [ -n "$COUNT" ] && [ "$COUNT" -gt 0 ]; then
    echo "✓ $COUNT observations"
  else
    echo "✗ MISSING"
  fi
done
