# Phase 1: Foundation and Data Ingestion - Research

**Researched:** 2026-03-23
**Domain:** Docker Compose infrastructure, FRED/BEA data ingestion, FastAPI backend, Next.js frontend skeleton
**Confidence:** HIGH

## Summary

This phase establishes a greenfield Docker Compose stack with four containers (TimescaleDB, Redis, Python/FastAPI backend, Next.js frontend) and builds an automated data ingestion pipeline for FRED and BEA macroeconomic data. The Python ecosystem has mature, well-maintained libraries for both FRED (`fredapi`) and BEA (`beaapi` -- the official BEA library). TimescaleDB runs as a PostgreSQL extension in Docker and integrates cleanly with SQLAlchemy 2.0 async via asyncpg. Celery with Redis broker handles scheduled background fetches, and FastAPI provides SSE for streaming progress.

The stack is well-trodden territory -- FastAPI + Celery + Redis is the standard Python async task pattern, TimescaleDB is the standard time-series extension for PostgreSQL, and Next.js + shadcn/ui is the default React dashboard stack. The main complexity lies in correctly modeling the BEA NIPA table naming conventions, handling two different API rate limits (FRED: 120/min, BEA: 100/min), and designing a TimescaleDB schema that stores heterogeneous time-series at native frequencies with a vintage_date column for future revision tracking.

**Primary recommendation:** Use fredapi + beaapi (official libraries) for data retrieval, SQLAlchemy 2.0 async with asyncpg for database access, Celery beat for scheduling, tenacity for retry/backoff, and Alembic for migrations. Keep the schema simple: one hypertable for observations, one regular table for series metadata.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Shaikh/Tonak methodology drives series selection (most widely cited Marxist NIPA mapping)
- BEA NIPA tables to ingest: Corporate profits (Table 6.19), National income (Table 1.12), Fixed assets (FAT Tables), GDP by industry (Tables 1.3/1.15)
- Broad FRED coverage (~50-80 series): Phase 2 essentials plus GDP components, interest rates, money supply, unemployment, industrial production, housing
- Series list managed via configuration file (YAML/JSON), not hardcoded
- Store all series at native frequency (monthly/quarterly/annual) -- no implicit resampling
- Frequency alignment happens at query time with explicit strategy parameter
- Interpolation: LOCF only -- most conservative, no synthetic data points
- Gaps: flag explicitly with null values and metadata markers, do not interpolate across gaps
- Log warnings when gaps are detected during ingestion
- Vintage tracking: schema includes vintage_date column per DATA-09, but no ALFRED vintage retrieval pipeline
- Daily automatic re-fetch via Celery beat
- Manual trigger via POST /api/data/fetch and CLI (python -m ecpm fetch)
- API keys via .env file with .env.example template
- Structured JSON logging for all fetch attempts
- /api/data/status endpoint showing last fetch time, failures, next scheduled run
- Full navigation shell with sidebar placeholder links for all 5 phases (disabled/greyed out)
- Dark theme, data-dense aesthetic (Bloomberg Terminal / Grafana feel)
- Data overview page with full metadata table: Series ID, Name, Source, Frequency, Last Updated, Observation Count, Status -- sortable and searchable

