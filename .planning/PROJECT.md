# Economic Crisis Prediction Model (ECPM)

## What This Is

A data-driven platform that ingests macroeconomic time-series data and translates it into the analytical categories of Marxist political economy — modeling, simulating, and forecasting the structural crisis tendencies inherent to capitalist accumulation. It draws on the theoretical contributions of Marx, Engels, Lenin, Luxemburg, Leontief, and Beer to treat crises as endogenous expressions of capital's contradictions, not exogenous shocks.

Built as a personal research tool running locally via Docker, with a Next.js dashboard for interactive exploration.

## Core Value

The system must ingest real macroeconomic data (FRED/BEA) and compute Marxist economic indicators — rate of profit, organic composition of capital, rate of surplus value — that are visible and explorable in a web dashboard. If nothing else works, this pipeline must.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Automated data ingestion from FRED and BEA APIs
- [ ] Feature engineering: profitability indicators (rate of profit, OCC, rate of surplus value, mass vs. rate divergence)
- [ ] Feature engineering: realization gap indicators (productivity-wage divergence, inventory-to-sales, consumer debt-to-income)
- [ ] Feature engineering: sectoral disproportionality via Leontief I-O analysis
- [ ] Feature engineering: fictitious capital / financial fragility indicators
- [ ] Feature engineering: imperialist displacement indicators (capital flows, terms of trade, peripheral debt)
- [ ] Feature engineering: cybernetic viability indicators (regulatory lag, planning horizon, feedback integrity)
- [ ] Predictive modeling: VAR/SVAR econometric forecasting
- [ ] Anomaly detection for crisis fingerprints (Isolation Forests, Markov regime-switching)
- [ ] Leontief structural shock propagation simulation
- [ ] Agent-based simulation of capitalist dynamics (Mesa)
- [ ] Composite Crisis Probability Index
- [ ] Next.js dashboard with interactive time-series charts
- [ ] Reproduction schema visualizer (Leontief I-O matrix view)
- [ ] Cybernetic system diagram (Beer VSM)
- [ ] Simulation control panel for agent-based model
- [ ] Crisis probability gauge with mechanism decomposition
- [ ] Theoretical annotation layer linking indicators to sources
- [ ] Historical calibration against known crisis episodes (1929, 1973, 2001, 2008, etc.)
- [ ] Dockerized local deployment (Docker Compose)

### Out of Scope

- Multi-user authentication — personal research tool, single user
- Cloud deployment (AWS/GCP) — local Docker only for MVP
- Mobile-responsive design — desktop-first research interface
- Real-time streaming data — batch ingestion is sufficient
- Production monitoring/alerting infrastructure

## Context

The architecture document (`ECPM_Architecture.md`) provides the complete theoretical framework and technical specifications. The system synthesizes six crisis typologies:

1. **TRPF** (Marx) — Tendency of the rate of profit to fall via rising organic composition
2. **Realization crisis** (Luxemburg/Marx) — Surplus value cannot be realized in circulation
3. **Disproportionality** (Marx Vol. II/Leontief) — Anarchic sectoral allocation breaks reproduction conditions
4. **Financial fragility** (Marx Vol. III/Engels) — Credit and fictitious capital mask and amplify contradictions
5. **Imperialist displacement** (Lenin/Luxemburg) — Crisis exported to periphery until exhaustion
6. **Cybernetic dysfunction** (Beer) — Capitalist economy structurally lacks viable feedback/control

The MVP approach builds a wired skeleton: all 4 modules (A–D) exist with real interfaces, but only the core data→indicators→basic models→dashboard path is fully functional. Future milestones flesh out advanced modeling, simulation, and visualization.

**Primary data sources for MVP:** FRED (Federal Reserve Economic Data), BEA (Bureau of Economic Analysis). Additional sources (BLS, World Bank, IMF, BIS, OECD) added in later milestones.

## Constraints

- **Tech stack**: Python 3.10+ backend (FastAPI), Next.js frontend, TimescaleDB, Redis, Docker Compose — as specified in architecture doc
- **Data access**: FRED API key required; BEA API key required; some data sources may have rate limits or access restrictions
- **Scope**: MVP proves the core pipeline works; advanced modules (agent-based sim, full Leontief analysis, periphery modeling) are stubbed with interfaces defined
- **Deployment**: Local Docker Compose only — no cloud infrastructure
- **User**: Single researcher, no auth needed

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Wired skeleton approach | All 4 modules exist with interfaces; MVP path functional, rest stubbed. Enables incremental milestones. | — Pending |
| Live APIs over sample data | Real FRED/BEA data from the start — the pipeline IS the product | — Pending |
| Next.js over Streamlit | Architecture doc specifies React/Next.js; user confirmed. Better for the rich interactive visualizations planned. | — Pending |
| Local Docker over cloud | Personal research tool; simplest deployment for MVP | — Pending |
| TimescaleDB for time-series | PostgreSQL extension optimized for the multi-resolution economic time-series data central to the system | — Pending |

---
*Last updated: 2026-03-23 after initialization*
