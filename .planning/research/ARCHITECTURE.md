# Architecture Patterns

**Domain:** Macroeconomic data analysis, prediction, and interactive dashboard platform
**Researched:** 2026-03-23

## Recommended Architecture

A four-layer pipeline architecture where data flows strictly downward through ingestion, transformation, modeling, and presentation layers. Each layer communicates with its neighbors through well-defined interfaces (database tables/views and REST API endpoints), never skipping layers.

```
+---------------------------------------------------------------------+
|  MODULE D: FRONTEND DASHBOARD (Next.js)                             |
|  - Time-series charts (Plotly.js)                                   |
|  - I-O matrix visualizer                                            |
|  - Simulation control panel                                         |
|  - Crisis probability gauge                                         |
+------------------------------|--------------------------------------+
                               | REST API (JSON) + SSE for long jobs
+------------------------------|--------------------------------------+
|  FASTAPI APPLICATION SERVER                                         |
|  - /api/indicators/* (read computed features)                       |
|  - /api/models/* (trigger/read model outputs)                       |
|  - /api/simulations/* (run/configure ABM)                           |
|  - /api/data/* (raw series access)                                  |
|  - /api/crisis-index/* (composite index)                            |
+---------|-------------------|-------------------|-------------------+
          |                   |                   |
+---------v----+ +------------v------+ +---------v------------------+
| MODULE A:    | | MODULE B:         | | MODULE C:                  |
| DATA         | | FEATURE           | | PREDICTIVE MODELING        |
| INGESTION    | | ENGINEERING       | | & SIMULATION               |
| & ETL        | |                   | |                            |
| - FRED pull  | | - Profitability   | | - VAR/SVAR forecasting     |
| - BEA pull   | | - Realization gap | | - Anomaly detection        |
| - BLS pull   | | - Disproportional.| | - Leontief shock sim       |
| - Scheduling | | - Fict. capital   | | - Agent-based sim (Mesa)   |
| - Validation | | - Imperialism     | | - Composite crisis index   |
+---------+----+ | - Cybernetic      | +----------------------------+
          |      +------|------------+              |
          |             |                           |
+---------v-------------v---------------------------v-----------------+
|  DATA LAYER                                                         |
|  TimescaleDB: raw_series, computed_features, model_outputs          |
|  Redis: cached API responses, model result cache, job status        |
+---------------------------------------------------------------------+
```

### Component Boundaries

| Component | Responsibility | Communicates With | Interface |
|-----------|---------------|-------------------|-----------|
| Module A: Data Ingestion | Pull raw data from external APIs (FRED, BEA, BLS), validate, normalize temporal resolution, store | TimescaleDB (writes raw_series tables), Redis (cache API responses to respect rate limits) | Python functions callable by scheduler; writes to `raw_series` hypertables |
| Module B: Feature Engineering | Read raw series, compute Marxist economic categories (rate of profit, OCC, realization gap, etc.), store derived features | TimescaleDB (reads raw_series, writes computed_features), Module A output tables | Python functions/classes; reads from `raw_series`, writes to `computed_features` hypertables |
| Module C: Predictive Modeling | Run econometric models (VAR/SVAR), anomaly detection, Leontief simulations, ABM, produce composite crisis index | TimescaleDB (reads computed_features, writes model_outputs), Redis (cache expensive model results) | Python functions/classes; reads from `computed_features`, writes to `model_outputs` tables |
| FastAPI Server | Expose all data, features, model outputs, and simulation controls as REST endpoints; manage long-running job lifecycle | All TimescaleDB tables (reads), Redis (read/write cache), Modules B and C (triggers recomputation) | REST API (JSON); SSE for streaming long-running job status |
| Module D: Frontend | Render interactive visualizations, accept user input for simulations, display crisis probability | FastAPI server only (never touches DB directly) | HTTP requests to FastAPI endpoints; SSE listeners for job progress |
| TimescaleDB | Persist all time-series data at multiple temporal resolutions | All backend modules | SQL via psycopg/asyncpg; hypertables with time-based partitioning |
| Redis | Cache frequently accessed data, store job status for long-running computations | FastAPI server, Module A (rate limit tracking), Module C (model result cache) | redis-py client |
| APScheduler | Trigger periodic data ingestion and recomputation | Module A, Module B, Module C (via function calls) | In-process scheduler running inside FastAPI process |

### Data Flow

**Primary pipeline (the core value path):**

```
External APIs (FRED/BEA)
    |
    v [batch pull, scheduled]
Module A: Ingestion & ETL
    | writes normalized time-series
    v
TimescaleDB: raw_series (hypertables)
    |
    v [triggered after ingestion completes]
Module B: Feature Engineering
    | reads raw_series, computes Marxist indicators
    v
TimescaleDB: computed_features (hypertables)
    |
    v [triggered after feature engineering completes]
Module C: Predictive Modeling
    | reads features, runs VAR/anomaly detection/etc.
    v
TimescaleDB: model_outputs + Redis cache
    |
    v [on dashboard request]
FastAPI: serves JSON via REST endpoints
    |
    v [HTTP fetch + SSE]
Next.js Dashboard: renders charts, gauges, matrices
```

