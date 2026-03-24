#!/bin/bash
echo "=== Testing Indicator Math Fixes ==="
echo ""

echo "Step 1: Clearing Redis cache..."
docker-compose exec -T redis redis-cli FLUSHALL >/dev/null 2>&1
echo "✓ Cache cleared"
echo ""

echo "Step 2: Rebuilding backend..."
docker-compose build backend >/dev/null 2>&1
echo "✓ Backend rebuilt"
echo ""

echo "Step 3: Restarting backend..."
docker-compose restart backend >/dev/null 2>&1
echo "✓ Backend restarted"
echo ""

echo "Waiting for backend to be healthy..."
sleep 5

echo ""
echo "Step 4: Testing indicators with corrected math..."
echo ""

echo "Rate of Profit:"
curl -s "http://localhost:8000/api/indicators/rate_of_profit?methodology=shaikh-tonak" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if d.get('latest_value'):
        val = d['latest_value']
        pct = val * 100
        print(f'  Latest value: {val:.6f} ({pct:.2f}%)')
        print(f'  Date: {d[\"latest_date\"][:10]}')
        print(f'  Data points: {len(d[\"data\"])}')
        if 0.05 < val < 0.25:
            print(f'  ✓ REALISTIC (5-25% is expected range)')
        else:
            print(f'  ⚠ May need review (expected 5-25%)')
    else:
        print(f'  ✗ No data')
except Exception as e:
    print(f'  ✗ Error: {e}')
"
echo ""

echo "Organic Composition of Capital (OCC):"
curl -s "http://localhost:8000/api/indicators/occ?methodology=shaikh-tonak" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if d.get('latest_value'):
        val = d['latest_value']
        print(f'  Latest value: {val:.2f}')
        print(f'  Date: {d[\"latest_date\"][:10]}')
        if 3 < val < 10:
            print(f'  ✓ REALISTIC (3-10 is expected range)')
        else:
            print(f'  ⚠ May need review (expected 3-10)')
    else:
        print(f'  ✗ No data')
except Exception as e:
    print(f'  ✗ Error: {e}')
"
echo ""

echo "Rate of Surplus Value:"
curl -s "http://localhost:8000/api/indicators/rate_of_surplus_value?methodology=shaikh-tonak" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if d.get('latest_value'):
        val = d['latest_value']
        pct = val * 100
        print(f'  Latest value: {val:.4f} ({pct:.1f}%)')
        print(f'  Date: {d[\"latest_date\"][:10]}')
        if 0.5 < val < 1.5:
            print(f'  ✓ REALISTIC (50-150% is expected range)')
        else:
            print(f'  ⚠ May need review (expected 50-150%)')
    else:
        print(f'  ✗ No data')
except Exception as e:
    print(f'  ✗ Error: {e}')
"
echo ""

echo "Mass of Profit:"
curl -s "http://localhost:8000/api/indicators/mass_of_profit?methodology=shaikh-tonak" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if d.get('latest_value'):
        val = d['latest_value']
        print(f'  Latest value: \${val:.2f} billions')
        print(f'  Date: {d[\"latest_date\"][:10]}')
        if val > 0:
            print(f'  ✓ POSITIVE (as expected)')
        else:
            print(f'  ✗ NEGATIVE (should be positive!)')
    else:
        print(f'  ✗ No data')
except Exception as e:
    print(f'  ✗ Error: {e}')
"
echo ""

echo "=== Test Complete ==="
