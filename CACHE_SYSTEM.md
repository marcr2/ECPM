# ECPM Indicator Caching System

## Overview

The ECPM backend uses a **disk-based caching system** to store pre-computed indicator results. This dramatically improves API response times by avoiding expensive recomputation on every request.

## How It Works

### 1. Daily Automatic Refresh

The system automatically refreshes the cache once per day via Celery Beat:

```
06:00 AM - Data refresh (fetch latest FRED/BEA data)
06:03 AM - Cache refresh (compute all indicators)
06:10 AM - Model retrain (update forecasting models)
```

The cache refresh runs **3 minutes after data refresh** to ensure the latest data is incorporated.

### 2. Cache Storage

Computed indicators are stored as JSON files in a Docker volume:

```
/app/cache/indicators/
├── shaikh-tonak/
│   ├── _overview.json          # Overview summary for all indicators
│   ├── rate_of_profit.json     # Individual indicator data
│   ├── occ.json
│   └── ...
└── kliman/
    ├── _overview.json
    ├── rate_of_profit.json
    └── ...
```

Each cache file includes:
- `cached_at`: Timestamp of when the data was computed
- `data`: The actual indicator data (time series, metadata, etc.)
- `methodology`: Which methodology was used
- `slug`: Indicator identifier

### 3. Cache TTL (Time-To-Live)

Cache files are valid for **24 hours**. After that:
- API endpoints will recompute on-demand
- Next scheduled refresh will update the cache

### 4. API Behavior

When you request indicator data:

1. **Check disk cache** - If valid (< 24 hours old), return cached data instantly
2. **Fallback to compute** - If cache miss/expired, compute on-demand and cache result
3. **No double work** - Redis is no longer used for indicator caching

## Manual Operations

### Refresh Cache Manually

**Via API:**
```bash
curl -X POST http://localhost:8000/api/cache/refresh
```

**Via Script:**
```bash
docker compose exec backend python scripts/refresh_cache.py
```

**Via Python:**
```python
from ecpm.tasks.cache_tasks import run_precompute_sync
results = run_precompute_sync()
print(results)
```

### Invalidate Cache

Delete cached files to force recomputation:

```bash
# Invalidate all cache
curl -X POST http://localhost:8000/api/cache/invalidate

# Invalidate specific methodology
curl -X POST "http://localhost:8000/api/cache/invalidate?methodology=shaikh-tonak"

# Invalidate specific indicator
curl -X POST "http://localhost:8000/api/cache/invalidate?methodology=shaikh-tonak&slug=rate_of_profit"
```

## Cache Directory Location

The cache is stored in a **Docker named volume** called `indicator_cache`:

```yaml
volumes:
  indicator_cache:  # Persists across container restarts
```

To inspect the cache:
```bash
docker compose exec backend ls -lh /app/cache/indicators/shaikh-tonak/
```

## Performance Impact

### Before (Redis TTL caching):
- Cold request: ~2-5 seconds (compute on-demand)
- Warm request: ~100-300ms (from Redis)
- Cache invalidated every hour

### After (Disk-based daily caching):
- Cold request (cache miss): ~2-5 seconds (compute on-demand, then cached)
- Warm request: **~10-50ms** (direct file read)
- Cache refreshed once daily
- **No computation during user requests** (pre-computed overnight)

## Configuration

Cache settings in `ecpm/cache_manager.py`:

```python
CACHE_DIR = Path("/app/cache/indicators")  # Cache directory
CACHE_TTL_HOURS = 24                       # Cache validity period
```

Schedule settings in `.env`:

```bash
FETCH_SCHEDULE_HOUR=6      # 6 AM US/Eastern
FETCH_SCHEDULE_MINUTE=0    # On the hour
```

## Troubleshooting

### Cache not updating

Check Celery Beat logs:
```bash
docker compose logs celery_beat -f
```

Manually trigger refresh:
```bash
curl -X POST http://localhost:8000/api/cache/refresh
```

### Old data showing

Check cache file timestamp:
```bash
docker compose exec backend cat /app/cache/indicators/shaikh-tonak/_overview.json | jq '.cached_at'
```

Invalidate and refresh:
```bash
curl -X POST http://localhost:8000/api/cache/invalidate
curl -X POST http://localhost:8000/api/cache/refresh
```

### Disk space concerns

Cache files are small (~50-200KB per indicator). Total cache size is typically < 10MB.

To clear old cache:
```bash
docker compose exec backend rm -rf /app/cache/indicators/*
```

## Migration Notes

When deploying this update:

1. **Restart all services** to apply code changes:
   ```bash
   docker compose restart
   ```

2. **Run initial cache population**:
   ```bash
   curl -X POST http://localhost:8000/api/cache/refresh
   ```

3. **Verify cache created**:
   ```bash
   docker compose exec backend ls /app/cache/indicators/
   ```

The old Redis cache will continue to exist but won't be used for indicators. You can safely flush Redis if needed:
```bash
docker compose exec redis redis-cli FLUSHALL
```