**Secondary flows:**

1. **On-demand simulation:** User adjusts ABM parameters in dashboard -> POST to FastAPI -> FastAPI triggers Module C simulation -> SSE streams progress -> result stored in model_outputs -> dashboard fetches completed result.

2. **Cache invalidation:** New data ingestion completes -> Module A signals completion -> invalidate relevant Redis cache keys -> downstream recomputation triggered.

3. **Historical calibration:** Batch job runs full pipeline against historical data windows -> stores calibration metrics alongside model outputs.

**Temporal resolution handling:**

Raw data arrives at mixed frequencies (daily, monthly, quarterly, annual). Module A normalizes and tags each series with its native frequency. Module B handles alignment -- quarterly features are computed from quarterly inputs; mixed-frequency features use the coarsest resolution or interpolation where theoretically justified. TimescaleDB's `time_bucket()` function handles aggregation at query time for dashboard display.

## Patterns to Follow

### Pattern 1: Pipeline-as-Functions with Database Boundaries

**What:** Each module (A, B, C) is implemented as a set of pure-ish Python functions that read from database tables and write to database tables. The database is the integration layer, not in-memory function calls.

**When:** Always. This is the core architectural pattern.

**Why:** Decouples modules completely. Module B does not import Module A code -- it reads from tables that Module A populated. This means each module can be tested independently by seeding its input tables. It also means partial pipeline reruns are trivial (re-run Module B without re-ingesting data).

**Example:**
```python
# module_a/ingest_fred.py
async def ingest_fred_series(series_ids: list[str], db: AsyncSession):
    """Pull from FRED API, validate, write to raw_series table."""
    for sid in series_ids:
        data = await fred_client.get_series(sid)
        validated = validate_and_normalize(data)
        await db.execute(
            insert(RawSeries).values(validated).on_conflict_do_update(...)
        )

# module_b/profitability.py
async def compute_rate_of_profit(db: AsyncSession):
    """Read raw series, compute r = profits / (fixed_assets + compensation)."""
    profits = await db.execute(select(RawSeries).where(series_id == "CORP_PROFITS"))
    assets = await db.execute(select(RawSeries).where(series_id == "FIXED_ASSETS"))
    compensation = await db.execute(select(RawSeries).where(series_id == "COMPENSATION"))
    # compute and store
    result = compute_r(profits, assets, compensation)
    await db.execute(insert(ComputedFeature).values(result))
```

### Pattern 2: Hypertable Schema Design for Multi-Resolution Time Series

**What:** Use TimescaleDB hypertables with a unified schema that handles multiple temporal resolutions, rather than separate tables per frequency.

**When:** For all time-series storage (raw and computed).

**Why:** Economic data arrives at daily, monthly, quarterly, and annual frequencies. A single hypertable with a `frequency` column and TimescaleDB's `time_bucket()` for queries is simpler than managing dozens of frequency-specific tables.

**Example:**
```sql
CREATE TABLE raw_series (
    time        TIMESTAMPTZ NOT NULL,
    series_id   TEXT NOT NULL,
    value       DOUBLE PRECISION,
    frequency   TEXT NOT NULL,  -- 'D', 'M', 'Q', 'A'
    source      TEXT NOT NULL,  -- 'FRED', 'BEA', 'BLS'
    vintage     TIMESTAMPTZ,   -- for point-in-time accuracy
    UNIQUE (time, series_id)
);
SELECT create_hypertable('raw_series', 'time');

-- Continuous aggregate for monthly dashboard queries
CREATE MATERIALIZED VIEW monthly_features
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 month', time) AS month,
       series_id,
       avg(value) AS avg_value
FROM raw_series
WHERE frequency = 'D'
GROUP BY month, series_id;
```

### Pattern 3: APScheduler for Lightweight Job Orchestration

**What:** Use APScheduler (running in-process with FastAPI) for scheduling data pulls and pipeline stages, rather than Airflow or Dagster.

**When:** For this project specifically -- a single-user local tool.

**Why:** Airflow and Dagster are designed for team-scale data engineering with DAG visualization, multi-worker execution, and complex dependency management. This project has a simple linear pipeline with maybe 10 scheduled jobs. APScheduler adds zero infrastructure overhead (no separate scheduler service, no metadata database) and integrates directly with FastAPI's async loop. If the pipeline grows complex enough to need a DAG runner, Dagster can be added later without changing the module code (because modules are database-boundary functions, not scheduler-coupled).

