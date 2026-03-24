# Changelog

All notable changes to ECPM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-24

### Added

**Phase 1: Foundation and Data Ingestion**
- FRED API client with 50+ macroeconomic series configuration
- BEA API client for NIPA tables (national income, fixed assets, corporate profits)
- Census API client for Economic Census concentration data
- PostgreSQL/TimescaleDB storage with Alembic migrations
- Redis caching layer with configurable TTLs
- Celery task pipeline with Beat scheduler for automated data refresh
- Next.js 16 dashboard with shadcn/ui components
- Docker Compose orchestration for all services

**Phase 2: Feature Engineering and Core Dashboard**
- Marxist indicator computation engine
- Rate of profit (TRPF) with multiple methodologies:
  - Shaikh-Tonak: surplus value / (constant capital + variable capital)
  - Kliman: historical-cost fixed assets in denominator
  - Moseley: productive labor distinction
- Organic composition of capital (OCC): c/v ratio
- Rate of surplus value (exploitation rate): s/v ratio
- Financial indicators:
  - Credit-to-GDP gap with one-sided HP filter (BIS methodology)
  - Debt-service ratio
  - Productivity-wage gap
  - Financial-to-real ratio
- Interactive indicator charts with methodology comparison
- KaTeX formula rendering for mathematical derivations
- Methodology documentation with NIPA mappings and academic citations

**Phase 3: Predictive Modeling and Crisis Index**
- VAR (Vector Autoregression) forecasting with lag selection (AIC/BIC)
- SVAR (Structural VAR) with Cholesky identification
- 8-quarter forecast horizon with 95% confidence intervals
- Markov regime-switching model (2-state: expansion/crisis)
- Transition probability matrix and regime probabilities
- Composite Crisis Index (0-100 scale) aggregating:
  - TRPF component (inverted profit rate)
  - OCC component (rising organic composition)
  - Financial component (credit-GDP gap, debt-service ratio)
  - Disproportionality component (from I-O analysis)
- Historical backtesting against major recessions:
  - 2001 Dot-com recession
  - 2008 Global Financial Crisis
  - 2020 COVID-19 recession
- Forecast overlay toggle on indicator charts
- Auto-retraining pipeline via Celery Beat (5-minute offset from data refresh)
- SSE streaming for training progress notifications

**Phase 4: Structural Analysis**
- BEA Input-Output table ingestion (Use and Make tables)
- Technical coefficient matrix (A) computation
- Leontief inverse matrix (I-A)^-1 with Hawkins-Simon stability check
- Output multipliers and sectoral linkages
- Shock propagation simulation:
  - Single-sector demand shocks
  - Multi-sector shock superposition
  - Impact ranking and total effect calculation
- Department I/II classification (Marxist reproduction schema):
  - Department I: means of production (NAICS manufacturing, mining, utilities)
  - Department II: consumption goods (retail, food, healthcare, etc.)
- Reproduction conditions validation:
  - Simple reproduction: I(c+v+s) = I(c) + II(c)
  - Expanded reproduction with surplus allocation
- Constant capital (c), variable capital (v), surplus value (s) decomposition
- Critical sector identification via backward/forward linkages
- Nivo HeatMapCanvas for 71x71 I-O matrix visualization
- Sankey diagram for inter-departmental flows
- Year-over-year matrix comparison

**Phase 5: Corporate Concentration Analysis**
- Census Bureau API integration for Economic Census data
- Concentration metrics:
  - HHI (Herfindahl-Hirschman Index) with DoJ/FTC thresholds:
    - < 1500: Unconcentrated
    - 1500-2500: Moderately concentrated
    - > 2500: Highly concentrated
  - CR4 (4-firm concentration ratio)
  - CR8 (8-firm concentration ratio)
- NAICS industry classification support
- Trend analysis across Census years (2002-2022)
- Lead-lag correlation engine:
  - Tests correlations at [0, 3, 6, 12, 18, 24] month offsets
  - Confidence scoring based on correlation strength and sample size
  - Identifies optimal lag for each industry-indicator pair
- Top correlated industries ranking
- Sparkline visualizations for multi-industry comparison
- Concentration-to-crisis mapping analysis

### Technical Details

**Backend Stack:**
- Python 3.12+
- FastAPI 0.135+ with async/await
- SQLAlchemy 2.0 (async) with asyncpg driver
- Celery 5.6 with Redis broker
- statsmodels for VAR/regime-switching models
- numpy/scipy for matrix operations
- pandas for time-series manipulation
- structlog for structured logging

**Frontend Stack:**
- Next.js 16 with App Router
- React 19 with Server Components
- TypeScript 5.7
- Tailwind CSS with dark theme
- shadcn/ui component library
- Recharts for time-series charts
- Nivo for heatmaps and Sankey diagrams
- TanStack Table for data grids
- KaTeX for mathematical formula rendering

**Infrastructure:**
- Docker Compose with 4 services
- TimescaleDB (PostgreSQL 16 with time-series extensions)
- Redis 7 for caching and Celery broker
- Alembic for database migrations

### Known Limitations

- BEA I-O tables require manual annual update (API provides only latest year)
- Census concentration data has ~2 year reporting lag
- Regime-switching may produce spurious transitions on short time series (<40 observations)
- SVAR identification assumes recursive (Cholesky) structure
- Department I/II classification uses simplified NAICS mapping (no detailed BLS input)

### Dependencies

**Runtime:**
- Python 3.12+
- Node.js 22+
- PostgreSQL 16 with TimescaleDB extension
- Redis 7
- Docker and Docker Compose (recommended)

**API Keys Required:**
- [FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html)
- [BEA API key](https://apps.bea.gov/API/signup/)
- [Census API key](https://api.census.gov/data/key_signup.html)

### Migration Notes

This is the initial release. No migration from previous versions required.

---

## [Unreleased]

### Planned
- Real-time data streaming via WebSocket
- Additional methodologies (Duménil-Lévy, Carchedi)
- International data sources (Eurostat, OECD)
- Interactive what-if scenario modeling
- PDF report generation
- User authentication and saved views
