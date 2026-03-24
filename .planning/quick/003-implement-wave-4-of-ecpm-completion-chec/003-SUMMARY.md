---
phase: quick
plan: 003
subsystem: frontend-backend-integration
tags: ["recharts", "forecast-overlay", "sidebar", "celery-beat", "ci-bands"]
dependency-graph:
  requires: ["quick-002"]
  provides: ["forecast-ui-integration", "forecasting-navigation", "auto-retrain"]
  affects: ["phase-04", "phase-05"]
tech-stack:
  added: []
  patterns: ["recharts-area-ci-bands", "toggle-based-feature-flag"]
file-tracking:
  key-files:
    created: []
    modified:
      - frontend/src/components/indicators/indicator-chart.tsx
      - frontend/src/app/indicators/[slug]/page.tsx
      - frontend/src/components/layout/sidebar.tsx
      - backend/ecpm/tasks/celery_app.py
decisions:
  - key: "ci-band-rendering"
    choice: "Recharts Area with [lower, upper] array format for gradient bands"
    rationale: "Allows stacked transparency (95% light, 68% darker) with single data structure"
  - key: "forecast-toggle-state"
    choice: "Per-page useState with lazy fetch on enable"
    rationale: "Avoids fetching forecast data until user explicitly requests it"
  - key: "retrain-schedule-offset"
    choice: "Hardcoded 5 minute offset from data refresh"
    rationale: "Simple and reliable; data refresh completes well within 5 minutes for ~200 series"
metrics:
  duration: "3min"
  completed: "2026-03-24"
---

# Quick Task 003: Wave 4 Phase 3 Integration Summary

Integrated Phase 3 forecasting capabilities into Phase 2 indicator UI with forecast overlay, enabled navigation, and auto-retrain scheduling.

## One-liner

Forecast toggle on indicator charts with CI band overlay, enabled sidebar navigation, and Celery Beat auto-retrain schedule.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add forecast overlay to indicator chart with toggle | a8fa462 | indicator-chart.tsx, [slug]/page.tsx |
| 2 | Enable Forecasting sidebar navigation | 3282c17 | sidebar.tsx |
| 3 | Add auto-retrain schedule to Celery Beat | 4401f0d | celery_app.py |

## Implementation Details

### Task 1: Forecast Overlay with Toggle

**indicator-chart.tsx changes:**
- Added `forecastData?: ForecastPoint[]` prop
- Imported `Area` from recharts for CI band rendering
- Added `mergeWithForecast()` helper function that:
  - Builds map from forecast dates to forecast points
  - Merges overlapping dates into existing data
  - Appends future forecast dates extending beyond historical data
- CI bands rendered as:
  - 95% CI: `fillOpacity={0.1}` (lighter)
  - 68% CI: `fillOpacity={0.2}` (darker)
- Forecast line: dashed (`strokeDasharray="5 5"`) with chart-3 color

**[slug]/page.tsx changes:**
- Added state: `showForecast`, `forecastData`, `forecastUnavailable`
- Added useEffect to fetch forecast when toggle enabled
- Graceful 404 handling: disables toggle if forecast unavailable
- Added Forecast toggle button in controls section (after Crises)
- Passes `forecastData` to IndicatorChart when enabled

### Task 2: Sidebar Navigation

Single line change: `enabled: false` to `enabled: true` for Forecasting phase entry.

### Task 3: Auto-retrain Schedule

Added `daily-model-retrain` entry to `celery_app.conf.beat_schedule`:
- Task: `ecpm.tasks.training_tasks.run_training_pipeline`
- Schedule: 5 minutes after data refresh (`fetch_schedule_minute + 5`)

## Verification Results

- Frontend builds successfully
- `forecastData` present in indicator-chart.tsx
- `showForecast` toggle present in page.tsx
- Forecasting `enabled: true` in sidebar.tsx
- `run_training_pipeline` in celery beat schedule

## Deviations from Plan

None - plan executed exactly as written.

## Next Steps

- Phase 4: Structural Analysis (Leontief I-O model, BEA integration)
- Phase 5: Concentration metrics (Nivo visualization)
