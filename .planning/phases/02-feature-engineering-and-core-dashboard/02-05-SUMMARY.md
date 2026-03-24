---
phase: 02-feature-engineering-and-core-dashboard
plan: 05
subsystem: frontend
tags: [nextjs, react, dashboard, indicators, charts, methodology, recharts]

# Dependency graph
requires:
  - phase: 02-03
    provides: "Chart components (IndicatorChart, Sparkline, CrisisAnnotations, DateRangeControls, OverlaySelector, MethodologyToggle, Formula)"
  - phase: 02-04
    provides: "API endpoints (/api/indicators/, /api/indicators/{slug}, /api/indicators/methodology)"
provides:
  - "/indicators overview page with hero TRPF trio cards + 5 secondary indicator cards"
  - "/indicators/{slug} detail pages with interactive charts, Brush zoom, crisis annotations, dual y-axis overlay"
  - "/indicators/methodology page with KaTeX formulas and NIPA mapping tables"
  - "/indicators/compare page with side-by-side methodology comparison"
  - "Updated sidebar navigation with Indicators section enabled and sub-links"
affects: [03-05, user-facing-dashboard]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Next.js 16 async params pattern: const { slug } = await props.params"
    - "Hero/secondary card layout with responsive grid (3-col hero, 5-col secondary)"
    - "Client-side date range filtering for chart interactions"
    - "Collapsible sidebar sub-navigation for indicator hierarchy"

key-files:
  created:
    - "frontend/src/app/indicators/page.tsx"
    - "frontend/src/app/indicators/layout.tsx"
    - "frontend/src/app/indicators/[slug]/page.tsx"
    - "frontend/src/app/indicators/[slug]/loading.tsx"
    - "frontend/src/app/indicators/methodology/page.tsx"
    - "frontend/src/app/indicators/compare/page.tsx"
    - "frontend/src/components/indicators/indicator-card.tsx"
    - "frontend/src/components/indicators/methodology-table.tsx"
  modified:
    - "frontend/src/components/layout/sidebar.tsx"

key-decisions:
  - "Hero layout uses 3-card TRPF trio (Rate of Profit, OCC, Rate of Surplus Value) as most important indicators per Marxist crisis theory"
  - "Crisis annotations default to 'shaded' mode for better visual clarity on detail pages"
  - "Methodology toggle placed in layout.tsx to affect all indicator pages via shared state"
  - "Side-by-side methodology comparison gets dedicated /compare page rather than inline on detail pages"

patterns-established:
  - "Overview dashboard pattern: hero cards (large, prominent) + secondary cards (compact grid)"
  - "Interactive chart pattern: Brush zoom + crisis annotations + date presets + dual y-axis overlay on detail pages"
  - "Documentation pattern: LaTeX formula rendering + NIPA mapping tables + side-by-side diff tables"
  - "Sidebar collapsible sub-navigation pattern for hierarchical page structures"

requirements-completed: [DASH-01, DASH-02, DASH-03, DASH-04, DASH-05]

# Metrics
duration: 3min
completed: 2026-03-23
---

# Phase 2 Plan 5: Frontend Indicator Pages Summary

**Complete user-facing dashboard with overview cards, interactive detail pages, methodology documentation, and comparison views**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-23T17:08:59Z
- **Completed:** 2026-03-23T17:11:53Z
- **Tasks:** 2 (Task 1: overview + cards, Tasks 2-3: detail/methodology/compare pages)
- **Files created:** 8
- **Files modified:** 1

## Accomplishments
- Created indicator overview dashboard at /indicators with 3 hero TRPF cards and 5 secondary indicator cards
- Built 8 individual indicator detail pages at /indicators/{slug} with interactive Recharts charts, Brush zoom, crisis annotations, date range presets, and dual y-axis overlay
- Implemented methodology documentation page at /indicators/methodology with KaTeX-rendered LaTeX formulas and NIPA mapping tables
- Built side-by-side methodology comparison page at /indicators/compare showing Shaikh/Tonak vs. Kliman
- Created reusable indicator-card component with sparklines, trend badges, and click-to-detail navigation
- Created methodology-table component for side-by-side diff visualization
- Updated sidebar navigation to enable Indicators section with collapsible sub-links (Overview, 8 indicators, Methodology, Compare)
- All TypeScript compiles without errors
- Complete Phase 2 frontend culmination: Marxist indicators are now fully explorable via interactive dashboard

## Task Commits

Each task group was committed atomically:

1. **Task 1: Build overview dashboard and indicator card component** - `2ee83a2` (feat)
   - Files: page.tsx, layout.tsx, indicator-card.tsx, sidebar.tsx
2. **Tasks 2-3: Build detail page, methodology page, and comparison view** - `ba04816` (feat)
   - Files: [slug]/page.tsx, [slug]/loading.tsx, methodology/page.tsx, compare/page.tsx, methodology-table.tsx

## Files Created/Modified