### Claude's Discretion
- Exact TimescaleDB schema design (table structure, indexes, hypertable configuration)
- FastAPI project structure and endpoint naming conventions
- Next.js component library choice (shadcn/ui, etc.)
- Docker Compose networking and health check specifics
- Celery configuration details
- Redis caching strategy for API responses

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DATA-01 | Retrieve time-series data from FRED API with API key auth | fredapi library handles auth and retrieval; get_series() returns pandas Series |
| DATA-02 | Cache all retrieved FRED series in TimescaleDB | Hypertable schema with series_id + observation_date partitioning |
| DATA-03 | Ingest BEA NIPA tables (corporate profits, national income, fixed assets, GDP by industry) | beaapi official library; NIPA dataset + FixedAssets dataset; TableName format T{section}{subsection}{metric} |
| DATA-04 | Store series metadata (units, frequency, seasonality, source, last updated) | Separate metadata table with foreign key to observations hypertable |
| DATA-05 | Scheduled data fetches via Celery beat on configurable intervals | Celery beat with Redis broker; separate worker and beat containers |
| DATA-06 | Handle missing data with explicit interpolation and frequency alignment | LOCF at query time; null values stored as-is; metadata markers for gaps |
| DATA-07 | Store all series at native frequency without implicit resampling | Schema stores raw frequency; no transformation on ingestion |
| DATA-08 | Exponential backoff retry for API calls (FRED 120 req/min) | tenacity library with wait_exponential decorator |
| DATA-09 | Schema includes vintage_date column for future revision tracking | Column in observations table; nullable; no ALFRED pipeline yet |
| INFR-01 | Docker Compose with TimescaleDB, Redis, Python backend, Next.js frontend | Four-service compose file with health checks and volumes |
| INFR-02 | FastAPI REST endpoints for all data | SQLAlchemy 2.0 async + asyncpg; Pydantic v2 response models |
| INFR-03 | FastAPI SSE for streaming progress of long-running jobs | EventSourceResponse (built-in since FastAPI 0.135.0) or sse-starlette |
| INFR-04 | Redis caches expensive computations | redis-py async client; cache API responses with TTL |
| INFR-05 | Docker Compose health checks and separate dev/prod configs | Healthcheck commands per service; compose profiles or override files |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | >=0.115 | REST API framework | Async-native, Pydantic integration, SSE support, OpenAPI docs |
| SQLAlchemy | >=2.0 | ORM / database toolkit | Async support via asyncpg, mapped types, mature ecosystem |
| asyncpg | >=0.29 | PostgreSQL async driver | Fastest Python PostgreSQL driver, native async |
| Alembic | >=1.13 | Database migrations | Standard SQLAlchemy migration tool |
| Celery | >=5.4 | Task queue / scheduler | De facto Python task queue; beat for periodic tasks |
| fredapi | >=0.5 | FRED API client | Most widely used Python FRED client; pandas-native |
| beaapi | >=0.0.4 | BEA API client | Official BEA-maintained library; auto rate limiting |
| tenacity | >=8.2 | Retry with backoff | Decorator-based; exponential backoff, jitter, custom stop conditions |
| Pydantic | >=2.0 | Data validation / schemas | FastAPI's native validation layer; settings management |
| redis[hiredis] | >=5.0 | Redis async client | hiredis for C-speed parsing |
| Next.js | >=15.0 | React framework | App Router, server components, standard React framework |
| shadcn/ui | latest | UI component library | Copy-paste components, Tailwind-native, dark mode built-in |
| TanStack Table | v8 | Data table | Sorting, filtering, pagination for large datasets; shadcn DataTable wraps it |
| next-themes | >=0.4 | Theme switching | Dark mode toggle with 2 lines of code; shadcn default |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| uvicorn | >=0.30 | ASGI server | Running FastAPI in production |
| structlog | >=24.0 | Structured logging | JSON logging for fetch attempts, errors, retries |
| pydantic-settings | >=2.0 | Settings from env | Loading .env config, API keys, schedule intervals |
| httpx | >=0.27 | HTTP client | If direct API calls needed beyond fredapi/beaapi |
| pandas | >=2.2 | Data manipulation | fredapi returns pandas; transform before DB insert |
| PyYAML | >=6.0 | YAML parsing | Series configuration file |
| sqlalchemy-timescaledb | >=0.4 | TimescaleDB dialect | Hypertable DDL support in SQLAlchemy models |
| sse-starlette | >=2.0 | SSE support | If FastAPI built-in EventSourceResponse insufficient |
| flower | >=2.0 | Celery monitoring | Dev-time monitoring of task execution |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| fredapi | fedfred | fedfred is newer (async-native, built-in rate limiter, Polars support) but less battle-tested; fredapi is mature and well-documented |
| beaapi | Direct requests | beaapi is official and handles rate limiting automatically; no reason to hand-roll |
| SQLAlchemy | raw asyncpg | SQLAlchemy provides ORM, migrations (Alembic), and schema management; raw asyncpg is faster but requires manual SQL |
| Celery | APScheduler | Celery is heavier but provides task persistence, retry, monitoring (Flower); APScheduler is simpler but less robust for production |
| structlog | python-json-logger | structlog has better API, processors pipeline, and contextvars support |