**Example:**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def start_scheduler():
    # Daily: pull FRED data
    scheduler.add_job(ingest_fred_series, "cron", hour=2, args=[FRED_SERIES_IDS])
    # After ingestion: recompute features
    scheduler.add_job(recompute_all_features, "cron", hour=3)
    # After features: rerun models
    scheduler.add_job(rerun_models, "cron", hour=4)
    scheduler.start()
```

### Pattern 4: SSE for Long-Running Job Feedback

**What:** Use Server-Sent Events (not WebSockets) for streaming progress of long-running operations (model training, ABM simulation runs) from FastAPI to the dashboard.

**When:** Any operation that takes more than a few seconds -- ABM simulations, full model retraining, historical calibration runs.

**Why:** SSE is unidirectional (server to client), which matches the use case perfectly -- the dashboard needs to receive progress updates, not send a stream of data back. SSE works over standard HTTP (no protocol upgrade), reconnects automatically on disconnect, and FastAPI has native support via `EventSourceResponse`. WebSockets are overkill for this pattern.

### Pattern 5: Pydantic Models as the API Contract

**What:** Define all API request/response shapes as Pydantic models shared between FastAPI endpoint definitions and (optionally) used to generate TypeScript types for the Next.js frontend.

**When:** Every API endpoint.

**Why:** Ensures type safety across the Python-TypeScript boundary. FastAPI auto-generates OpenAPI schema from Pydantic models. Tools like `openapi-typescript` can generate TypeScript types from that schema, giving the frontend compile-time guarantees about API shapes without manual type duplication.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Direct Database Access from Frontend

**What:** Next.js API routes or server components querying TimescaleDB directly.

**Why bad:** Couples the frontend to the database schema. Makes it impossible to change the database structure without updating the frontend. Bypasses any business logic in the Python backend. Splits query logic across two languages.

**Instead:** All data access goes through FastAPI endpoints. The frontend knows nothing about the database.

### Anti-Pattern 2: Monolithic Pipeline Function

**What:** A single `run_pipeline()` function that calls ingestion, then feature engineering, then modeling in sequence with in-memory data passing.

**Why bad:** Cannot rerun a single stage. Cannot inspect intermediate results. Cannot test stages independently. A failure in Module C requires re-running Module A. Memory pressure from holding all data in RAM simultaneously.

**Instead:** Each stage reads from and writes to the database. Stages are independently runnable.

### Anti-Pattern 3: Airflow/Dagster for a Single-User Local Tool

**What:** Deploying a full-featured workflow orchestrator when the pipeline has fewer than 15 jobs and one user.

**Why bad:** Airflow requires its own metadata database, webserver, scheduler process, and worker processes. That is 3-4 additional containers in Docker Compose for a problem solvable with 20 lines of APScheduler code. Dagster is lighter but still adds a separate service.

**Instead:** APScheduler in-process. Graduate to Dagster only if the pipeline grows to need DAG visualization, retries with backoff, or multi-worker parallelism.

### Anti-Pattern 4: Real-Time Streaming for Batch Economic Data

**What:** Building Kafka/Flink streaming infrastructure for data that updates monthly or quarterly.

**Why bad:** Macroeconomic data from FRED/BEA is released on known schedules (monthly, quarterly). There is nothing to stream. Real-time infrastructure adds massive complexity for zero benefit.

**Instead:** Scheduled batch pulls aligned with data release calendars. The "freshest" FRED data is still days old by the time it is published.

### Anti-Pattern 5: Separate Microservices per Module

**What:** Running Module A, B, C, and FastAPI as four separate containers with inter-service HTTP calls.

**Why bad:** For a single-user local tool, this adds network latency, deployment complexity, and debugging difficulty with zero scalability benefit. The modules share a database -- they do not need service boundaries.

**Instead:** Single Python application containing all modules, organized as packages. FastAPI imports and calls module functions directly when needed. The database-as-boundary pattern provides logical separation without process isolation overhead.

## Scalability Considerations

| Concern | At 1 user (MVP) | At research group (5-10) | At institutional scale |
|---------|-----------------|--------------------------|------------------------|
| Data volume | ~50-100 FRED/BEA series, <1GB | ~500 series, multi-source, ~10GB | Thousands of series, global sources, ~100GB+ |
| Compute | Single process, APScheduler | Same, possibly background workers | Dagster/Celery for parallel model runs |
| Database | Single TimescaleDB container | Same, with connection pooling | TimescaleDB with compression, possibly read replicas |
| API | Single FastAPI instance | Same, no change needed | Multiple workers behind load balancer |
| Frontend | Local access only | Deployed with auth | Deployed with auth, role-based access |
| Deployment | Docker Compose local | Docker Compose on a server | Kubernetes or managed services |

For this project (single-user, local Docker), scalability concerns are minimal. The architecture supports growth because the database-boundary pattern means upgrading orchestration, adding workers, or splitting services can happen without rewriting module code.

## Build Order (Dependency-Driven)

The following build order reflects hard dependencies between components. Each step requires the previous step's output to function.

```
Phase 1: Foundation
  [TimescaleDB schema] --> [Module A: Data Ingestion (FRED + BEA)]
  [FastAPI skeleton]   --> [Basic REST endpoints for raw data]
  [Next.js skeleton]   --> [Basic page rendering, connected to API]