**Created:**
- `frontend/src/app/indicators/page.tsx` - Overview dashboard with hero TRPF trio (Rate of Profit, OCC, Rate of Surplus Value) + 5 secondary cards (Mass of Profit, Productivity-Wage Gap, Credit-GDP Gap, Financial-Real Ratio, Debt Service Ratio). Responsive grid layout (3-col hero on lg, 5-col secondary on xl). Auto-refresh polling every 60s. Methodology toggle at top.
- `frontend/src/app/indicators/layout.tsx` - Layout wrapper for all /indicators/* pages with MethodologyToggle stored in URL search params. Provides methodology context to children.
- `frontend/src/app/indicators/[slug]/page.tsx` - Individual indicator detail page using Next.js 16 async params pattern. Interactive IndicatorChart with full data, crisis annotations (default shaded), Brush zoom, DateRangeControls (5Y/10Y/25Y/50Y/All presets), OverlaySelector for dual y-axis overlay, crisis annotation mode toggle (shaded/lines/hidden). Formula display below chart. Client-side date filtering.
- `frontend/src/app/indicators/[slug]/loading.tsx` - Loading skeleton for detail page (chart area + controls)
- `frontend/src/app/indicators/methodology/page.tsx` - Methodology documentation page rendering LaTeX formulas with KaTeX (<Formula> component from 02-03), NIPA component mapping tables (Marx Category, NIPA Table, Line, Description, Operation columns), interpretation notes, citations. Side-by-side diff tables showing where Shaikh/Tonak and Kliman diverge. Section headings with anchor links for each indicator.
- `frontend/src/app/indicators/compare/page.tsx` - Side-by-side methodology comparison view. Dropdown to select indicator. Chart showing both Shaikh/Tonak (blue) and Kliman (red) methodologies overlaid using IndicatorChart dual-line pattern. Legend identifying each line. Crisis annotations visible.
- `frontend/src/components/indicators/indicator-card.tsx` - Reusable overview card component. Props: indicator summary (from API), size (hero/secondary), def. Hero cards: larger (1/3 row), prominent sparkline, large latest value, trend badge (rising/falling/flat with colored arrow). Secondary cards: compact sparkline, smaller text. Uses shadcn/ui Card components. Entire card wrapped in Link to /indicators/{slug}. Shows units and formatted latest_date.
- `frontend/src/components/indicators/methodology-table.tsx` - Side-by-side diff table component for methodology comparison. Props: indicator, shaikhTonak, kliman. Two-column table (Shaikh/Tonak vs. Kliman). Rows: Formula, NIPA mappings, interpretation. Highlights cells where methodologies diverge (different bg color). Uses shadcn/ui Table.

**Modified:**
- `frontend/src/components/layout/sidebar.tsx` - Changed Indicators section to enabled: true. Added collapsible sub-navigation: Overview (/indicators), individual indicator links (/indicators/{slug}) for all 8 indicators, Methodology (/indicators/methodology), Compare (/indicators/compare). Sub-items styled as indented secondary links. Expand when pathname starts with /indicators, collapse otherwise.

## Decisions Made

- **Hero TRPF trio layout:** Per Marxist crisis theory, the three most important indicators (Rate of Profit, Organic Composition of Capital, Rate of Surplus Value) are given hero card prominence in a 3-column row at the top of the overview page. These directly measure the tendency of the rate of profit to fall (TRPF), the primary Marxist crisis mechanism. The remaining 5 indicators (Mass of Profit, Productivity-Wage Gap, Credit-GDP Gap, Financial-Real Ratio, Debt Service Ratio) are shown in a compact secondary grid below.

- **Crisis annotations default to shaded:** On detail pages, crisis annotations render as shaded vertical regions by default (rather than lines or hidden) because this provides the best visual clarity for seeing how indicator movements correlate with historical crisis periods (Great Depression, Stagflation, Great Recession, etc.).

- **Methodology toggle in layout.tsx:** The MethodologyToggle component is placed in the shared layout.tsx (not individual pages) so that switching between Shaikh/Tonak and Kliman methodologies affects all indicator pages via URL search params. This avoids per-page state management and provides consistent methodology context across the entire Indicators section.

- **Dedicated /compare page:** Rather than embedding side-by-side methodology comparison inline on detail pages (which would clutter the UI), a dedicated /indicators/compare page provides a focused comparison view. Users select an indicator from a dropdown, then see both methodologies overlaid on the same chart with different colors and a clear legend.

## Deviations from Plan

### Auto-fixed Issues
None - all tasks completed as specified in plan.

---

**Total deviations:** 0
**Impact on plan:** No deviations. Plan executed exactly as designed.

## Issues Encountered
None. All components integrated cleanly with Phase 2 Plans 02-03 (chart components) and 02-04 (API endpoints).

## User Setup Required
None - frontend pages consume existing backend API endpoints. No additional configuration or environment variables needed.

## Next Phase Readiness
- Phase 2 is now complete: all 8 Marxist indicators are computed, stored, served via API, and rendered in an interactive dashboard
- User can explore indicators at three levels:
  1. Overview (/indicators): glance at all 8 indicators with sparklines and trend badges
  2. Detail (/indicators/{slug}): deep dive with interactive charts, Brush zoom, crisis context, overlays, date ranges
  3. Methodology (/indicators/methodology, /indicators/compare): understand theoretical foundations and compare Shaikh/Tonak vs. Kliman approaches
- Phase 3 (Predictive Modeling and Crisis Index) can now build on these indicators to generate forecasts, detect regimes, and compute composite crisis index
- Phase 5 (Corporate Concentration Analysis) can correlate concentration metrics with these indicators

## Self-Check: PASSED

All 9 files verified present:
- ✅ frontend/src/app/indicators/page.tsx
- ✅ frontend/src/app/indicators/layout.tsx
- ✅ frontend/src/app/indicators/[slug]/page.tsx
- ✅ frontend/src/app/indicators/[slug]/loading.tsx
- ✅ frontend/src/app/indicators/methodology/page.tsx
- ✅ frontend/src/app/indicators/compare/page.tsx
- ✅ frontend/src/components/indicators/indicator-card.tsx
- ✅ frontend/src/components/indicators/methodology-table.tsx
- ✅ frontend/src/components/layout/sidebar.tsx (Indicators enabled)

Both task commits (2ee83a2, ba04816) verified in git log. TypeScript compilation passes. All DASH requirements (DASH-01 through DASH-05) completed.

---
*Phase: 02-feature-engineering-and-core-dashboard*
*Completed: 2026-03-23*