**Installation (backend):**
```bash
pip install fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic \
    celery[redis] redis[hiredis] fredapi beaapi tenacity pydantic-settings \
    structlog pandas pyyaml httpx sqlalchemy-timescaledb flower
```

**Installation (frontend):**
```bash
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir
cd frontend && npx shadcn@latest init
npx shadcn@latest add table card badge sidebar input button separator skeleton
npm install next-themes @tanstack/react-table
```

## Architecture Patterns

### Recommended Project Structure
```
ecpm/
├── docker-compose.yml
├── docker-compose.override.yml    # Dev overrides (ports, volumes, hot reload)
├── .env.example                   # Template for API keys and config
├── .env                           # Actual keys (gitignored)
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic/
│   │   ├── alembic.ini
│   │   ├── env.py                 # Async engine configuration
│   │   └── versions/
│   ├── ecpm/
│   │   ├── __init__.py
│   │   ├── __main__.py            # CLI entry point (python -m ecpm fetch)
│   │   ├── config.py              # Pydantic Settings (env vars, schedule)
│   │   ├── database.py            # AsyncEngine, AsyncSession factory
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── observation.py     # Hypertable model
│   │   │   └── series_metadata.py # Metadata model
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── series.py          # Pydantic response models
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # Main API router
│   │   │   ├── data.py            # /api/data/* endpoints
│   │   │   └── status.py          # /api/data/status endpoint
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── fred_client.py     # FRED API wrapper with retry
│   │   │   ├── bea_client.py      # BEA API wrapper with retry
│   │   │   ├── pipeline.py        # Orchestrates fetch -> transform -> store
│   │   │   └── series_config.py   # Loads YAML series definitions
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py      # Celery app + config
│   │   │   └── fetch_tasks.py     # Periodic fetch tasks
│   │   └── core/
│   │       ├── __init__.py
│   │       └── logging.py         # structlog configuration
│   └── series_config.yaml         # Series definitions (FRED IDs, BEA tables)
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx         # Root layout with ThemeProvider
│   │   │   ├── page.tsx           # Redirect to /data
│   │   │   └── data/
│   │   │       └── page.tsx       # Data overview page
│   │   ├── components/
│   │   │   ├── ui/                # shadcn components
│   │   │   ├── layout/
│   │   │   │   ├── sidebar.tsx    # Navigation shell with phase links
│   │   │   │   └── header.tsx     # Top bar
│   │   │   └── data/
│   │   │       └── series-table.tsx  # Sortable/searchable data table
│   │   └── lib/
│   │       ├── api.ts             # Backend API client
│   │       └── utils.ts           # Utility functions
│   └── tailwind.config.ts
└── config/
    └── timescaledb/
        └── init.sql               # CREATE EXTENSION timescaledb
```

### Pattern 1: TimescaleDB Schema Design
**What:** Two-table design -- metadata table + observations hypertable
**When to use:** Always for this project (heterogeneous time-series at different frequencies)

