# Phase 2: Feature Engineering and Core Dashboard - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Compute Marxist economic indicators (rate of profit, OCC, rate of surplus value, mass of profit, productivity-wage gap, financial fragility) from ingested NIPA data via a configurable translation engine, and display them in an interactive time-series dashboard with documented methodology. Two built-in methodologies (Shaikh/Tonak, Kliman) with plugin extensibility. Predictive modeling, structural analysis, and corporate concentration are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Chart visualization
- Recharts library for all interactive time-series charts
- Crisis annotations default to translucent shaded regions spanning crisis duration, toggleable to vertical lines or hidden entirely
- Six major US crisis episodes: Great Depression (1929-10 to 1933-03), Oil/Stagflation (1973-11 to 1975-03), Volcker Recession (1980-01 to 1982-11), Dot-com (2001-03 to 2001-11), Global Financial Crisis (2007-12 to 2009-06), COVID Recession (2020-02 to 2020-04)
- Date range selection via Recharts Brush component + preset buttons (5Y, 10Y, 25Y, 50Y, All)
- Dual y-axis support for overlaying indicators with different units/scales

### Methodology flexibility
- Shaikh/Tonak and Kliman as built-in methodology presets
- Plugin architecture: abstract base class for methodology mappers, registry for discovery, new methodologies added by implementing the interface
- Global methodology toggle for normal use (one active methodology at a time)
- Dedicated side-by-side comparison view showing same indicator computed under both methodologies on one chart
- LOCF-only frequency alignment (consistent with Phase 1 decision) — no per-indicator strategy selection

### Indicator overview layout
- Dashboard grid layout with hierarchy reflecting theoretical importance
- Hero row: 3 large cards with sparklines for TRPF trio (Rate of Profit, Organic Composition of Capital, Rate of Surplus Value)
- Secondary section below: smaller cards for remaining indicators (Mass of Profit, Productivity-Wage Gap, Credit-GDP Gap, Financial-to-Real Asset Ratio, Corporate Debt Service Ratio)
- Each indicator gets a dedicated route (/indicators/{indicator-slug}) with full chart and all controls
- Sidebar expands under "Indicators" to show: Overview, individual indicator links, Methodology
- Inline overlay on detail pages via "Add overlay" dropdown — layer additional indicators with dual y-axes

### Methodology docs UX
- Dedicated /indicators/methodology page as canonical reference
- Backend-driven documentation: methodology mappers define their own docs (formula, NIPA table/line references, interpretation notes) — served via API endpoint, guarantees docs stay in sync with computation code
- Side-by-side diff tables showing Shaikh/Tonak vs Kliman mappings for each indicator, highlighting where they diverge
- KaTeX for formula rendering (proper fractions, subscripts, Greek letters)
- Each indicator section shows: formula, NIPA component mappings with specific table/line references, interpretation notes

### Claude's Discretion
- Exact plugin architecture implementation details (ABC design, registration mechanism)
- Recharts chart styling, color palette, responsive breakpoints
- Sparkline implementation on overview cards
- API endpoint structure for indicators and methodology docs
- Loading states and error boundaries (DASH-08)
- Exact card sizing and grid responsive behavior

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- Card component (frontend/src/components/ui/card.tsx): shadcn/ui card for overview dashboard cards
- Table component (frontend/src/components/ui/table.tsx): for methodology comparison tables
- Skeleton component (frontend/src/components/ui/skeleton.tsx): loading states
- Badge component (frontend/src/components/ui/badge.tsx): indicator status/trend badges
- api.ts client (frontend/src/lib/api.ts): typed fetch wrapper with error handling — extend for indicator endpoints
- SeriesMetadata + Observation models (backend/ecpm/models/): existing data layer to query for indicator computation
- Redis caching pattern (backend/ecpm/cache.py): reuse for caching computed indicators
- LOCF frequency alignment (backend/ecpm/api/data.py:_align_frequency): reuse for cross-frequency indicator computation
- YAML series config loader (backend/ecpm/ingestion/series_config.py): pattern for config-driven indicator definitions

### Established Patterns
- Async SQLAlchemy with FastAPI dependency injection (get_db)
- Pydantic response schemas with model_validate
- Redis cache with sha256 key hashing and configurable TTL
- structlog for structured logging
- shadcn/ui + Tailwind CSS for dark theme, data-dense aesthetic
- Next.js App Router with page.tsx per route

### Integration Points
- Sidebar nav (frontend/src/components/layout/sidebar.tsx): "Indicators" link at /indicators currently disabled — enable and add sub-navigation
- API router (backend/ecpm/api/router.py): mount new indicator endpoints
- Observation table in TimescaleDB: source data for all indicator computations
- series_config.yaml: may need additional series for financial fragility indicators

</code_context>

<specifics>
## Specific Ideas

- Hero cards should give an immediate "state of the economy" feel — the TRPF trio is the theoretical nucleus
- Side-by-side methodology comparison is a key research feature — seeing how Shaikh/Tonak vs Kliman diverge on the same indicator is the analysis
- Crisis annotations should be subtle enough not to obscure data but clear enough to see patterns across decades
- Methodology docs must be authoritative — if the computation code changes, the docs change with it (backend-driven)
- Brush + preset buttons pattern borrowed from financial charting tools (Bloomberg, TradingView)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-feature-engineering-and-core-dashboard*
*Context gathered: 2026-03-23*