Phase 2: Core Value Path
  [Module B: Feature Engineering] (depends on: raw_series from Phase 1)
  [API endpoints for computed features]
  [Dashboard: time-series charts for Marxist indicators]

Phase 3: Modeling
  [Module C.1: VAR/SVAR] (depends on: computed_features from Phase 2)
  [Module C.2: Anomaly detection] (depends on: computed_features from Phase 2)
  [Module C.5: Composite crisis index] (depends on: C.1 + C.2 outputs)
  [Dashboard: crisis probability gauge]

Phase 4: Advanced Simulation
  [Module C.3: Leontief structural analysis] (depends on: I-O data in raw_series)
  [Module C.4: Agent-based simulation] (depends on: computed_features)
  [Dashboard: I-O matrix visualizer, simulation control panel]

Phase 5: Enrichment
  [Additional data sources: BLS, World Bank, BIS]
  [Module B extensions: imperialist displacement, cybernetic indicators]
  [Historical calibration against crisis episodes]
  [Dashboard: VSM diagram, theoretical annotation layer]
```

**Ordering rationale:**

1. **Phase 1 before everything:** Nothing works without data in the database and a way to serve it.
2. **Phase 2 before Phase 3:** Models need features as inputs. Features are also independently valuable (the dashboard showing rate of profit over time is useful before any prediction exists).
3. **Phase 3 before Phase 4:** VAR/SVAR and anomaly detection are simpler, well-established methods that prove the modeling layer works. Leontief analysis requires I-O matrix data (a different, more complex data source). ABM is the most complex module and should be built last.
4. **Phase 5 is enrichment:** Additional data sources and advanced indicators do not change the architecture -- they add more series to Module A and more computations to Module B. They should come after the core pipeline is proven.

**Critical path:** TimescaleDB schema -> FRED ingestion -> rate of profit computation -> basic chart in dashboard. This is the minimum path to proving the system works end-to-end.

## Docker Compose Service Layout

```yaml
services:
  db:
    image: timescale/timescaledb:latest-pg16
    volumes:
      - timescale_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    depends_on: [db, redis]
    ports:
      - "8000:8000"
    # Contains: FastAPI + all Python modules (A, B, C) + APScheduler

  frontend:
    build: ./frontend
    depends_on: [backend]
    ports:
      - "3000:3000"
    # Next.js dev server or production build
```

Four containers total. No separate scheduler service. No message broker. The backend container is a single Python process running FastAPI with APScheduler, and all module code is importable within it.

## Sources

- [TimescaleDB Python integration](https://oneuptime.com/blog/post/2026-02-02-timescaledb-python/view) -- hypertable patterns with Python
- [TimescaleDB GitHub](https://github.com/timescale/timescaledb) -- continuous aggregates, compression
- [Next.js + FastAPI template](https://www.vintasoftware.com/blog/next-js-fastapi-template) -- full-stack integration pattern
- [Interactive Dashboard with Next.js and Python](https://www.augustinfotech.com/blogs/building-an-interactive-dashboard-with-next-js-and-python/) -- dashboard architecture
- [FastAPI SSE documentation](https://fastapi.tiangolo.com/tutorial/server-sent-events/) -- native SSE support
- [SSE with FastAPI and React](https://github.com/harshitsinghai77/server-sent-events-using-fastapi-and-reactjs) -- SSE + React integration
- [fredapi](https://github.com/mortada/fredapi) -- FRED Python client
- [fedfred](https://medium.com/@nsunder724/access-macroeconomic-data-at-scale-with-fedfred-a-modern-python-client-for-the-fred-api-96745541ef2a) -- modern FRED client with Pandas/Polars support
- [APScheduler vs Celery Beat](https://leapcell.io/blog/scheduling-tasks-in-python-apscheduler-vs-celery-beat) -- scheduler comparison
- [Plotly vs Recharts comparison](https://medium.com/@ponshriharini/comparing-8-popular-react-charting-libraries-performance-features-and-use-cases-cc178d80b3ba) -- charting library comparison
- [Statsmodels for econometrics](https://github.com/statsmodels/statsmodels) -- VAR/SVAR/VECM implementation
- [Macroeconomic time-series pipeline](https://medium.com/@silva.f.francis/building-an-advanced-pipeline-for-processing-and-analyzing-macroeconomic-time-series-a-b25ec9906863) -- Python econometric pipeline patterns
