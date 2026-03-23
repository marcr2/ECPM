# Technology Stack

**Project:** Economic Crisis Prediction Model (ECPM)
**Researched:** 2026-03-23
**Overall Confidence:** HIGH

## Critical Decision: Python 3.12

Mesa 3.5 (the agent-based modeling framework specified in the architecture doc) requires Python 3.12+. This is a hard constraint that overrides the architecture doc's "Python 3.10+" specification. All backend libraries listed below are compatible with Python 3.12. Use **Python 3.12** (not 3.13 or 3.14) for maximum ecosystem stability -- 3.12 is the sweet spot where every library below has confirmed support.

**Confidence:** HIGH -- Mesa PyPI page and release notes confirm Python >=3.12 requirement as of Mesa 3.4+.

---

## Recommended Stack

### Runtime & Language

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python | 3.12.x | Backend runtime | Required by Mesa 3.5; well-supported by all data science libraries; stable free-threading support in 3.12 |
| Node.js | 22 LTS | Frontend runtime | Required for Next.js 16; LTS channel for stability |
| uv | latest | Python package management | 10-100x faster than pip; lockfile support; recommended by FastAPI team; handles venvs automatically |

### Backend Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| FastAPI | ~0.135 | REST API framework | Async-native, automatic OpenAPI docs, Pydantic integration, 15k+ RPS, ideal for serving model outputs to dashboard |
| Uvicorn | latest | ASGI server | FastAPI's recommended production server; handles async I/O efficiently |
| Pydantic | ~2.12 | Data validation & serialization | Rust-powered validation (5-50x faster than v1); tight FastAPI integration; enforces schema contracts between modules |
| httpx | ~0.28 | Async HTTP client | For FRED/BEA API calls; native asyncio support; connection pooling; drop-in replacement for requests with async |

**Confidence:** HIGH -- versions verified against PyPI and official docs.

### Database Layer

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| TimescaleDB | 2.25 | Time-series database | PostgreSQL extension purpose-built for multi-resolution economic time-series; hypertable compression gives 289x speedup on MIN/MAX/FIRST/LAST queries; native continuous aggregates for pre-computing rolling indicators |
| PostgreSQL | 17 | Base database engine | Required by TimescaleDB 2.25; JSONB for simulation config storage (no need for separate MongoDB) |
| Redis | 7.4 | Caching & task broker | Cache computed Leontief inverses, model predictions, dashboard state; serve as Celery broker |
| SQLAlchemy | ~2.0 | ORM & query builder | Mature async support via asyncpg; TimescaleDB dialect available (sqlalchemy-timescaledb); Alembic migration support |
| asyncpg | latest | Async PostgreSQL driver | 15k concurrent queries/sec; required for non-blocking FastAPI<->TimescaleDB communication |
| Alembic | ~1.18 | Database migrations | Auto-generates migration scripts from SQLAlchemy models; standard for FastAPI+PostgreSQL projects |

**Confidence:** HIGH -- TimescaleDB 2.25 verified via GitHub releases; PostgreSQL 17 compatibility confirmed.

### Data Ingestion & API Clients

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| fredapi | ~0.5.2 | FRED data access | Official-style wrapper returning pandas Series/DataFrame; handles data revisions; fulltext search |
| beaapi | latest | BEA data access | Official BEA Python library (maintained by us-bea GitHub org); direct access to I-O tables, national accounts |
| pandas | ~3.0 | Data manipulation | Major release (Jan 2026); native string dtype; time-series resampling, frequency alignment, merge/join for multi-source data |
| NumPy | ~2.4 | Numerical computing | Matrix operations for Leontief inverse (I-A)^-1; eigenvalue analysis; array backend for all scientific libraries |
| SciPy | ~1.17 | Scientific computing | Sparse matrix support for large I-O tables; linear algebra (scipy.linalg.inv, solve); optimization for model calibration |

