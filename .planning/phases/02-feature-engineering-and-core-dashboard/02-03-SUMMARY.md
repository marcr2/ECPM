---
phase: 02-feature-engineering-and-core-dashboard
plan: 03
subsystem: ui
tags: [recharts, katex, chart-components, crisis-annotations, sparkline, loading-states]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: "Next.js frontend skeleton, shadcn/ui components (Button, Card, Skeleton), dark theme"
  - phase: 02-01
    provides: "Frontend data definitions (crisis-episodes.ts, indicator-defs.ts, indicators.ts), recharts + katex deps"
provides:
  - "IndicatorChart: Recharts ComposedChart with Brush, dual YAxis, crisis annotations"
  - "CrisisAnnotations: ReferenceArea overlays for 6 historical US crises"
  - "Sparkline: Mini LineChart for overview cards"
  - "FormulaDisplay: KaTeX renderToString for LaTeX formulas"
  - "DateRangeControls: 5Y/10Y/25Y/50Y/All preset buttons"
  - "OverlaySelector: Dropdown for adding dual y-axis overlay indicator"
  - "MethodologyToggle: Shaikh/Tonak vs Kliman TSSI button group"
  - "loading.tsx: Skeleton grid for indicators section"
  - "error.tsx: Next.js 16 error boundary with unstable_retry"
affects: [02-05-indicator-pages]

# Tech tracking
tech-stack:
  added: []
  patterns: [recharts-composed-chart, crisis-reference-area, katex-render-to-string, next16-error-boundary]

key-files:
  created:
    - frontend/src/components/indicators/indicator-chart.tsx
    - frontend/src/components/indicators/crisis-annotations.tsx
    - frontend/src/components/indicators/sparkline.tsx
    - frontend/src/components/indicators/formula-display.tsx
    - frontend/src/components/indicators/date-range-controls.tsx
    - frontend/src/components/indicators/overlay-selector.tsx
    - frontend/src/components/indicators/methodology-toggle.tsx
    - frontend/src/app/indicators/loading.tsx
    - frontend/src/app/indicators/error.tsx
  modified: []

key-decisions:
  - "Used ComposedChart (not LineChart) to support mixing Line + ReferenceArea in same chart"
  - "Brush tickFormatter shows year-only for compactness at bottom zoom bar"
  - "Overlay line uses strokeDasharray to visually distinguish from primary indicator"
  - "Error boundary uses Button component for consistent styling with dark theme"

patterns-established:
  - "Recharts ComposedChart pattern: dual YAxis + CrisisAnnotations + Brush for all indicator charts"
  - "KaTeX direct renderToString pattern (no react-katex wrapper) for React 19 compatibility"
  - "Next.js 16 error.tsx uses unstable_retry (not reset) for error recovery"

requirements-completed: [DASH-01, DASH-02, DASH-03, DASH-08]

# Metrics
duration: 6min
completed: 2026-03-23
---

# Phase 2 Plan 3: Frontend Chart Components Summary

**Recharts ComposedChart component library with crisis annotations, sparkline, KaTeX formula display, and Next.js 16 loading/error boundaries for the indicators dashboard**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-23T20:21:34Z
- **Completed:** 2026-03-23T20:27:57Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Built IndicatorChart with Recharts ComposedChart supporting Brush zoom, dual YAxis overlay, and CrisisAnnotations as translucent ReferenceArea regions
- Created 7 reusable indicator components (chart, crisis annotations, sparkline, formula display, date range controls, overlay selector, methodology toggle)
- Implemented Next.js 16 loading.tsx with skeleton grid (3 hero + 5 secondary cards) and error.tsx with unstable_retry

## Task Commits

Each task was committed atomically:

1. **Task 1: Install dependencies and create shared data definitions** - `b975e64` (feat, pre-existing from Plan 02-01)
2. **Task 2: Build reusable chart components and loading/error states** - `27b69f5` (feat)

## Files Created/Modified
- `frontend/src/components/indicators/indicator-chart.tsx` - Main Recharts ComposedChart with Brush, dual YAxis, CrisisAnnotations
- `frontend/src/components/indicators/crisis-annotations.tsx` - ReferenceArea overlays for 6 crisis episodes (shaded/lines/hidden modes)
- `frontend/src/components/indicators/sparkline.tsx` - Mini LineChart for overview cards, no axes/tooltip
- `frontend/src/components/indicators/formula-display.tsx` - KaTeX renderToString for LaTeX formula rendering
- `frontend/src/components/indicators/date-range-controls.tsx` - Preset buttons (5Y/10Y/25Y/50Y/All)
- `frontend/src/components/indicators/overlay-selector.tsx` - Dropdown for adding second indicator with dual y-axis
- `frontend/src/components/indicators/methodology-toggle.tsx` - Button group toggle for methodology selection
- `frontend/src/app/indicators/loading.tsx` - Server component skeleton loading state
- `frontend/src/app/indicators/error.tsx` - Client component error boundary with unstable_retry

## Decisions Made
- Used ComposedChart (not LineChart) to support mixing Line + ReferenceArea child components in the same chart
- Overlay indicator line uses strokeDasharray="5 3" to visually distinguish it from the primary indicator
- Brush component at bottom uses year-only tick formatting for compactness
- Error boundary uses shadcn/ui Button for consistent styling rather than raw HTML button
- FormulaDisplay uses katex.renderToString directly (no react-katex wrapper) for React 19 compatibility

## Deviations from Plan

### Task 1 Pre-existing Work

Task 1 deliverables (recharts/katex installation, crisis-episodes.ts, indicator-defs.ts, indicators.ts) were already present in the codebase from Plan 02-01 commit `b975e64`. The files were identical to the plan specification, so no separate commit was needed. Task 2 was the actual new implementation work for this plan.

---

**Total deviations:** 0 auto-fixed. 1 pre-existing overlap noted.
**Impact on plan:** No scope creep. Task 1 was effectively a no-op since 02-01 already delivered those files.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All chart components ready for composition into full indicator pages (Plan 02-05)
- Components designed to consume data from backend API endpoints (Plan 02-04)
- Loading/error boundaries in place for the /indicators route segment
- Crisis episodes, indicator definitions, and API client all available for page-level integration

## Self-Check: PASSED

- All 9 created files verified present on disk
- Commit 27b69f5 (Task 2) verified in git log
- Commit b975e64 (Task 1, from Plan 02-01) verified in git log
- SUMMARY.md verified present at expected path

---
*Phase: 02-feature-engineering-and-core-dashboard*
*Completed: 2026-03-23*
