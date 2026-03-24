# Deployment Steps for Disk-Based Caching System

## Changes Made

### Backend Files Created/Modified

**New Files:**
- `backend/ecpm/cache_manager.py` - Disk-based cache manager
- `backend/ecpm/tasks/cache_tasks.py` - Daily cache refresh tasks
- `backend/ecpm/api/cache.py` - Cache management API endpoints
- `backend/scripts/refresh_cache.py` - Manual cache refresh script
- `CACHE_SYSTEM.md` - Documentation

**Modified Files:**
- `backend/ecpm/api/indicators.py` - Uses disk cache instead of Redis
- `backend/ecpm/api/router.py` - Added cache router
- `backend/ecpm/tasks/celery_app.py` - Added daily cache refresh schedule
- `backend/ecpm/indicators/computation.py` - Fixed NaN handling in summaries
- `docker-compose.yml` - Added indicator_cache volume

**Root Scripts:**
- `refresh-cache.sh` - Quick cache refresh via API

### Frontend Files Modified

- `frontend/src/app/globals.css` - Brighter chart colors for dark theme
- `frontend/src/components/indicators/indicator-chart.tsx` - Better axis contrast
- `frontend/src/lib/indicators.ts` - Fixed slug format conversion
- `frontend/src/lib/forecast-api.ts` - Fixed slug format conversion
- `frontend/src/app/indicators/page.tsx` - Fixed overview slug matching
- `frontend/src/app/indicators/methodology/page.tsx` - Fixed column layout

## Deployment Steps

### 1. Stop Services

```bash
cd /home/marcellinor/Desktop/ECPM
docker compose down
```

### 2. Rebuild Containers

The backend Python code changes require rebuilding:

```bash
docker compose build backend celery_worker celery_beat
```

### 3. Start Services

```bash
docker compose up -d
```

### 4. Wait for Services to be Healthy

```bash
docker compose ps
```

Wait until all services show "healthy" status.

### 5. Initial Cache Population

Run the cache refresh to populate the cache for the first time:

```bash
./refresh-cache.sh
```

Or via curl:
```bash
curl -X POST http://localhost:8000/api/cache/refresh
```

This will take 2-5 minutes to compute all indicators for all methodologies.

### 6. Verify Cache Created

```bash
docker compose exec backend ls -lh /app/cache/indicators/
```

You should see directories for each methodology with JSON files inside.

### 7. Test Frontend

1. Open http://localhost:3000/indicators
2. You should see:
   - Actual values instead of "N/A"
   - Bright, visible chart colors
   - Fast page loads (<100ms for cached data)

3. Navigate to individual indicators
4. Check chart visibility

### 8. Hard Refresh Browser

Clear browser cache to get new CSS:
- Windows/Linux: Ctrl + Shift + R
- Mac: Cmd + Shift + R

## Verification Checklist

- [ ] Backend starts without errors
- [ ] Celery Beat is running and scheduled tasks are loaded
- [ ] Cache directory exists: `/app/cache/indicators/`
- [ ] Cache files are created: `_overview.json`, `rate_of_profit.json`, etc.
- [ ] API responds quickly: `curl http://localhost:8000/api/indicators/`
- [ ] Overview page shows actual values (not N/A)
- [ ] Charts are visible with bright colors
- [ ] Individual indicator pages load quickly

## Monitoring

### Check Celery Beat Schedule

```bash
docker compose logs celery_beat | grep "daily-cache-refresh"
```

### Check Cache File Ages

```bash
docker compose exec backend find /app/cache -name "*.json" -ls
```

### Check Cache Hit Rate

```bash
docker compose logs backend | grep "cache.disk_cache_hit"
```

### Manual Cache Refresh

```bash
# Via API
curl -X POST http://localhost:8000/api/cache/refresh

# Via script
docker compose exec backend python scripts/refresh_cache.py
```

## Rollback Plan

If issues occur, rollback by:

1. Stop services: `docker compose down`
2. Revert git changes: `git checkout HEAD~1`
3. Rebuild: `docker compose build`
4. Start: `docker compose up -d`

## Performance Expectations

**Before:**
- Overview page: 2-5 seconds (cold), 100-300ms (warm Redis)
- Individual indicator: 1-3 seconds (cold), 50-100ms (warm Redis)

**After:**
- Overview page: **10-50ms** (always cached)
- Individual indicator: **10-50ms** (always cached)
- Cache refresh: 2-5 minutes (runs once daily at 6:03 AM)

## Troubleshooting

### Cache not populating

Check backend logs:
```bash
docker compose logs backend -f
```

### Celery Beat not running

Check Beat service:
```bash
docker compose logs celery_beat -f
```

### Old data showing

Invalidate and refresh:
```bash
curl -X POST http://localhost:8000/api/cache/invalidate
curl -X POST http://localhost:8000/api/cache/refresh
```

### Charts still dark

Hard refresh browser cache (Ctrl+Shift+R)

Check CSS compiled:
```bash
docker compose logs frontend | grep globals.css
```