```sql
-- Series metadata (regular PostgreSQL table)
CREATE TABLE series_metadata (
    id SERIAL PRIMARY KEY,
    series_id VARCHAR(50) UNIQUE NOT NULL,    -- e.g., "GDPC1" or "NIPA_T11200_L1"
    source VARCHAR(10) NOT NULL,               -- "FRED" or "BEA"
    source_detail JSONB,                       -- BEA: {dataset, table_name, line_number}
    name TEXT NOT NULL,
    units VARCHAR(100),
    frequency VARCHAR(1) NOT NULL,             -- "D", "M", "Q", "A"
    seasonal_adjustment VARCHAR(50),
    last_updated TIMESTAMPTZ,
    last_fetched TIMESTAMPTZ,
    observation_count INTEGER DEFAULT 0,
    fetch_status VARCHAR(20) DEFAULT 'pending', -- pending/ok/stale/error
    fetch_error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Time-series observations (TimescaleDB hypertable)
CREATE TABLE observations (
    observation_date TIMESTAMPTZ NOT NULL,
    series_id VARCHAR(50) NOT NULL,
    value DOUBLE PRECISION,                    -- NULL for explicit gaps
    vintage_date DATE,                         -- DATA-09: for future revision tracking
    gap_flag BOOLEAN DEFAULT FALSE,            -- Explicit gap marker
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (series_id) REFERENCES series_metadata(series_id)
);

-- Convert to hypertable
SELECT create_hypertable('observations', 'observation_date',
    chunk_time_interval => INTERVAL '1 year');  -- Macro data is sparse; yearly chunks

-- Indexes for common query patterns
CREATE INDEX idx_obs_series_date ON observations (series_id, observation_date DESC);
CREATE UNIQUE INDEX idx_obs_unique ON observations (series_id, observation_date, vintage_date)
    WHERE vintage_date IS NOT NULL;
CREATE UNIQUE INDEX idx_obs_unique_no_vintage ON observations (series_id, observation_date)
    WHERE vintage_date IS NULL;
```

### Pattern 2: Ingestion Pipeline with Retry
**What:** Wrapper around fredapi/beaapi with tenacity retry and structured logging
**When to use:** All data fetches

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog

logger = structlog.get_logger()

class FredClient:
    def __init__(self, api_key: str):
        self.fred = Fred(api_key=api_key)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        before_sleep=lambda retry_state: logger.warning(
            "fred_retry",
            series_id=retry_state.args[1] if len(retry_state.args) > 1 else "unknown",
            attempt=retry_state.attempt_number,
        ),
    )
    async def fetch_series(self, series_id: str) -> pd.DataFrame:
        # fredapi is sync; run in executor
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, self.fred.get_series, series_id
        )
        info = await loop.run_in_executor(
            None, self.fred.get_series_info, series_id
        )
        logger.info("fred_fetch_success", series_id=series_id, count=len(data))
        return data, info
```

### Pattern 3: Celery Beat Schedule in Docker
**What:** Separate beat and worker containers sharing the same codebase
**When to use:** Scheduled data fetches

```python
# ecpm/tasks/celery_app.py
from celery import Celery
from celery.schedules import crontab

celery_app = Celery("ecpm", broker="redis://redis:6379/0", backend="redis://redis:6379/1")

celery_app.conf.beat_schedule = {
    "daily-data-refresh": {
        "task": "ecpm.tasks.fetch_tasks.fetch_all_series",
        "schedule": crontab(hour=6, minute=0),  # Daily at 6 AM
    },
}
celery_app.conf.timezone = "US/Eastern"
```

```yaml
# docker-compose.yml (relevant services)
services:
  celery-worker:
    build: ./backend
    command: celery -A ecpm.tasks.celery_app worker -l info -c 2
    depends_on:
      redis: { condition: service_healthy }
      timescaledb: { condition: service_healthy }
    env_file: .env

  celery-beat:
    build: ./backend
    command: celery -A ecpm.tasks.celery_app beat -l info
    depends_on:
      redis: { condition: service_healthy }
    env_file: .env
```

### Pattern 4: FastAPI Async Session Dependency
**What:** SQLAlchemy 2.0 async session via FastAPI dependency injection
**When to use:** All database-accessing endpoints

```python
# ecpm/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine(
    "postgresql+asyncpg://ecpm:ecpm@timescaledb:5432/ecpm",
    pool_size=5, max_overflow=10,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### Pattern 5: BEA NIPA Table Name Mapping
**What:** BEA API uses TableName codes that map to official table numbers
**When to use:** All BEA data retrieval

```
BEA TableName Format: T{section}{subsection}{metric}
- Table 6.19  -> T61900  (Corporate profits -- but check: 6.19 may map to T60900 or T61900)
- Table 1.12  -> T11200  (National Income by Type of Income)
- Table 1.3   -> T10300  (Real Gross Domestic Product)
- Table 1.15  -> T11500  (Gross Value Added of Domestic Corporate Business)

FixedAssets is a SEPARATE dataset from NIPA:
  beaapi.get_data(key, datasetname='FixedAssets', TableName='FAAt101', ...)

Use beaapi.get_parameter_values(key, 'NIPA', 'TableName') to discover all available tables.
Use beaapi.get_parameter_values(key, 'FixedAssets', 'TableName') for FAT tables.
```