**Confidence:** HIGH -- pandas 3.0 verified via official release notes; fredapi/beaapi verified via PyPI.

**Note on Polars:** The architecture doc mentions Polars alongside Pandas. Skip Polars for this project -- the econometric libraries (statsmodels, Mesa) all expect pandas DataFrames. Adding Polars creates unnecessary conversion overhead for no benefit at this data scale (macroeconomic data is small -- thousands of rows, not millions).

### Econometrics & Statistical Modeling

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| statsmodels | ~0.14.6 | VAR/SVAR/VECM, unit root tests, Granger causality, Markov regime-switching | The only mature Python library with full SVAR identification restrictions and VECM cointegration testing; Hamilton-style Markov regime models built in |
| scikit-learn | ~1.8.0 | Isolation Forests, preprocessing, model evaluation | Industry standard; IsolationForest well-documented for anomaly detection; consistent API across all estimators |

**Confidence:** HIGH -- statsmodels 0.14.6 verified via PyPI (Dec 2025); scikit-learn 1.8.0 verified via official docs.

**Note on hmmlearn:** The architecture doc suggests hmmlearn for Markov regime-switching. Skip it -- statsmodels has built-in MarkovAutoregression and MarkovRegression classes that are purpose-built for econometric regime detection. Using hmmlearn would require manually adapting a generic HMM library to time-series data that statsmodels handles natively.

**Note on PyOD:** The architecture doc suggests PyOD for anomaly detection. Defer it -- scikit-learn's IsolationForest is sufficient for MVP. PyOD adds 30+ anomaly detection algorithms but introduces a large dependency tree. Add it in a later milestone if IsolationForest proves insufficient.

### Agent-Based Modeling

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Mesa | ~3.5.1 | Agent-based simulation | Only mature Python ABM framework; public event scheduling API (3.5); built-in data collection; active development toward 4.0 |

**Confidence:** HIGH -- Mesa 3.5.1 verified via PyPI (March 2026).

Mesa 3.5 is a significant release with stabilized event system and deprecation of legacy patterns. The project should target 3.5.x, not the 4.0 alpha -- 4.0 has breaking API changes and is not stable.

### Task Scheduling & Background Jobs

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Celery | ~5.5 | Async task queue | Scheduled data ingestion from FRED/BEA; background model retraining; simulation execution; proven Redis broker support |
| celery-beat | (included) | Periodic task scheduling | Cron-like scheduling for batch data pulls (monthly, quarterly, annual) |

**Confidence:** MEDIUM -- Celery is the established choice but adds operational complexity. For a single-user local tool, APScheduler would also work. Celery chosen because it handles long-running simulation tasks better and the architecture doc specifies scheduled batch jobs.

**Note on Airflow/Dagster:** The architecture doc suggests Airflow or Dagster for pipeline orchestration. Skip both -- massive overkill for a single-user local research tool with ~10 data sources. Celery beat handles the scheduling; FastAPI endpoints handle the orchestration. Adding Airflow would triple the Docker memory footprint for no benefit.

### Frontend Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Next.js | 16.2 | React framework | Turbopack stable by default (fast builds); React Compiler stable (automatic memoization); App Router for layout-based dashboard structure |
| React | 19 | UI library | Required by Next.js 16; concurrent features for smooth dashboard interactions |
| TypeScript | ~5.7 | Type safety | Catches data shape errors at build time; essential when wiring complex model outputs to chart components |

**Confidence:** HIGH -- Next.js 16.2 LTS verified via official blog (March 2026).

### Data Visualization

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Nivo | latest | Primary chart library | D3-based; supports SVG + Canvas rendering (Canvas for large time-series); built-in theming; Sankey diagrams for I-O flows; heatmaps for correlation matrices; line/area charts for time-series |
| D3.js | ~7.x | Custom visualizations | Direct D3 for: Beer VSM cybernetic diagram, Leontief I-O matrix view, force-directed sectoral dependency graph -- these are too custom for any chart library |
| Zustand | latest | State management | Lightweight (1.1kB); no boilerplate; perfect for managing toggled indicators, simulation params, time range selections |

