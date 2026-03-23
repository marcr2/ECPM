# Economic Crisis Prediction Model (ECPM)

A data-driven platform that ingests US macroeconomic time-series data and translates it into the analytical categories of Marxist political economy — modeling, simulating, and forecasting the structural crisis tendencies inherent to capitalist accumulation.

Draws on the theoretical contributions of Marx, Engels, Lenin, Luxemburg, Leontief, and Beer to treat crises as endogenous expressions of capital's contradictions, not exogenous shocks.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  FRED / BEA  │────▶│   Ingestion  │────▶│  TimescaleDB  │────▶│   FastAPI    │
│   (APIs)     │     │  (Celery)    │     │              │     │   Backend   │
└─────────────┘     └─────────────┘     └──────────────┘     └──────┬──────┘
                                              │                      │
                                              ▼                      ▼
                                        ┌──────────┐          ┌───────────┐
                                        │  Redis    │          │  Next.js   │
                                        │  (cache)  │          │  Frontend  │
                                        └──────────┘          └───────────┘
```

**Services** (all orchestrated via Docker Compose):

| Service      | Technology                  | Purpose                                    |
|--------------|-----------------------------|------------------------------------------- |
| **Backend**  | Python 3.12, FastAPI        | REST API, data ingestion, Celery tasks      |
| **Frontend** | Next.js 16, React 19        | Interactive dashboard (Tailwind + shadcn/ui)|
| **Database** | TimescaleDB (PostgreSQL 16) | Time-series storage at native frequency     |
| **Cache**    | Redis 7                     | Response caching + Celery task broker       |

## Crisis Typologies

The system synthesizes six crisis mechanisms into a unified analytical framework:

1. **TRPF** (Marx) — Tendency of the rate of profit to fall via rising organic composition
2. **Realization crisis** (Luxemburg/Marx) — Surplus value cannot be realized in circulation
3. **Disproportionality** (Marx Vol. II/Leontief) — Anarchic sectoral allocation breaks reproduction conditions
4. **Financial fragility** (Marx Vol. III/Engels) — Credit and fictitious capital mask and amplify contradictions
5. **Imperialist displacement** (Lenin/Luxemburg) — Crisis exported to periphery until exhaustion
6. **Cybernetic dysfunction** (Beer) — Capitalist economy structurally lacks viable feedback/control

## Modules

| # | Module                       | Status      | Description                                                       |
|---|------------------------------|-------------|-------------------------------------------------------------------|
| 1 | Data Ingestion               | Complete    | FRED/BEA pipeline, TimescaleDB storage, scheduled fetching        |
| 2 | Feature Engineering          | Not started | NIPA-to-Marx translation (rate of profit, OCC, surplus value)     |
| 3 | Predictive Modeling          | Not started | VAR/SVAR forecasting, regime-switching, Composite Crisis Index    |
| 4 | Structural Analysis          | Not started | Leontief I-O, shock propagation, reproduction schema              |
| 5 | Corporate Concentration      | Not started | Monopolization metrics, concentration-to-crisis mapping           |

## Getting Started

### Prerequisites

- Docker and Docker Compose
- [FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html)
- [BEA API key](https://apps.bea.gov/API/signup/)

### Setup

```bash
# Clone and configure
cp .env.example .env
# Edit .env — add your FRED_API_KEY and BEA_API_KEY

# Start all services
docker compose up
```

Once healthy, the services are available at:

| Service   | URL                       |
|-----------|---------------------------|
| Frontend  | http://localhost:3000      |
| Backend   | http://localhost:8000      |
| API docs  | http://localhost:8000/docs |

### Environment Variables

| Variable                | Default                                              | Description                   |
|-------------------------|------------------------------------------------------|-------------------------------|
| `FRED_API_KEY`          | —                                                    | FRED API key (required)       |
| `BEA_API_KEY`           | —                                                    | BEA API key (required)        |
| `DATABASE_URL`          | `postgresql+asyncpg://ecpm:ecpm_dev@timescaledb:5432/ecpm` | TimescaleDB connection  |
| `REDIS_URL`             | `redis://redis:6379/0`                               | Redis connection              |
| `CELERY_BROKER_URL`     | `redis://redis:6379/0`                               | Celery broker                 |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/1`                               | Celery result backend         |
| `FETCH_SCHEDULE_HOUR`   | `6`                                                  | Daily fetch hour (UTC)        |
| `FETCH_SCHEDULE_MINUTE` | `0`                                                  | Daily fetch minute            |
| `LOG_LEVEL`             | `INFO`                                               | Logging level                 |

### Local Development (without Docker)

**Backend:**

```bash
cd backend
pip install -e ".[dev]"
pytest
uvicorn ecpm.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Requires TimescaleDB and Redis running locally or via `docker compose up timescaledb redis`.

## Project Structure

```
.
├── backend/
│   ├── ecpm/
│   │   ├── api/            # FastAPI routers (data, status)
│   │   ├── clients/        # FRED and BEA API clients
│   │   ├── ingestion/      # ETL pipeline orchestrator
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── tasks/          # Celery async tasks
│   │   ├── cache.py        # Redis caching layer
│   │   ├── config.py       # Pydantic settings
│   │   ├── database.py     # Async session factory
│   │   └── main.py         # FastAPI app entry point
│   └── tests/              # pytest suite
├── frontend/
│   └── src/
│       ├── app/            # Next.js App Router pages
│       ├── components/     # React components (data, layout, ui)
│       └── lib/            # API client, utilities
├── config/
│   └── timescaledb/        # DB init scripts
├── docs/
│   └── ECPM_Architecture.md
├── docker-compose.yml
├── docker-compose.override.yml
└── .env.example
```

## License

[MIT](LICENSE)