### Anti-Patterns to Avoid
- **Resampling on ingestion:** Never convert quarterly data to monthly or vice versa during storage. Store at native frequency; resample at query time only.
- **Single observations table without metadata:** Metadata must be a separate table -- querying metadata should not scan the hypertable.
- **Celery beat in the worker container:** Always run beat as a separate single-instance container to avoid duplicate scheduled tasks.
- **Synchronous fredapi in async endpoints:** fredapi is sync -- wrap in `run_in_executor()` or use a Celery task; never block the FastAPI event loop.
- **Hardcoded series IDs:** All series must come from the YAML configuration file. Adding a series should require zero code changes.
- **Giant single migration:** Break into logical steps: extension creation, metadata table, observations hypertable, indexes.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| FRED API access | Custom HTTP client with auth | `fredapi` library | Handles auth, pagination, series info, ALFRED vintage API |
| BEA API access | Custom HTTP client | `beaapi` (official) | Auto rate limiting (100/min), parameter discovery, pandas output |
| Exponential backoff | Custom retry loops | `tenacity` decorator | Handles jitter, max attempts, exception filtering, logging hooks |
| Database migrations | Raw SQL scripts | Alembic | Version tracking, rollback, autogenerate from models |
| Structured logging | Custom JSON formatter | `structlog` | Processors pipeline, contextvars binding, stdlib integration |
| Settings management | Custom env parser | `pydantic-settings` | Type validation, .env file loading, nested settings |
| Data table UI | Custom table component | shadcn DataTable (TanStack Table) | Sorting, filtering, pagination built-in; dark mode automatic |
| Dark mode toggle | Custom CSS solution | `next-themes` | 2 lines of code; handles system preference, localStorage persistence |

**Key insight:** This phase is primarily integration work -- connecting well-established libraries together. The value is in correct wiring, schema design, and error handling, not in novel code.

## Common Pitfalls

### Pitfall 1: BEA Table Name Discovery
**What goes wrong:** BEA NIPA table names (T10100, T61900) are not intuitive and don't exactly follow a simple formula. The mapping from human-readable table numbers (Table 6.19) to API TableName codes requires verification.
**Why it happens:** BEA's naming convention is not perfectly documented; some tables have been renumbered over time.
**How to avoid:** On first run, call `beaapi.get_parameter_values(key, 'NIPA', 'TableName')` and `beaapi.get_parameter_values(key, 'FixedAssets', 'TableName')` to get the full list of available tables with descriptions. Store this mapping. Verify each table code against the description before hardcoding in config.
**Warning signs:** Empty DataFrames returned from get_data; HTTP 400 errors with "invalid TableName."

### Pitfall 2: fredapi is Synchronous
**What goes wrong:** Calling fredapi methods directly in async FastAPI endpoints blocks the event loop, causing all concurrent requests to stall.
**Why it happens:** fredapi uses requests internally; it predates async Python patterns.
**How to avoid:** Either (a) run fredapi calls in a thread executor (`loop.run_in_executor`), or (b) perform all FRED fetches in Celery tasks (which are already synchronous workers). For the manual fetch endpoint, use Celery task submission and return a task ID.
**Warning signs:** Slow API response times; timeouts on concurrent requests during data fetch.

### Pitfall 3: Alembic + TimescaleDB Index Conflicts
**What goes wrong:** TimescaleDB automatically creates indexes on hypertable time columns. Alembic's autogenerate sees these untracked indexes and generates DROP INDEX operations.
**Why it happens:** Alembic compares model metadata against database state; TimescaleDB's auto-created indexes aren't in the model.
**How to avoid:** Use `include_object` filter in Alembic's env.py to exclude TimescaleDB internal tables and auto-generated indexes. Also exclude `_timescaledb_internal` schema.
**Warning signs:** Alembic generates unexpected DROP INDEX or errors about `cache_inval_hypertable`.