**Confidence:** MEDIUM-HIGH -- Nivo chosen over Recharts because this project needs Canvas rendering for dense time-series AND Sankey diagrams for I-O flows. Recharts lacks both. Visx was considered but its steep learning curve and lack of pre-built chart types would slow development significantly.

**Note on Plotly:** The architecture doc suggests Plotly. Avoid Plotly.js in a Next.js app -- it is 3.5MB minified, ships its own DOM management that conflicts with React's virtual DOM, and its React wrapper (react-plotly.js) is poorly maintained. Nivo + D3 covers every visualization need at a fraction of the bundle size.

### Infrastructure & DevOps

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Docker | latest | Containerization | Reproducible environments across data science, API, and frontend layers |
| Docker Compose | v2 | Service orchestration | Single `docker compose up` for entire stack; health checks for service dependencies; volume mounts for development |

**Confidence:** HIGH -- standard tooling, no version concerns.

### Testing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| pytest | latest | Python testing | De facto standard; async test support; fixture system for database/API testing |
| pytest-asyncio | latest | Async test support | Required for testing FastAPI async endpoints and async database operations |
| Vitest | latest | Frontend testing | Native ESM support; compatible with Next.js; faster than Jest for TypeScript |

**Confidence:** HIGH -- standard choices with no controversy.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Python version | 3.12 | 3.10/3.11 | Mesa 3.5 requires >=3.12; no going lower |
| Python version | 3.12 | 3.13/3.14 | Some scientific libraries have incomplete 3.13+ wheels; 3.12 is safest |
| Package manager | uv | pip/poetry | uv is 10-100x faster, handles lockfiles, recommended by FastAPI team |
| Data manipulation | pandas 3.0 only | pandas + Polars | All downstream libraries expect pandas; Polars adds conversion friction for no gain at this scale |
| Regime detection | statsmodels MarkovAutoregression | hmmlearn | statsmodels has purpose-built econometric regime models; hmmlearn is generic HMM |
| Anomaly detection | scikit-learn IsolationForest | PyOD | scikit-learn sufficient for MVP; PyOD adds large dependency tree |
| Pipeline orchestration | Celery beat | Airflow/Dagster | Airflow/Dagster are massive overkill for single-user local tool; Celery handles scheduling fine |
| Charts | Nivo + D3 | Plotly.js | Plotly is 3.5MB, conflicts with React DOM, poorly maintained React wrapper |
| Charts | Nivo + D3 | Recharts | Recharts lacks Canvas rendering and Sankey diagrams needed for this project |
| Charts | Nivo + D3 | Visx | Visx has steep learning curve and no pre-built chart types; too low-level for rapid development |
| State management | Zustand | Redux | Redux is overkill for single-user dashboard; Zustand is simpler with less boilerplate |
| I-O analysis | NumPy/SciPy direct | iopy/PyIO | I-O libraries are niche, poorly maintained; NumPy's `linalg.inv` and SciPy's sparse matrices handle Leontief math directly with more control |
| Database ORM | SQLAlchemy 2.0 | SQLModel | SQLModel is a thin wrapper over SQLAlchemy; adds a dependency for syntactic sugar; SQLAlchemy 2.0's own syntax is already clean |
| Document store | PostgreSQL JSONB | MongoDB | PostgreSQL JSONB handles simulation configs and annotations without adding another database to the Docker stack |

---

## Installation

### Backend (Python)

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project with Python 3.12
uv init --python 3.12
uv venv

# Core framework
uv add fastapi[standard] uvicorn pydantic httpx

# Database
uv add sqlalchemy[asyncio] asyncpg alembic sqlalchemy-timescaledb redis celery

# Data ingestion
uv add pandas numpy scipy fredapi beaapi

