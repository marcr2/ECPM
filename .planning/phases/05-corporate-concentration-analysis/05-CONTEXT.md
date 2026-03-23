# Phase 5: Corporate Concentration Analysis - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Ingest corporate concentration data (Census Bureau Economic Census), compute concentration metrics (CR4, CR8, HHI) by NAICS sector, map concentration trends to Marxist crisis indicator trajectories via rolling correlation, and display results in an indicator-first interactive dashboard at /concentration. Indicator computation (Phase 2), predictive modeling (Phase 3), and structural I-O analysis (Phase 4) are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Data source and ingestion
- Census Bureau Economic Census as primary data source — free, authoritative
- Coverage: 1992–present (1992, 1997, 2002, 2007, 2012, 2017, 2022 — 7 census years)
- Linear interpolation between census years to produce annual estimates
- Store both aggregate concentration ratios (CR4, CR8, HHI) AND named top 4 firms per sector
- Top firms stored at parent company level (e.g., Alphabet not YouTube), per CORP-01

### Concentration metrics
- Four metrics computed: CR4 (top 4 firm share), CR8 (top 8 firm share), HHI (Herfindahl-Hirschman Index), concentration trend rate (rate of change in CR4/HHI)
- Industry granularity: NAICS 3-digit (~20 subsectors)
- Sectors also aggregated into Marxist departments: Dept I (means of production) and Dept II (means of consumption) — connects to Phase 4 reproduction schema
- Top 4 firms tracked per sector (matches CR4 scope)

### Crisis mapping methodology
- Rolling Pearson/Spearman correlation between sector concentration metrics and crisis indicators
- Maps concentration against ALL Phase 2 Marxist indicators (rate of profit, OCC, rate of surplus value, mass of profit, productivity-wage gap, financial fragility metrics)
- Computed at both per-sector level AND aggregate level (economy-wide weighted average)
- Confidence score = composite 0–100 combining statistical significance (p-value) and effect size (r-coefficient)
- Raw p-value and r-coefficient available in tooltip for researcher validation

### Dashboard layout
- Hero overview section: economy-wide concentration trend chart + Dept I vs Dept II concentration comparison
- Below hero: indicator-first selector — pick a crisis indicator, see sectors ranked by correlation strength
- Sector ranking displayed with color-coded horizontal bars (green→red by correlation magnitude) + confidence score badge
- Clicking a sector opens detail panel with:
  - Dual-axis time-series chart (sector CR4/HHI on left axis, selected indicator on right axis) — reuses Phase 2 Recharts overlay pattern
  - Top 4 firms table (name, market share, share change since last census)
  - Confidence breakdown (r-coefficient, p-value, composite score, data point count)
  - Dept I/II context badge showing department membership and aggregate comparison
- Sidebar enables "Concentration" link (currently disabled from Phase 1)

### Claude's Discretion
- Census Bureau data parsing and ingestion pipeline details
- NAICS-to-Department I/II mapping specifics
- Rolling correlation window size and parameters
- Exact color palette for correlation strength visualization
- API endpoint structure for concentration data, correlations, and sector details
- Redis caching strategy for computed correlations
- Database schema for concentration data (new tables vs extending existing)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- Recharts library (Phase 2): reuse for concentration trend charts, dual-axis overlays, sparklines
- Sparkline component (frontend/src/components/indicators/sparkline.tsx): for sector overview cards
- Card component (frontend/src/components/ui/card.tsx): for sector cards, detail panels
- Table component (frontend/src/components/ui/table.tsx): for top firms table
- Badge component (frontend/src/components/ui/badge.tsx): for confidence scores, Dept I/II labels
- Indicator chart component (frontend/src/components/indicators/indicator-chart.tsx): pattern for dual-axis overlay
- api.ts client (frontend/src/lib/api.ts): extend for concentration endpoints
- Redis caching (backend/ecpm/cache.py): cache computed correlations
- Indicator registry + ABC pattern (backend/ecpm/indicators/): pattern for pluggable computation

### Established Patterns
- Async SQLAlchemy with FastAPI dependency injection (get_db)
- Pydantic response schemas with model_validate
- Redis cache with sha256 key hashing and configurable TTL
- structlog for structured logging
- shadcn/ui + Tailwind CSS dark theme, data-dense Bloomberg aesthetic
- Next.js App Router with page.tsx per route
- Sidebar navigation with section-based routing
- Config-driven data definitions (YAML series config pattern from Phase 1)

### Integration Points
- Sidebar nav (frontend/src/components/layout/sidebar.tsx): "Concentration" link currently disabled — enable
- API router (backend/ecpm/api/router.py): mount new concentration endpoints
- Phase 2 indicator computation results: source data for correlation mapping
- TimescaleDB: new tables for concentration data (sectors, firms, ratios, correlations)

</code_context>

<specifics>
## Specific Ideas

- Indicator-first navigation answers the theoretical question: "which sectors' monopolization most affects the rate of profit?" — the Marxist research question drives the UX
- Dept I/II aggregation directly connects to Marx's reproduction schema and Phase 4's structural analysis
- Color-coded bars for correlation strength maintain the data-dense Bloomberg/Grafana aesthetic established in Phase 1
- Confidence breakdown gives the researcher full statistical transparency — this is a research tool, not a simplified dashboard

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-corporate-concentration-analysis*
*Context gathered: 2026-03-23*