### Pitfall 4: FRED Rate Limit (120 req/min)
**What goes wrong:** Fetching 50-80 FRED series sequentially with no delay hits the rate limit, causing 429 errors.
**Why it happens:** Each get_series() + get_series_info() = 2 API calls per series. 80 series = 160 calls, exceeding 120/min.
**How to avoid:** Add a small delay between fetches (e.g., 0.6s between calls) or use tenacity's rate limiter. Process series in batches of ~50 with a pause between batches.
**Warning signs:** HTTP 429 responses; ValueError from fredapi.

### Pitfall 5: Docker Compose Service Startup Order
**What goes wrong:** Backend starts before TimescaleDB is ready to accept connections, causing immediate crash.
**Why it happens:** `depends_on` only waits for container start, not service readiness.
**How to avoid:** Use `depends_on` with `condition: service_healthy` and proper healthcheck on TimescaleDB (`pg_isready`). Also add connection retry logic in the backend startup.
**Warning signs:** "connection refused" errors on first `docker compose up`.

### Pitfall 6: BEA FixedAssets is a Separate Dataset
**What goes wrong:** Trying to fetch Fixed Assets tables using `datasetname='NIPA'` returns errors.
**Why it happens:** BEA organizes Fixed Assets (FAT) as a distinct dataset from NIPA.
**How to avoid:** Use `datasetname='FixedAssets'` for FAT tables. The ingestion pipeline must handle both datasets.
**Warning signs:** "invalid parameter" errors; empty results for FAT table names.

## Code Examples

### Docker Compose Health Checks
```yaml
services:
  timescaledb:
    image: timescale/timescaledb:latest-pg16
    environment:
      POSTGRES_DB: ecpm
      POSTGRES_USER: ecpm
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-ecpm_dev}
    ports:
      - "5432:5432"
    volumes:
      - timescaledb_data:/var/lib/postgresql/data
      - ./config/timescaledb/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ecpm -d ecpm"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  backend:
    build: ./backend
    command: uvicorn ecpm.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    env_file: .env
    depends_on:
      timescaledb: { condition: service_healthy }
      redis: { condition: service_healthy }
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  frontend:
    build: ./frontend
    command: npm run dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      backend: { condition: service_healthy }
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  timescaledb_data:
```

### SSE Progress Streaming for Data Fetch
```python
# Source: FastAPI official docs + sse-starlette pattern
from sse_starlette.sse import EventSourceResponse
from fastapi import APIRouter
import json

router = APIRouter(prefix="/api/data")

@router.get("/fetch/stream")
async def stream_fetch_progress():
    async def event_generator():
        yield {"event": "start", "data": json.dumps({"total_series": 75})}
        # Celery task publishes progress to Redis pubsub
        async for progress in redis_subscribe("fetch_progress"):
            yield {
                "event": "progress",
                "data": json.dumps(progress)
            }
        yield {"event": "complete", "data": json.dumps({"status": "done"})}
    return EventSourceResponse(event_generator())
```

### Series Configuration YAML
```yaml
# series_config.yaml
fred:
  # GDP components
  - id: GDPC1
    name: Real Gross Domestic Product
    category: gdp
  - id: A191RL1Q225SBEA
    name: Real GDP Growth Rate
    category: gdp
  # Interest rates
  - id: FEDFUNDS
    name: Federal Funds Effective Rate
    category: interest_rates
  - id: DGS10
    name: 10-Year Treasury Constant Maturity Rate
    category: interest_rates
  # ... 50-80 total series

bea:
  nipa:
    - table_name: T11200
      description: National Income by Type of Income
      frequency: Q,A
      years: "1947,ALL"
    - table_name: T61900
      description: Corporate Profits by Industry
      frequency: Q,A
      years: "1947,ALL"
    - table_name: T10300
      description: Real Gross Domestic Product
      frequency: Q,A
      years: "1947,ALL"
    - table_name: T11500
      description: Gross Value Added of Domestic Corporate Business
      frequency: Q,A
      years: "1947,ALL"
  fixed_assets:
    - table_name: FAAt101
      description: Current-Cost Net Stock of Fixed Assets
      frequency: A
      years: "1925,ALL"
```

