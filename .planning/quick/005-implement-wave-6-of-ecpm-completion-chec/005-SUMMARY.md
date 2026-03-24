---
phase: quick-005
plan: 1
subsystem: frontend
tags: [nivo, heatmap, sankey, structural-analysis, i-o-matrix]
dependency_graph:
  requires: [quick-004]
  provides: [structural-frontend, nivo-visualizations]
  affects: []
tech_stack:
  added: ["@nivo/heatmap@0.99.0", "@nivo/sankey@0.99.0", "@nivo/core@0.99.0"]
  patterns: [nivo-heatmap-canvas, nivo-sankey, tabbed-page-layout]
key_files:
  created:
    - frontend/src/lib/structural-api.ts
    - frontend/src/components/structural/coefficient-heatmap.tsx
    - frontend/src/components/structural/heatmap-drill-down.tsx
    - frontend/src/components/structural/reproduction-sankey.tsx
    - frontend/src/components/structural/proportionality-badge.tsx
    - frontend/src/components/structural/year-selector.tsx
    - frontend/src/components/structural/shock-simulator.tsx
    - frontend/src/components/structural/shock-results.tsx
    - frontend/src/app/structural/page.tsx
    - frontend/src/app/structural/layout.tsx
    - frontend/src/app/structural/loading.tsx
    - frontend/src/app/structural/error.tsx
  modified:
    - frontend/package.json
    - frontend/src/components/layout/sidebar.tsx
decisions:
  - key: nivo-canvas-renderer
    choice: HeatMapCanvas over HeatMap
    rationale: Canvas renderer handles 71x71 matrix performance better than SVG
  - key: sankey-flow-construction
    choice: Build flows from 2x2 matrix when sankey_data is null
    rationale: Graceful fallback when backend doesn't provide pre-built sankey structure
  - key: year-selector-native
    choice: Native HTML select instead of Base UI Select
    rationale: Simpler implementation, consistent styling with project patterns
metrics:
  duration: ~8min
  completed: 2026-03-24
---

# Quick Task 005: Phase 4 Frontend Summary

**One-liner:** Nivo-based I-O matrix heatmap and Sankey reproduction visualization with shock simulation UI for /structural route.

## What Was Built

### Task 1: Nivo Dependencies and API Client
- Installed @nivo/heatmap, @nivo/sankey, @nivo/core (all 0.99.0)
- Created `structural-api.ts` with 5 fetch functions matching backend Pydantic schemas
- Types: YearsResponse, MatrixResponse, ShockRequest, ShockResultResponse, ReproductionResponse, CriticalSectorsResponse

### Task 2: Nivo Visualization Components
- **CoefficientHeatmap**: HeatMapCanvas with diverging red-yellow-blue color scale, cell click handler
- **HeatmapDrillDown**: Base UI Dialog side panel showing cell details (row/col codes, coefficient value)
- **ReproductionSankey**: ResponsiveSankey for Dept I/II flows with c/v/s breakdown cards
- **ProportionalityBadge**: Expandable badge showing Marx's reproduction proportionality condition
- **YearSelector**: Native select dropdown for BEA benchmark years

### Task 3: Shock Simulation Components
- **ShockSimulator**: Industry dropdown, magnitude slider (-100% to +100%), shock type radio (supply/demand)
- **ShockResults**: Recharts BarChart with sorted impacts, top 10 filter, total impact stat, weakest link badge

### Task 4: /structural Page Route
- **page.tsx**: Three-tab layout (I-O Matrix, Shock Simulation, Reproduction Schema), year selector, refresh button
- **layout.tsx**: Breadcrumb navigation
- **loading.tsx**: Skeleton placeholders
- **error.tsx**: Next.js 16 unstable_retry pattern

### Task 5: Sidebar Navigation
- Changed Structural Analysis `enabled: false` to `enabled: true`
- Navigation to /structural now accessible from sidebar

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Heatmap renderer | HeatMapCanvas | 71x71 matrix (5,041 cells) requires canvas for performance |
| Sankey construction | Build from flows[][] | Backend may not provide sankey_data, fallback needed |
| Year selector | Native HTML select | Simpler than Base UI Select, consistent styling |
| Recharts tooltip | Custom content prop | Recharts 3 strict typing breaks formatter prop pattern |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed Nivo HeatMapCanvas data format**
- **Found during:** Task 2
- **Issue:** Nivo 0.99 expects `{ id: string, data: { x: string, y: number }[] }[]` format, not flat records
- **Fix:** Restructured data transformation in useMemo
- **Files modified:** coefficient-heatmap.tsx
- **Commit:** 50fb5b0

**2. [Rule 3 - Blocking] Fixed HeatMapCanvas minValue/maxValue props**
- **Found during:** Task 2
- **Issue:** minValue/maxValue are inside colors config object, not top-level props
- **Fix:** Moved to `colors: { type: "diverging", minValue, maxValue, ... }`
- **Files modified:** coefficient-heatmap.tsx
- **Commit:** 50fb5b0

**3. [Rule 1 - Bug] Fixed Recharts tooltip typing**
- **Found during:** Task 3
- **Issue:** Recharts 3 strict typing rejects formatter function signature
- **Fix:** Used custom `content` prop instead of `formatter`
- **Files modified:** shock-results.tsx
- **Commit:** e47f0ad

## Verification Results

- [x] `npm run build` passes - no TypeScript errors
- [x] `/structural` route in build output
- [x] HeatMapCanvas used in coefficient-heatmap.tsx
- [x] ResponsiveSankey used in reproduction-sankey.tsx
- [x] structural-api.ts exports 5 fetch functions
- [x] 7 structural components created (5 visualization + 2 shock)
- [x] Sidebar shows Structural Analysis as enabled

## Commit Log

| Commit | Message | Files |
|--------|---------|-------|
| 4f9d4d2 | feat(quick-005): install Nivo dependencies and create structural API client | package.json, structural-api.ts |
| 50fb5b0 | feat(quick-005): create Nivo visualization components | 5 component files |
| e47f0ad | feat(quick-005): create shock simulation components | shock-simulator.tsx, shock-results.tsx |
| 7b618d5 | feat(quick-005): create /structural page route with tabbed layout | page.tsx, layout.tsx, loading.tsx, error.tsx |
| 51a13f5 | feat(quick-005): enable Structural Analysis in sidebar navigation | sidebar.tsx |

## Next Phase Readiness

Phase 4 (Structural Analysis) frontend is complete. The UI can:
1. Display 71x71 I-O coefficient matrix as interactive heatmap
2. Simulate supply/demand shocks with visual impact analysis
3. Show Marx's reproduction schema as Sankey diagram with proportionality check

**Remaining for ECPM completion:**
- Phase 5: Concentration/Centralization metrics (frontend + backend)
- Integration testing across all phases