# Econometrics & ML
uv add statsmodels scikit-learn

# Agent-based modeling
uv add mesa~=3.5

# Testing
uv add --dev pytest pytest-asyncio
```

### Frontend (Node.js)

```bash
# Create Next.js app with TypeScript
npx create-next-app@latest frontend --typescript --app --tailwind --eslint

# Visualization
cd frontend
npm install @nivo/core @nivo/line @nivo/heatmap @nivo/sankey @nivo/bar
npm install d3 @types/d3

# State management
npm install zustand

# Testing
npm install -D vitest @testing-library/react
```

### Docker Compose Services

```yaml
# docker-compose.yml structure
services:
  db:        # TimescaleDB (timescale/timescaledb:latest-pg17)
  redis:     # Redis 7.4 (redis:7.4-alpine)
  api:       # FastAPI (python:3.12-slim + uv)
  worker:    # Celery worker (same image as api)
  beat:      # Celery beat scheduler (same image as api)
  frontend:  # Next.js (node:22-alpine)
```

---

## Version Pinning Strategy

Pin **major.minor** in pyproject.toml / package.json, let patch versions float:

- `fastapi~=0.135` -- pin to 0.135.x
- `pandas~=3.0` -- pin to 3.0.x
- `statsmodels~=0.14.6` -- pin to 0.14.x
- `mesa~=3.5` -- pin to 3.5.x (do NOT use 4.0 alpha)
- `next: ^16.2.0` -- pin to 16.x

Use `uv lock` for reproducible backend builds. Use `package-lock.json` for reproducible frontend builds.

---

## Sources

- [FastAPI releases](https://github.com/fastapi/fastapi/releases) -- v0.135.1, March 2026
- [FastAPI official docs](https://fastapi.tiangolo.com/) -- Python 3.10+ requirement, SSE support
- [statsmodels PyPI](https://pypi.org/project/statsmodels/) -- v0.14.6, December 2025
- [statsmodels VAR/SVAR/VECM docs](https://www.statsmodels.org/stable/vector_ar.html) -- full vector autoregression module
- [statsmodels Markov regime-switching](https://www.statsmodels.org/stable/generated/statsmodels.tsa.regime_switching.markov_regression.MarkovRegression.html)
- [Mesa PyPI](https://pypi.org/project/Mesa/) -- v3.5.1, March 2026; requires Python >=3.12
- [Mesa JOSS paper](https://joss.theoj.org/papers/10.21105/joss.07668) -- Mesa 3 overview
- [scikit-learn IsolationForest docs](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html) -- v1.8.0
- [Next.js 16.2 blog](https://nextjs.org/blog/next-16-1) -- Turbopack stable, React Compiler stable
- [TimescaleDB releases](https://github.com/timescale/timescaledb/releases) -- v2.25, January 2026
- [TimescaleDB changelog](https://docs.timescale.com/about/latest/changelog/) -- PostgreSQL 17 support
- [pandas 3.0 release notes](https://pandas.pydata.org/docs/whatsnew/v3.0.0.html) -- January 2026
- [NumPy news](https://numpy.org/news/) -- v2.4.3, March 2026
- [Pydantic PyPI](https://pypi.org/project/pydantic/) -- v2.12/2.13 beta
- [redis-py docs](https://redis.readthedocs.io/en/stable/) -- v7.3.0, asyncio support
- [Alembic docs](https://alembic.sqlalchemy.org/) -- v1.18.4
- [SQLAlchemy asyncio docs](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) -- v2.0+
- [Nivo charts](https://nivo.rocks/) -- D3-based, SVG+Canvas rendering
- [fredapi PyPI](https://pypi.org/project/fredapi/) -- v0.5.2
- [beaapi GitHub](https://github.com/us-bea/beaapi) -- official BEA Python library
- [QuantEcon I-O lecture](https://intro.quantecon.org/input_output.html) -- NumPy/SciPy Leontief implementation reference