### Alembic env.py for Async + TimescaleDB
```python
# alembic/env.py
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

def include_object(object, name, type_, reflected, compare_to):
    # Exclude TimescaleDB internal schemas and auto-generated objects
    if type_ == "table" and object.schema == "_timescaledb_internal":
        return False
    if type_ == "index" and name.startswith("_hyper_"):
        return False
    return True

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    engine = create_async_engine(get_url())
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()

def run_migrations_online():
    asyncio.run(run_async_migrations())
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SQLAlchemy 1.x sync | SQLAlchemy 2.0 async (Mapped types) | 2023 | Native async; better type hints; required for asyncpg |
| FastAPI manual SSE | Built-in EventSourceResponse | FastAPI 0.135.0 | No need for sse-starlette (but sse-starlette still works and is more mature) |
| Pydantic v1 | Pydantic v2 | 2023 | 5-50x faster validation; model_config instead of Config class |
| fredapi only | fedfred (newer alternative) | 2024-2025 | fedfred has async, Polars, rate limiter; but fredapi is more proven |
| docker-compose (v1) | docker compose (v2, built-in) | 2023 | v2 is now standard; uses `docker compose` not `docker-compose` |
| shadcn/ui init | shadcn CLI (npx shadcn@latest) | 2024 | Simplified setup; better registry support |

**Deprecated/outdated:**
- `docker-compose` CLI (v1): Use `docker compose` (v2, bundled with Docker Desktop/Engine)
- SQLAlchemy `declarative_base()`: Use `DeclarativeBase` class (SQLAlchemy 2.0)
- Pydantic `class Config`: Use `model_config = ConfigDict(...)` (Pydantic v2)

## Open Questions

1. **Exact BEA NIPA Table Name codes**
   - What we know: The format is T{digits} and FixedAssets is a separate dataset
   - What's unclear: Exact mapping for Table 6.19 (corporate profits) -- could be T60900 or T61900. FAT table names need discovery.
   - Recommendation: First implementation task should call `beaapi.get_parameter_values()` to discover and document all available table names. Log the full list and select the correct ones.

2. **fredapi vs fedfred**
   - What we know: fredapi is mature and proven; fedfred is newer with async support and built-in rate limiting
   - What's unclear: Whether fedfred's async support justifies switching from the more proven fredapi
   - Recommendation: Use fredapi (proven, widely documented) and wrap sync calls in executors. fredapi is sufficient for this use case since fetches happen in Celery workers anyway.

3. **Celery worker concurrency with fredapi**
   - What we know: fredapi is sync; Celery workers are sync by default (prefork pool)
   - What's unclear: Whether a single worker with 2 prefork processes is sufficient for daily fetch of ~80 FRED + ~5 BEA series
   - Recommendation: Start with concurrency=2 (prefork). Daily fetch takes <5 minutes total. No need for async Celery workers.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >= 8.0 + pytest-asyncio >= 0.23 |
| Config file | `backend/pyproject.toml` [tool.pytest.ini_options] -- Wave 0 |
| Quick run command | `docker compose exec backend pytest tests/ -x --timeout=30` |
| Full suite command | `docker compose exec backend pytest tests/ -v --timeout=60` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | FRED API retrieval with auth | integration | `pytest tests/test_fred_client.py -x` | Wave 0 |
| DATA-02 | FRED series cached in TimescaleDB | integration | `pytest tests/test_ingestion_pipeline.py::test_fred_persistence -x` | Wave 0 |
| DATA-03 | BEA NIPA table ingestion | integration | `pytest tests/test_bea_client.py -x` | Wave 0 |
| DATA-04 | Series metadata storage | unit | `pytest tests/test_models.py::test_metadata_fields -x` | Wave 0 |
| DATA-05 | Celery beat scheduled fetch | integration | `pytest tests/test_tasks.py::test_scheduled_fetch -x` | Wave 0 |
| DATA-06 | Missing data handling (LOCF, gaps) | unit | `pytest tests/test_ingestion_pipeline.py::test_gap_handling -x` | Wave 0 |
| DATA-07 | Native frequency storage | unit | `pytest tests/test_ingestion_pipeline.py::test_native_frequency -x` | Wave 0 |
| DATA-08 | Exponential backoff retry | unit | `pytest tests/test_fred_client.py::test_retry_backoff -x` | Wave 0 |
| DATA-09 | vintage_date column exists | unit | `pytest tests/test_models.py::test_vintage_date_column -x` | Wave 0 |
| INFR-01 | Docker Compose starts all 4 containers | smoke | `docker compose up -d && docker compose ps --format json` | Wave 0 |
| INFR-02 | FastAPI REST endpoints respond | integration | `pytest tests/test_api.py -x` | Wave 0 |
| INFR-03 | SSE streaming progress | integration | `pytest tests/test_api.py::test_sse_stream -x` | Wave 0 |
| INFR-04 | Redis caching works | integration | `pytest tests/test_cache.py -x` | Wave 0 |
| INFR-05 | Health checks pass | smoke | `docker compose ps --format json \| jq '.[] .Health'` | Wave 0 |

### Sampling Rate
- **Per task commit:** `docker compose exec backend pytest tests/ -x --timeout=30`
- **Per wave merge:** `docker compose exec backend pytest tests/ -v --timeout=60`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/pyproject.toml` -- pytest + pytest-asyncio configuration
- [ ] `backend/tests/conftest.py` -- async session fixtures, test database, mock API clients
- [ ] `backend/tests/test_fred_client.py` -- covers DATA-01, DATA-08
- [ ] `backend/tests/test_bea_client.py` -- covers DATA-03
- [ ] `backend/tests/test_ingestion_pipeline.py` -- covers DATA-02, DATA-06, DATA-07
- [ ] `backend/tests/test_models.py` -- covers DATA-04, DATA-09
- [ ] `backend/tests/test_tasks.py` -- covers DATA-05
- [ ] `backend/tests/test_api.py` -- covers INFR-02, INFR-03
- [ ] `backend/tests/test_cache.py` -- covers INFR-04
- [ ] Framework install: `pip install pytest pytest-asyncio pytest-timeout` -- none detected

