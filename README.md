# Economic Crisis Prediction Model (ECPM)

A data-driven platform that ingests US macroeconomic time-series data and translates it into the analytical categories of Marxist political economy — modeling, simulating, and forecasting the structural crisis tendencies inherent to capitalist accumulation.

Draws on the theoretical contributions of Marx, Engels, Lenin, Luxemburg, Leontief, and Beer to treat crises as endogenous expressions of capital's contradictions, not exogenous shocks.

## Architecture

```
┌─────────────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ FRED / BEA /    │────▶│   Ingestion  │────▶│  TimescaleDB  │────▶│   FastAPI    │
│    Census       │     │  (Celery)    │     │              │     │   Backend   │
└─────────────────┘     └─────────────┘     └──────────────┘     └──────┬──────┘
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

| # | Module                       | Status      | Description                                                            |
|---|------------------------------|-------------|------------------------------------------------------------------------|
| 1 | Data Ingestion               | Complete    | FRED/BEA/Census pipeline, TimescaleDB storage, scheduled fetching      |
| 2 | Feature Engineering          | Complete    | NIPA-to-Marx translation (rate of profit, OCC, exploitation rate)      |
| 3 | Predictive Modeling          | Complete    | VAR/SVAR forecasting, regime-switching, Composite Crisis Index         |
| 4 | Structural Analysis          | Complete    | Leontief I-O, shock propagation, reproduction schema                   |
| 5 | Corporate Concentration      | Complete    | HHI/CR4/CR8 metrics, concentration-to-crisis correlation analysis      |

## Features

### Phase 1: Data Ingestion
- **FRED API client** with 50+ macroeconomic series (GDP, employment, prices, interest rates)
- **BEA API client** for NIPA tables (national income, corporate profits, fixed assets)
- **Census API client** for Economic Census concentration data
- **Celery Beat scheduler** for automated daily data refresh
- **TimescaleDB storage** preserving native data frequencies

### Phase 2: Marxist Indicators
- **Rate of profit** computation with multiple methodologies (Shaikh-Tonak, Kliman, Moseley)
- **Organic composition of capital** (constant capital / variable capital)
- **Rate of surplus value** (exploitation rate)
- **Financial indicators**: credit-GDP gap, debt-service ratio, productivity-wage gap
- **Interactive comparison** of indicator values across methodologies
- **KaTeX formula rendering** showing computational derivations

### Phase 3: Predictive Modeling
- **VAR/SVAR forecasting** with 8-quarter horizon and confidence intervals
- **Markov regime-switching** detection (expansion vs. crisis states)
- **Composite Crisis Index** (0-100 scale) aggregating all crisis mechanisms
- **Historical backtesting** against major recessions (2001, 2008 GFC, 2020 COVID)
- **Forecast overlay** on indicator charts with toggle controls
- **Auto-retraining** pipeline via Celery Beat

### Phase 4: Structural Analysis
- **Leontief input-output analysis** from BEA Use/Make tables
- **Technical coefficient matrix** and **Leontief inverse** computation
- **Shock propagation simulation** — model sectoral demand shocks
- **Department I/II classification** (means of production vs. consumption goods)
- **Reproduction schema validation** (simple and expanded reproduction conditions)
- **Nivo heatmaps** for 71x71 I-O matrix visualization
- **Sankey diagrams** for inter-departmental flows

### Phase 5: Corporate Concentration
- **HHI (Herfindahl-Hirschman Index)** with DoJ/FTC threshold markers
- **CR4/CR8 concentration ratios** across NAICS industries
- **Trend analysis** tracking concentration over Census years
- **Lead-lag correlation** between concentration and Marxist indicators
- **Sparkline visualizations** for multi-industry comparison
- **Top correlated industries** identification

## Getting Started

### Prerequisites

- Docker and Docker Compose
- [FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html)
- [BEA API key](https://apps.bea.gov/API/signup/)
- [Census API key](https://api.census.gov/data/key_signup.html)

### Setup

```bash
# Clone and configure
cp .env.example .env
# Edit .env — add your FRED_API_KEY, BEA_API_KEY, and CENSUS_API_KEY

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
| `CENSUS_API_KEY`        | —                                                    | Census API key (required)     |
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
│   │   ├── api/                # FastAPI routers
│   │   │   ├── data.py         # Series data endpoints
│   │   │   ├── indicators.py   # Marxist indicator endpoints
│   │   │   ├── forecasting.py  # VAR/regime/crisis index endpoints
│   │   │   ├── structural.py   # I-O matrix and shock simulation
│   │   │   ├── concentration.py# HHI/CR4 and correlation endpoints
│   │   │   └── status.py       # Health and pipeline status
│   │   ├── clients/            # External API clients
│   │   │   ├── fred.py         # FRED API client
│   │   │   ├── bea.py          # BEA API client
│   │   │   └── census.py       # Census API client
│   │   ├── indicators/         # Marxist indicator computation
│   │   │   ├── shaikh_tonak.py # Shaikh-Tonak methodology
│   │   │   ├── kliman.py       # Kliman methodology
│   │   │   └── financial.py    # Financial indicators
│   │   ├── modeling/           # Predictive modeling
│   │   │   ├── var_forecast.py # VAR/SVAR forecasting
│   │   │   ├── regime_switching.py # Markov regime detection
│   │   │   └── crisis_index.py # Composite crisis index
│   │   ├── structural/         # I-O analysis
│   │   │   ├── leontief.py     # Leontief inverse computation
│   │   │   ├── departments.py  # Dept I/II classification
│   │   │   └── shock.py        # Shock propagation
│   │   ├── concentration/      # Concentration analysis
│   │   │   ├── metrics.py      # HHI/CR4/CR8 computation
│   │   │   └── correlation.py  # Lead-lag correlation
│   │   ├── ingestion/          # ETL pipeline orchestrator
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── tasks/              # Celery async tasks
│   │   ├── cache.py            # Redis caching layer
│   │   ├── config.py           # Pydantic settings
│   │   ├── database.py         # Async session factory
│   │   └── main.py             # FastAPI app entry point
│   └── tests/                  # pytest suite (183 tests)
├── frontend/
│   └── src/
│       ├── app/                # Next.js App Router pages
│       │   ├── page.tsx        # Dashboard home
│       │   ├── indicators/     # Indicator charts page
│       │   ├── forecasting/    # Forecasting and crisis index
│       │   ├── structural/     # I-O analysis and shocks
│       │   └── concentration/  # Concentration analysis
│       ├── components/         # React components
│       │   ├── data/           # Data display components
│       │   ├── layout/         # Sidebar, header, navigation
│       │   ├── charts/         # Recharts and Nivo wrappers
│       │   └── ui/             # shadcn/ui components
│       └── lib/                # API client, utilities
├── config/
│   └── timescaledb/            # DB init scripts
├── docs/
│   └── ECPM_Architecture.md
├── docker-compose.yml
├── docker-compose.override.yml
├── CHANGELOG.md                # Release notes
└── .env.example
```

## API Endpoints

### Data Ingestion
- `GET /api/data/series` — List all series metadata
- `GET /api/data/series/{series_id}` — Get series observations
- `POST /api/data/fetch` — Trigger manual data fetch

### Indicators
- `GET /api/indicators` — List all indicator summaries
- `GET /api/indicators/{slug}` — Get indicator time series
- `GET /api/indicators/{slug}/compare` — Compare across methodologies
- `GET /api/indicators/methodologies` — List methodology documentation

### Forecasting
- `GET /api/forecasting/forecasts` — Get VAR forecast results
- `GET /api/forecasting/regime` — Get current regime detection
- `GET /api/forecasting/crisis-index` — Get composite crisis index
- `GET /api/forecasting/backtests` — Get historical backtest results
- `POST /api/forecasting/train` — Trigger model retraining

### Structural Analysis
- `GET /api/structural/years` — Available I-O table years
- `GET /api/structural/matrix/{year}` — Get coefficient or inverse matrix
- `POST /api/structural/shock` — Run shock simulation
- `GET /api/structural/reproduction/{year}` — Get Dept I/II flows
- `GET /api/structural/critical-sectors/{year}` — Identify critical sectors

### Concentration Analysis
- `GET /api/concentration/industries` — List industries with concentration data
- `GET /api/concentration/{naics}/metrics` — Get HHI/CR4/CR8 for industry
- `GET /api/concentration/trends` — Get concentration trends over time
- `GET /api/concentration/correlations` — Get correlation with indicators

## License

[MIT](LICENSE)
