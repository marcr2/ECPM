# Phase 4: Structural Analysis - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver Leontief input-output analysis: ingest BEA I-O tables (detailed 71-sector), compute technical coefficient matrix and Leontief inverse, simulate shock propagation (multi-sector scenarios + automatic weakest-link mode), aggregate into Department I / Department II with proportionality condition checks, and visualize via interactive heatmap and Sankey diagram. Predictive modeling (Phase 3) and corporate concentration (Phase 5) are separate phases.

</domain>

<decisions>
## Implementation Decisions

### I-O data scope
- Detailed 71-sector BEA I-O tables (not summary 15-sector)
- All available annual tables (~1997 onward) for time-series of structural change
- Extend existing BEA API client (`backend/ecpm/clients/bea.py`) using BEA InputOutput dataset endpoint — consistent with Phase 1 ingestion patterns
- Built-in canonical 71-to-2 Department I/II classification based on NAICS codes (manufacturing/mining/construction → Dept I, consumer goods/services → Dept II). Pre-defined, documented, not user-editable

### Heatmap visualization
- Aggregated overview (~15 sector groups) by default, click a cell to drill down into detailed sub-sectors within that group
- Sequential single-hue color scale (dark → bright on dark theme) for coefficient magnitude — zero/near-zero cells are background-dark, high coefficients glow
- Year selector dropdown to switch between annual I-O tables and see structural change over time
- Hover tooltips showing exact coefficient value + sector names
- Heatmap library: Claude's discretion — priority is fastest, most responsive rendering for 71x71 matrix (research D3, Nivo, canvas-based options and pick best performer)

### Shock simulation UX
- Three shock modes:
  1. **Multi-sector scenario builder**: select multiple sectors, set independent shock magnitudes for each (e.g., energy +30% AND manufacturing -20%)
  2. **Automatic "weakest link"**: system identifies most vulnerable sector(s) via Leontief inverse multipliers and simulates crisis from there — with full explanation of WHY that sector was chosen (vulnerability ranking, multiplier values, dependency counts)
- Results displayed as: ranked bar chart (largest impact first) + highlighted heatmap showing propagation path (shocked sectors and affected sectors glow). Side by side layout
- All computation server-side via backend API (NumPy/SciPy) — frontend sends shock params, receives results. Consistent with existing pattern

### Reproduction schema visualization
- Sankey diagram for Department I / Department II material flows
- Three toggleable depth levels: (1) department-only (2 nodes), (2) department + top sub-sectors (default), (3) full 71-sector view
- Proportionality conditions (e.g., I(v+s) ≥ II(c)) displayed inline on the Sankey — flows colored green/red based on whether conditions hold, with formula shown as tooltip
- Year selector dropdown (same pattern as heatmap) to track structural change over time
- Sankey library: Claude's discretion — research and pick best fit for React + dark theme

### Claude's Discretion
- Heatmap library choice (D3, Nivo, canvas-based — prioritize rendering performance)
- Sankey library choice
- Backend module structure for I-O computation (matrix storage, caching strategy)
- API endpoint design for I-O data, shock simulation, and reproduction schema
- Exact NAICS-to-Department mapping table
- Numerical stability checks for Leontief inverse (condition number thresholds, Hawkins-Simon)
- Redis caching strategy for computed matrices and simulation results
- Sector ordering/grouping logic for the aggregated heatmap view

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- BEA API client (`backend/ecpm/clients/bea.py`): extend for I-O table queries (InputOutput dataset)
- Card component (`frontend/src/components/ui/card.tsx`): for simulation controls, vulnerability ranking cards
- Skeleton component (`frontend/src/components/ui/skeleton.tsx`): loading states
- api.ts client (`frontend/src/lib/api.ts`): typed fetch wrapper — extend for I-O and simulation endpoints
- Redis caching (`backend/ecpm/cache.py`): cache Leontief inverse, simulation results
- Recharts (Phase 2): reuse for bar charts (shock results), sparklines
- Crisis annotations data (Phase 2): 6 episodes available if needed for temporal context

### Established Patterns
- Async SQLAlchemy with FastAPI dependency injection (get_db)
- Pydantic response schemas with model_validate
- Redis cache with sha256 key hashing and configurable TTL
- structlog for structured logging
- shadcn/ui + Tailwind CSS dark theme, data-dense aesthetic
- Next.js App Router with page.tsx per route
- Backend-driven methodology documentation pattern (Phase 2)
- Year/time selector dropdowns for temporal data

### Integration Points
- Sidebar nav (`frontend/src/components/layout/sidebar.tsx`): "Structural Analysis" at `/structural` currently disabled — enable and add sub-navigation
- API router (`backend/ecpm/api/router.py`): mount new I-O and simulation endpoints
- BEA ingestion pipeline: extend to include I-O table fetching alongside NIPA tables
- TimescaleDB: new tables for I-O coefficients, Leontief inverse results, sector classifications

</code_context>

<specifics>
## Specific Ideas

- Aggregated-then-drill-down heatmap: overview gives structural pattern at a glance, click to inspect individual sector dependencies
- "Automatic weakest link" shock mode is a key research feature — system identifies where the economy is most structurally vulnerable and explains why with metrics
- Multi-sector scenario builder allows testing complex crisis hypotheses (e.g., simultaneous energy + supply chain disruption)
- Inline proportionality conditions on the Sankey make the Marxist reproduction schema analysis visually immediate — green flows = conditions met, red = breakdown
- Three Sankey depth levels let the researcher zoom from macro (2 departments) to full resolution (71 sectors) without leaving the page
- Heatmap library choice should prioritize raw rendering speed for 71x71 — the researcher will switch years frequently

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-structural-analysis*
*Context gathered: 2026-03-23*