## Sources

### Primary (HIGH confidence)
- [beaapi official docs](https://us-bea.github.io/beaapi/README.html) - Full API usage, parameter discovery, rate limiting
- [fredapi PyPI](https://pypi.org/project/fredapi/) - API methods, authentication, pandas integration
- [FastAPI official docs](https://fastapi.tiangolo.com/tutorial/server-sent-events/) - SSE support (EventSourceResponse)
- [TimescaleDB docs](https://docs.timescale.com/) - Hypertable design, chunk intervals, compression
- [shadcn/ui docs](https://ui.shadcn.com/docs/dark-mode/next) - Next.js dark mode setup with next-themes

### Secondary (MEDIUM confidence)
- [SQLAlchemy 2.0 + FastAPI async patterns](https://dev-faizan.medium.com/fastapi-sqlalchemy-2-0-modern-async-database-patterns-7879d39b6843) - Verified against SQLAlchemy docs
- [Celery + FastAPI + Redis guide](https://testdriven.io/blog/fastapi-and-celery/) - Well-known reference (TestDriven.io)
- [Alembic + TimescaleDB conflicts](https://github.com/sqlalchemy/alembic/discussions/1465) - include_object workaround verified
- [tenacity docs](https://tenacity.readthedocs.io/) - Exponential backoff patterns
- [BEA table name format](https://fgeerolf.com/data/bea/api.html) - T{section}{subsection}{metric} pattern

### Tertiary (LOW confidence)
- BEA NIPA exact table name codes (T61900 for Table 6.19) -- needs runtime verification via get_parameter_values()
- FixedAssets table name format (FAAt101 etc.) -- needs runtime verification

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries are well-established with extensive documentation
- Architecture: HIGH - FastAPI+Celery+Redis+TimescaleDB is a well-trodden pattern
- Pitfalls: HIGH - Multiple sources confirm these issues (Alembic+TimescaleDB, fredapi sync, rate limits)
- BEA table names: MEDIUM - Format is documented but exact codes need runtime verification

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable stack; 30-day validity)
