# Phase 2: Feature Engineering and Core Dashboard - Research

**Researched:** 2026-03-23
**Domain:** NIPA-to-Marx translation engine, Recharts interactive charting, KaTeX formula rendering, FastAPI indicator API
**Confidence:** HIGH

## Summary

Phase 2 bridges raw NIPA/FRED data (ingested in Phase 1) to computed Marxist economic indicators displayed in an interactive dashboard. The phase has two major technical axes: (1) a backend translation engine that maps NIPA line items to Marxian categories (surplus value, variable capital, constant capital) via configurable methodology presets, and (2) a frontend charting layer using Recharts 3.x for time-series visualization with crisis annotations, dual y-axes, and brush-based date range selection.

The backend domain requires careful attention to the economic methodology. Shaikh/Tonak and Kliman differ in how they handle productive/unproductive labor distinctions and historical-cost vs. current-cost asset valuation. The plugin architecture (ABC + registry pattern) is well-supported by Python's `abc` module and is the standard approach for extensible computation engines. The frontend domain is straightforward: Recharts 3.x provides all needed components (ComposedChart, ReferenceArea, Brush, multiple YAxis), and KaTeX provides server-safe formula rendering via `renderToString`.

**Primary recommendation:** Build the methodology engine as an abstract base class with a registry, compute indicators lazily from the Observation table using async SQLAlchemy queries, cache results in Redis, and expose via new `/api/indicators/` endpoints that the Recharts-based frontend consumes.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Recharts library for all interactive time-series charts
- Crisis annotations default to translucent shaded regions spanning crisis duration, toggleable to vertical lines or hidden entirely
- Six major US crisis episodes: Great Depression (1929-10 to 1933-03), Oil/Stagflation (1973-11 to 1975-03), Volcker Recession (1980-01 to 1982-11), Dot-com (2001-03 to 2001-11), Global Financial Crisis (2007-12 to 2009-06), COVID Recession (2020-02 to 2020-04)
- Date range selection via Recharts Brush component + preset buttons (5Y, 10Y, 25Y, 50Y, All)
- Dual y-axis support for overlaying indicators with different units/scales
- Shaikh/Tonak and Kliman as built-in methodology presets
- Plugin architecture: abstract base class for methodology mappers, registry for discovery, new methodologies added by implementing the interface
- Global methodology toggle for normal use (one active methodology at a time)
- Dedicated side-by-side comparison view showing same indicator computed under both methodologies on one chart
- LOCF-only frequency alignment (consistent with Phase 1 decision) -- no per-indicator strategy selection
- Dashboard grid layout with hierarchy reflecting theoretical importance
- Hero row: 3 large cards with sparklines for TRPF trio (Rate of Profit, Organic Composition of Capital, Rate of Surplus Value)
- Secondary section below: smaller cards for remaining indicators (Mass of Profit, Productivity-Wage Gap, Credit-GDP Gap, Financial-to-Real Asset Ratio, Corporate Debt Service Ratio)
- Each indicator gets a dedicated route (/indicators/{indicator-slug}) with full chart and all controls
- Sidebar expands under "Indicators" to show: Overview, individual indicator links, Methodology
- Inline overlay on detail pages via "Add overlay" dropdown -- layer additional indicators with dual y-axes
- Dedicated /indicators/methodology page as canonical reference
- Backend-driven documentation: methodology mappers define their own docs (formula, NIPA table/line references, interpretation notes) -- served via API endpoint, guarantees docs stay in sync with computation code
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

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FEAT-01 | Configurable NIPA-to-Marx translation engine with Shaikh/Tonak methodology | ABC plugin architecture pattern, NIPA table mappings documented below |
| FEAT-02 | Rate of profit: r = S / (C + V) from NIPA proxies | Shaikh/Tonak and Kliman NIPA table/line mappings identified |
| FEAT-03 | Organic composition of capital: OCC = C/V from NIPA proxies | Same NIPA mappings as FEAT-02, ratio computation |
| FEAT-04 | Rate of surplus value: s/v = (Value Added - Wages) / Wages | NIPA Table 1.12 national income, compensation series |
| FEAT-05 | Mass of profit + mass vs. rate divergence tracking | Absolute surplus computed alongside rate; divergence is display-layer |
| FEAT-06 | Productivity-wage gap over rolling windows | FRED series OPHNFB (output per hour) and PRS85006092 (real compensation per hour) already ingested |
| FEAT-07 | Financial fragility: credit-to-GDP gap, financial-to-real asset ratio, corporate debt service | BIS HP-filter methodology for credit gap; FRED financial series already ingested |
| FEAT-08 | Documentation of every NIPA-to-Marx mapping with table/line references | Backend-driven docs pattern; methodology mappers self-document |
| FEAT-09 | Explicit frequency alignment at model-time with documented strategy parameter | LOCF already implemented in Phase 1 data.py; reuse and formalize |
| DASH-01 | Interactive time-series charts with zoom, pan, date range selection | Recharts 3.x ComposedChart + Brush component |
| DASH-02 | Overlay multiple indicators with dual y-axes | Recharts multiple YAxis with yAxisId + orientation props |
| DASH-03 | Crisis episode annotations (shaded regions/vertical lines) | Recharts ReferenceArea component with x1/x2/fill/fillOpacity |
| DASH-04 | Indicator overview/summary page | Dashboard grid with Card + sparkline pattern |
| DASH-05 | Methodology documentation page | KaTeX renderToString + backend-served docs API |
| DASH-08 | Loading states and error boundaries | Next.js 16 loading.tsx + error.tsx file conventions |
</phase_requirements>

## Standard Stack

### Core (Backend -- New for Phase 2)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python `abc` module | stdlib | Abstract base class for methodology plugin | Built-in, no dependency; standard pattern for extensible computation engines |
| pandas | >=2.2 (already installed) | DataFrame operations for indicator computation | Already in project; needed for rolling windows, alignment, arithmetic |
| numpy | (pandas dependency) | Numerical operations | Comes with pandas; needed for HP filter in credit-to-GDP gap |

### Core (Frontend -- New for Phase 2)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| recharts | ^3.8.0 | Interactive time-series charts, Brush, ReferenceArea, dual YAxis | User decision; latest stable is 3.8.0 (March 2026) |
| katex | ^0.16.40 | LaTeX formula rendering via `renderToString` | Latest stable; use directly instead of react-katex wrapper for React 19 compatibility |

### Supporting (Frontend)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lucide-react | already installed | Icons for indicator cards, navigation | Consistent with Phase 1 |
| shadcn/ui Card, Table, Skeleton, Badge | already installed | Overview cards, methodology tables, loading states | Consistent with Phase 1 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| recharts | visx, nivo | Recharts is user decision; visx is lower-level, nivo heavier |
| katex directly | react-katex | react-katex 3.1.0 may not support React 19; direct katex + dangerouslySetInnerHTML is safer and simpler |
| Python ABC | Protocol classes | ABC gives better error messages at instantiation time; Protocol is more for structural subtyping |

**Installation:**
```bash
# Frontend
cd frontend && npm install recharts katex

# Backend -- no new packages needed (abc is stdlib, pandas already installed)
```

## Architecture Patterns

### Recommended Backend Structure
```
backend/ecpm/
  indicators/
    __init__.py              # Registry + public API
    base.py                  # MethodologyMapper ABC
    registry.py              # MethodologyRegistry class
    shaikh_tonak.py          # Shaikh/Tonak implementation
    kliman.py                # Kliman TSSI implementation
    definitions.py           # Indicator enum/constants (slugs, display names, units)
    computation.py           # Indicator computation orchestrator (fetches data, calls mapper, caches)
  api/
    indicators.py            # FastAPI router for /api/indicators/*
    methodology.py           # FastAPI router for /api/indicators/methodology
```

### Recommended Frontend Structure
```
frontend/src/
  app/
    indicators/
      page.tsx                    # Overview dashboard (DASH-04)
      layout.tsx                  # Indicators layout (wraps all indicator pages)
      loading.tsx                 # Loading state for overview
      error.tsx                   # Error boundary for indicators section
      methodology/
        page.tsx                  # Methodology docs page (DASH-05)
      [slug]/
        page.tsx                  # Individual indicator detail page (DASH-01, DASH-02, DASH-03)
        loading.tsx               # Loading state for detail
      compare/
        page.tsx                  # Side-by-side methodology comparison view
  components/
    indicators/
      indicator-chart.tsx         # Recharts ComposedChart with Brush, ReferenceArea, dual YAxis
      crisis-annotations.tsx      # ReferenceArea overlays for crisis episodes
      indicator-card.tsx          # Overview card with sparkline
      sparkline.tsx               # Mini Recharts LineChart for cards
      date-range-controls.tsx     # Preset buttons (5Y, 10Y, 25Y, 50Y, All) + Brush integration
      overlay-selector.tsx        # "Add overlay" dropdown for dual y-axis
      methodology-toggle.tsx      # Global methodology selector
      formula-display.tsx         # KaTeX rendering component
      methodology-table.tsx       # Side-by-side diff table for methodologies
  lib/
    indicators.ts                 # API client functions for indicator endpoints
    crisis-episodes.ts            # Crisis episode definitions (dates, labels, colors)
    indicator-defs.ts             # Indicator slug/name/unit mapping (mirrors backend)
```

### Pattern 1: Methodology Mapper ABC

**What:** Abstract base class defining the interface every methodology must implement.
**When to use:** Always -- this is the core extensibility mechanism.

```python
# backend/ecpm/indicators/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class NIPAMapping:
    """Documents one NIPA-to-Marx mapping."""
    marx_category: str           # e.g., "surplus_value"
    nipa_table: str              # e.g., "T11200"
    nipa_line: int               # e.g., 1
    nipa_description: str        # e.g., "National income"
    operation: str               # e.g., "subtract", "add", "direct"
    notes: str = ""


@dataclass
class IndicatorDoc:
    """Self-documentation for one indicator under a methodology."""
    name: str
    slug: str
    formula_latex: str           # KaTeX-compatible LaTeX string
    interpretation: str
    mappings: list[NIPAMapping]
    citations: list[str]


class MethodologyMapper(ABC):
    """Abstract base for NIPA-to-Marx translation methodologies."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable methodology name."""
        ...

    @property
    @abstractmethod
    def slug(self) -> str:
        """URL-safe identifier."""
        ...

    @abstractmethod
    def compute_rate_of_profit(self, data: dict[str, pd.Series]) -> pd.Series:
        """Compute rate of profit from aligned NIPA series."""
        ...

    @abstractmethod
    def compute_occ(self, data: dict[str, pd.Series]) -> pd.Series:
        """Compute organic composition of capital."""
        ...

    @abstractmethod
    def compute_rate_of_surplus_value(self, data: dict[str, pd.Series]) -> pd.Series:
        """Compute rate of surplus value."""
        ...

    @abstractmethod
    def compute_mass_of_profit(self, data: dict[str, pd.Series]) -> pd.Series:
        """Compute mass of profit (absolute surplus)."""
        ...

    @abstractmethod
    def get_required_series(self) -> list[str]:
        """Return list of series_ids needed from the database."""
        ...

    @abstractmethod
    def get_documentation(self) -> list[IndicatorDoc]:
        """Return self-documentation for all indicators."""
        ...
```

### Pattern 2: Methodology Registry

**What:** Class-level registry that discovers and stores methodology implementations.
**When to use:** At app startup; endpoints look up methodologies by slug.

```python
# backend/ecpm/indicators/registry.py
from ecpm.indicators.base import MethodologyMapper


class MethodologyRegistry:
    """Registry for methodology mapper implementations."""

    _mappers: dict[str, MethodologyMapper] = {}

    @classmethod
    def register(cls, mapper: MethodologyMapper) -> None:
        cls._mappers[mapper.slug] = mapper

    @classmethod
    def get(cls, slug: str) -> MethodologyMapper:
        if slug not in cls._mappers:
            raise KeyError(f"Unknown methodology: {slug}")
        return cls._mappers[slug]

    @classmethod
    def list_all(cls) -> list[MethodologyMapper]:
        return list(cls._mappers.values())

    @classmethod
    def default(cls) -> MethodologyMapper:
        return cls._mappers["shaikh-tonak"]
```

### Pattern 3: Recharts ComposedChart with Crisis Annotations and Dual YAxis

**What:** The core chart component pattern for indicator detail pages.
**When to use:** Every individual indicator page, comparison view, overlay view.

```tsx
// IMPORTANT: Recharts 3.x -- accessibilityLayer is true by default
// Use ComposedChart for mixing Line + ReferenceArea
// Use yAxisId to link lines to specific axes

'use client'

import {
  ComposedChart, Line, XAxis, YAxis, Tooltip,
  CartesianGrid, Brush, ReferenceArea, ResponsiveContainer, Legend
} from 'recharts'

interface CrisisEpisode {
  name: string
  startDate: string  // ISO date
  endDate: string    // ISO date
  color: string
}

// Crisis annotations as ReferenceArea components
function CrisisAnnotations({ crises, visible }: {
  crises: CrisisEpisode[]
  visible: 'shaded' | 'lines' | 'hidden'
}) {
  if (visible === 'hidden') return null
  return crises.map((crisis) => (
    <ReferenceArea
      key={crisis.name}
      x1={crisis.startDate}
      x2={crisis.endDate}
      fill={crisis.color}
      fillOpacity={0.15}
      stroke={crisis.color}
      strokeOpacity={0.3}
      label={{ value: crisis.name, position: 'top', fontSize: 10 }}
    />
  ))
}

// Dual y-axis pattern
<ComposedChart data={mergedData}>
  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
  <XAxis dataKey="date" />
  <YAxis yAxisId="left" orientation="left" />
  <YAxis yAxisId="right" orientation="right" />
  <Tooltip />
  <Legend />
  <Line yAxisId="left" dataKey="rateOfProfit" stroke="#8884d8" dot={false} />
  <Line yAxisId="right" dataKey="massOfProfit" stroke="#82ca9d" dot={false} />
  {/* Crisis annotations rendered as ReferenceArea */}
  <CrisisAnnotations crises={CRISIS_EPISODES} visible={annotationMode} />
  <Brush dataKey="date" height={30} stroke="hsl(var(--primary))" />
</ComposedChart>
```

### Pattern 4: KaTeX Formula Rendering (No react-katex dependency)

**What:** Render LaTeX formulas using KaTeX directly, avoiding React 19 compatibility issues.
**When to use:** Methodology documentation page, indicator detail pages.

```tsx
'use client'

import katex from 'katex'
import 'katex/dist/katex.min.css'

interface FormulaProps {
  latex: string
  displayMode?: boolean
}

export function Formula({ latex, displayMode = true }: FormulaProps) {
  const html = katex.renderToString(latex, {
    displayMode,
    throwOnError: false,
  })
  return <span dangerouslySetInnerHTML={{ __html: html }} />
}
```

### Pattern 5: Next.js 16 Error Boundary and Loading State

**What:** File-convention based loading/error handling.
**When to use:** Every route segment under /indicators.

```tsx
// app/indicators/error.tsx -- MUST be client component
'use client'

import { useEffect } from 'react'

export default function ErrorPage({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string }
  unstable_retry: () => void
}) {
  useEffect(() => { console.error(error) }, [error])

  return (
    <div className="flex flex-col items-center justify-center gap-4 p-8">
      <h2 className="text-lg font-semibold">Failed to load indicators</h2>
      <p className="text-sm text-muted-foreground">{error.message}</p>
      <button onClick={() => unstable_retry()}>Try again</button>
    </div>
  )
}

// app/indicators/loading.tsx
import { Skeleton } from '@/components/ui/skeleton'

export default function Loading() {
  return (
    <div className="grid grid-cols-3 gap-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <Skeleton key={i} className="h-40 rounded-lg" />
      ))}
    </div>
  )
}
```

### Pattern 6: Next.js 16 Dynamic Route with Awaited Params

**What:** Dynamic segment params are Promises in Next.js 16 -- must await.
**When to use:** `/indicators/[slug]/page.tsx`

```tsx
// app/indicators/[slug]/page.tsx
export default async function IndicatorPage(props: PageProps<'/indicators/[slug]'>) {
  const { slug } = await props.params
  // Fetch indicator data...
}
```

### Anti-Patterns to Avoid

- **Computing indicators on every request:** Indicators should be computed once, cached in Redis with a TTL matching the data refresh cycle. Recompute only when new observations are ingested.
- **Storing computed indicators in the database:** Computed values are derived data. Store source observations only; compute and cache indicators. This avoids stale computed values and keeps the schema clean.
- **Using react-katex with React 19:** The react-katex package (v3.1.0) predates React 19. Use `katex.renderToString()` directly with `dangerouslySetInnerHTML` -- it is XSS-safe per KaTeX documentation.
- **Recharts 2.x patterns in Recharts 3.x:** Do NOT use `CategoricalChartState`, `activeIndex` props, `blendStroke`, or `isFront`. Recharts 3.x removed these. Use hooks like `useActiveTooltipLabel` instead.
- **Mixing async and client components:** Chart components need `'use client'` (useState, event handlers). Data fetching happens in Server Components or API routes. Do not try to make chart components async.
- **Hard-coding NIPA mappings in frontend:** All indicator definitions and documentation must come from the backend API. The frontend never knows NIPA table numbers -- it receives computed values and display metadata.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Credit-to-GDP gap trend extraction | Custom trend smoother | HP filter (scipy.signal or statsmodels) | BIS standard uses one-sided HP filter with lambda=400000 for quarterly data |
| Chart zoom/pan | Custom SVG interaction handlers | Recharts Brush component | Brush handles index management, resize handles, traveller positioning |
| Formula rendering | Custom math layout engine | KaTeX renderToString | Handles TeX parsing, glyph positioning, font metrics |
| Crisis annotation positioning | Pixel-based rectangle placement | Recharts ReferenceArea | Automatically maps data coordinates to SVG pixels via chart scales |
| Frequency alignment | New alignment code | Existing `_align_frequency()` from Phase 1 | Already handles LOCF for M/Q/A, tested and in production |
| Dual axis scaling | Manual min/max calculation | Recharts auto-scales each YAxis independently | Each YAxis with unique yAxisId auto-computes domain from linked data |

**Key insight:** The complexity in this phase is in the economic methodology (correctly mapping NIPA to Marx), not in the software infrastructure. All charting, caching, formula rendering, and API patterns have well-established library solutions.

## Common Pitfalls

### Pitfall 1: Mixing Up NIPA Table Numbering Formats
**What goes wrong:** BEA NIPA tables have multiple numbering schemes. "Table 1.12" in the handbook is "T10300" in the API. The series_config.yaml uses API-format table IDs.
**Why it happens:** Academic papers cite handbook numbers (1.12, 6.19, 6.17); BEA API uses different codes.
**How to avoid:** Always use BEA API table codes (T-format) in code. Document both formats in methodology docs for researcher reference.
**Warning signs:** 404 errors when querying BEA, table names not matching.

### Pitfall 2: Historical-Cost vs. Current-Cost Capital Stock
**What goes wrong:** Shaikh/Tonak and Kliman use different capital stock valuations, producing materially different profit rate trajectories.
**Why it happens:** Current-cost revalues assets at replacement prices; historical-cost uses original purchase prices. Inflation periods make these diverge sharply.
**How to avoid:** Make this the explicit differentiator in the methodology mapper. Document which BEA fixed asset table is used (FAAt101 for current-cost, FAAt102 for historical-cost).
**Warning signs:** Rate of profit series for Kliman showing dramatically different trends from Shaikh/Tonak in 1970s-1980s (expected divergence due to inflation).

### Pitfall 3: Productive vs. Unproductive Labor Classification
**What goes wrong:** Shaikh/Tonak classify financial, government, and real estate sectors as unproductive. Omitting this distinction produces conventional (non-Marxian) profit rates.
**Why it happens:** NIPA aggregates include all sectors by default. Marxian analysis requires filtering by productive sector.
**How to avoid:** Document the productive/unproductive boundary explicitly in each methodology mapper. Start with whole-economy aggregates as the simpler case; add productive-only variant as an option.
**Warning signs:** Computed surplus value matching conventional profit share exactly.

### Pitfall 4: Recharts 3.x Breaking Changes from 2.x
**What goes wrong:** Code examples from 2.x tutorials use removed props (`activeIndex`, `blendStroke`, `CategoricalChartState` in Customized).
**Why it happens:** Most online examples are still 2.x. Recharts 3.0 rewrote state management.
**How to avoid:** Install recharts@^3.8.0 explicitly. Do not use `Customized` for state access -- use exported hooks. `accessibilityLayer` is now true by default.
**Warning signs:** TypeScript errors about missing props, runtime errors in Customized components.

### Pitfall 5: Frequency Mismatch in Indicator Computation
**What goes wrong:** Dividing a quarterly series by an annual series produces NaN or misleading ratios.
**Why it happens:** FRED series have mixed frequencies (monthly, quarterly, annual). BEA fixed assets are annual.
**How to avoid:** Align all input series to a common frequency BEFORE computing ratios. Use LOCF (already implemented) to align to the lowest common frequency (usually annual for indicators involving capital stock).
**Warning signs:** NaN values in computed indicators, discontinuous jumps at year boundaries.

### Pitfall 6: Next.js 16 Params as Promise
**What goes wrong:** Accessing `params.slug` directly instead of `(await params).slug` causes TypeScript errors or runtime issues.
**Why it happens:** Next.js 16 changed params to be async (Promise-based).
**How to avoid:** Always `await params` or use `PageProps<'/indicators/[slug]'>` type helper.
**Warning signs:** TypeScript error about Promise not having property 'slug'.

## Code Examples

### NIPA-to-Marx Mapping: Shaikh/Tonak Methodology (Simplified)

```python
# Key NIPA mappings for Shaikh/Tonak rate of profit computation
# Source: Shaikh & Tonak (1994) "Measuring the Wealth of Nations"

# Surplus Value (S):
#   NIPA Table T11200 (National Income by Type of Income)
#   = National Income - Employee Compensation (all sectors)
#   Simplified: Corporate profits + Net interest + Rental income + Proprietors' income
#   FRED proxies: A053RC1Q027SBEA (National Income) - A576RC1 (Compensation of Employees)

# Variable Capital (V):
#   = Employee Compensation (productive sectors only, for full Shaikh/Tonak)
#   Simplified (whole-economy): A576RC1 (Compensation of Employees)
#   More precise: WASCUR (Wages and Salaries) -- narrower definition

# Constant Capital (C):
#   = Net Stock of Fixed Assets (current-cost for Shaikh/Tonak)
#   BEA Fixed Assets Table FAAt101, Line 2 (Private fixed assets)
#   FRED proxy: K1NTOTL1SI000 (Current-Cost Net Stock of Private Fixed Assets)
#   + Circulating constant capital (materials/intermediate inputs -- harder to get from NIPA)

# Rate of Profit: r = S / (C + V)
# OCC: C / V
# Rate of Surplus Value: S / V
# Mass of Profit: S (absolute value, not ratio)
```

### NIPA-to-Marx Mapping: Kliman TSSI Methodology (Simplified)

```python
# Key differences from Shaikh/Tonak:
#
# Capital Stock:
#   Kliman uses HISTORICAL COST (not current-cost)
#   BEA Fixed Assets Table FAAt102 (Historical-cost net stock)
#   The denominator is the net stock at END OF PRIOR YEAR (temporal interpretation)
#
# Profit Numerator:
#   NIPA Table T61700 (Corporate Profits by Industry)
#   Lines covering all corporate sectors
#   Also uses NIPA Table 6.17A-D line 1 in handbook notation
#
# Key distinction: Kliman's rate of profit does NOT recover in neoliberal period
# (post-1982) because historical-cost capital stock grows faster than current-cost
# when inflation decelerates.
```

### API Endpoint Structure (Recommended)

```python
# backend/ecpm/api/indicators.py

# GET /api/indicators/
#   Returns list of all available indicators with latest values
#   Query params: ?methodology=shaikh-tonak (default)

# GET /api/indicators/{slug}
#   Returns time-series for one indicator
#   Query params: ?methodology=shaikh-tonak&start=1947&end=2024&frequency=A

# GET /api/indicators/{slug}/compare
#   Returns same indicator computed under all methodologies for side-by-side view

# GET /api/indicators/methodology
#   Returns documentation for all indicators under all methodologies
#   (formulas, NIPA mappings, interpretation notes)

# GET /api/indicators/methodology/{methodology-slug}
#   Returns documentation for one methodology only
```

### Indicator Response Schema

```python
# backend/ecpm/schemas/indicators.py
from pydantic import BaseModel
from typing import Optional
import datetime as dt


class IndicatorDataPoint(BaseModel):
    date: dt.datetime
    value: float


class IndicatorResponse(BaseModel):
    slug: str
    name: str
    units: str
    methodology: str
    frequency: str
    data: list[IndicatorDataPoint]
    latest_value: Optional[float] = None
    latest_date: Optional[dt.datetime] = None


class IndicatorSummary(BaseModel):
    slug: str
    name: str
    units: str
    latest_value: Optional[float] = None
    latest_date: Optional[dt.datetime] = None
    trend: Optional[str] = None  # "rising", "falling", "flat"
    sparkline: list[float] = []  # last N values for overview card


class IndicatorOverviewResponse(BaseModel):
    methodology: str
    indicators: list[IndicatorSummary]


class NIPAMappingDoc(BaseModel):
    marx_category: str
    nipa_table: str
    nipa_line: int
    nipa_description: str
    operation: str
    notes: str = ""


class IndicatorMethodologyDoc(BaseModel):
    indicator_slug: str
    indicator_name: str
    formula_latex: str
    interpretation: str
    mappings: list[NIPAMappingDoc]
    citations: list[str]


class MethodologyDocResponse(BaseModel):
    methodology_slug: str
    methodology_name: str
    indicators: list[IndicatorMethodologyDoc]
```

### Financial Fragility: Credit-to-GDP Gap Computation

```python
# The BIS methodology for credit-to-GDP gap:
# 1. Compute credit-to-GDP ratio: total_credit / (4-quarter sum of nominal GDP)
# 2. Apply one-sided Hodrick-Prescott filter with lambda = 400,000 (quarterly)
# 3. Gap = actual ratio - HP trend
#
# FRED series available:
#   - BOGZ1FL073164003Q (Nonfinancial Corporate Business Debt)
#   - GDP (Nominal GDP)
#   - GFDEGDQ188S (Federal Debt as % GDP) -- related but different
#
# For HP filter: use statsmodels.tsa.filters.hp_filter.hpfilter
# or scipy equivalent. statsmodels is NOT currently in dependencies --
# can implement simple one-sided HP filter with scipy or numpy.
#
# NOTE: statsmodels would be needed for Phase 3 (VAR/SVAR) anyway,
# so adding it here is forward-compatible.

import numpy as np

def one_sided_hp_filter(series: np.ndarray, lamb: float = 400_000) -> np.ndarray:
    """One-sided (backward-looking) HP filter for credit-to-GDP gap.

    The BIS uses lambda=400,000 for quarterly data.
    This is a recursive implementation that only uses past data.
    """
    n = len(series)
    trend = np.zeros(n)
    trend[0] = series[0]
    if n > 1:
        trend[1] = series[1]

    for t in range(2, n):
        # Simplified one-sided HP: minimize sum of squared deviations
        # from data + lambda * sum of squared second differences of trend
        # Using the recursive approximation
        trend[t] = (series[t] + lamb * (2 * trend[t-1] - trend[t-2])) / (1 + lamb)

    return trend
```

### Sparkline Component Pattern

```tsx
'use client'

import { LineChart, Line, ResponsiveContainer } from 'recharts'

interface SparklineProps {
  data: number[]
  color?: string
  height?: number
}

export function Sparkline({ data, color = 'hsl(var(--primary))', height = 40 }: SparklineProps) {
  const chartData = data.map((value, index) => ({ value, index }))

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData}>
        <Line
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={1.5}
          dot={false}
          animationDuration={0}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Recharts 2.x CategoricalChartState | Recharts 3.x hooks + removed internal state | Recharts 3.0 (2025) | Must use hooks for tooltip/state access; Customized no longer receives state |
| react-katex wrapper | katex.renderToString directly | KaTeX 0.16.x | Avoids React version compatibility issues; same output |
| Next.js params as sync object | Next.js 16 params as Promise | Next.js 15+ | Must `await params` in all dynamic route handlers |
| Next.js error.tsx `reset` prop | Next.js 16 `unstable_retry` prop | Next.js 16 | Error boundary retry function renamed |
| Recharts `react-smooth` dependency | Recharts 3.x internal animations | Recharts 3.0 | Lighter bundle; no external animation library |

**Deprecated/outdated:**
- `recharts-scale` package: Removed; scales now internal to Recharts 3.x
- `react-smooth` package: Removed; animations internal to Recharts 3.x
- `activeIndex` prop on Recharts components: Removed in 3.x
- `TooltipProps` type: Renamed to `TooltipContentProps` in Recharts 3.x
- `error.tsx` `reset` callback: Renamed to `unstable_retry` in Next.js 16

## Open Questions

1. **HP Filter Implementation for Credit-to-GDP Gap**
   - What we know: BIS uses one-sided HP filter with lambda=400,000 for quarterly data
   - What's unclear: Whether to add `statsmodels` now (it will be needed in Phase 3 for VAR models) or implement a minimal one-sided HP filter in numpy
   - Recommendation: Add `statsmodels` now -- it is needed in Phase 3 anyway and provides a well-tested `hpfilter` implementation. Avoids duplicating filter logic.

2. **Precise NIPA Table/Line Mappings for Each Indicator**
   - What we know: General formulas (r = S/(C+V), OCC = C/V, etc.) and the broad categories (compensation, profits, fixed assets)
   - What's unclear: The exact line numbers for Shaikh/Tonak productive-sector adjustments (requires the book). The simplified whole-economy version is well-documented.
   - Recommendation: Start with whole-economy aggregate mappings (well-documented in academic literature) using FRED series already ingested. Document as "Simplified Shaikh/Tonak" and "Simplified Kliman". Add productive/unproductive sector refinements as an enhancement.

3. **Financial-to-Real Asset Ratio Data Source**
   - What we know: Conceptually = financial assets / real (tangible) assets
   - What's unclear: Exact FRED/BEA series for total financial assets vs. real assets. Flow of Funds (Z.1) data may be needed.
   - Recommendation: Use FRED series for financial indicators already ingested. If specific Z.1 series are needed, they can be added to series_config.yaml during implementation.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio 0.24.x |
| Config file | backend/pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `cd /home/marcellinor/Desktop/ECPM/backend && python -m pytest tests/ -x --timeout=30` |
| Full suite command | `cd /home/marcellinor/Desktop/ECPM/backend && python -m pytest tests/ --timeout=30 -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FEAT-01 | Translation engine ABC, registry, Shaikh/Tonak impl | unit | `pytest tests/test_indicators.py -x` | No -- Wave 0 |
| FEAT-02 | Rate of profit computation correctness | unit | `pytest tests/test_indicators.py::test_rate_of_profit -x` | No -- Wave 0 |
| FEAT-03 | OCC computation correctness | unit | `pytest tests/test_indicators.py::test_occ -x` | No -- Wave 0 |
| FEAT-04 | Rate of surplus value computation | unit | `pytest tests/test_indicators.py::test_rate_of_surplus_value -x` | No -- Wave 0 |
| FEAT-05 | Mass of profit + divergence tracking | unit | `pytest tests/test_indicators.py::test_mass_of_profit -x` | No -- Wave 0 |
| FEAT-06 | Productivity-wage gap rolling window | unit | `pytest tests/test_indicators.py::test_productivity_wage_gap -x` | No -- Wave 0 |
| FEAT-07 | Financial fragility indicators (credit gap, ratios) | unit | `pytest tests/test_indicators.py::test_financial_fragility -x` | No -- Wave 0 |
| FEAT-08 | Methodology docs served from backend | integration | `pytest tests/test_api_indicators.py::test_methodology_docs -x` | No -- Wave 0 |
| FEAT-09 | Frequency alignment with strategy parameter | unit | `pytest tests/test_indicators.py::test_frequency_alignment -x` | No -- Wave 0 |
| DASH-01 | Time-series charts render with controls | manual-only | Visual verification in browser | N/A |
| DASH-02 | Dual y-axis overlay works | manual-only | Visual verification in browser | N/A |
| DASH-03 | Crisis annotations visible on charts | manual-only | Visual verification in browser | N/A |
| DASH-04 | Overview page shows all indicators | smoke | `pytest tests/test_api_indicators.py::test_overview_endpoint -x` | No -- Wave 0 |
| DASH-05 | Methodology docs render with KaTeX | manual-only | Visual verification in browser | N/A |
| DASH-08 | Loading/error states display correctly | manual-only | Visual verification + error injection | N/A |

### Sampling Rate
- **Per task commit:** `cd /home/marcellinor/Desktop/ECPM/backend && python -m pytest tests/ -x --timeout=30`
- **Per wave merge:** `cd /home/marcellinor/Desktop/ECPM/backend && python -m pytest tests/ --timeout=30 -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_indicators.py` -- covers FEAT-01 through FEAT-07, FEAT-09 (indicator computation unit tests)
- [ ] `tests/test_api_indicators.py` -- covers FEAT-08, DASH-04 (API endpoint integration tests)
- [ ] `tests/test_methodology_registry.py` -- covers FEAT-01 (registry + plugin pattern)
- [ ] Shared fixtures: mock NIPA data (series dict with known values for verifying formulas)
- [ ] Optional: `statsmodels` dependency addition for HP filter

## Sources

### Primary (HIGH confidence)
- Next.js 16.2.1 local docs at `frontend/node_modules/next/dist/docs/` -- layouts, pages, dynamic routes, error handling, loading states
- Existing codebase patterns: `backend/ecpm/api/data.py`, `backend/ecpm/cache.py`, `backend/ecpm/models/` -- established async SQLAlchemy + Redis caching + Pydantic patterns
- Python `abc` module: [Python docs](https://docs.python.org/3/library/abc.html) -- ABC pattern for plugin architecture

### Secondary (MEDIUM confidence)
- [Recharts 3.0 migration guide](https://github.com/recharts/recharts/wiki/3.0-migration-guide) -- Breaking changes, removed props, new API
- [Recharts ReferenceArea API](https://recharts.github.io/en-US/api/ReferenceArea/) -- Crisis annotation component
- [KaTeX API](https://katex.org/docs/api) -- renderToString for server-safe formula rendering
- [BIS Credit-to-GDP Gaps](https://data.bis.org/topics/CREDIT_GAPS) -- HP filter methodology, lambda parameter
- [BLS Productivity-Compensation Gap](https://www.bls.gov/opub/btn/volume-6/understanding-the-labor-productivity-and-compensation-gap.htm) -- Methodology for gap calculation

### Tertiary (LOW confidence)
- Shaikh/Tonak NIPA mappings: Reconstructed from academic secondary sources; specific line numbers need verification against "Measuring the Wealth of Nations" (1994)
- Kliman TSSI NIPA mappings: Reconstructed from blog posts and reviews of "The Failure of Capitalist Production" (2012); BEA table T61700/FAAt102 references need verification
- HP filter one-sided implementation: Simplified recursive approximation; `statsmodels.hpfilter` is the authoritative implementation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- Recharts 3.x and KaTeX are well-documented; Python abc is stdlib
- Architecture: HIGH -- ABC + registry is standard Python plugin pattern; Recharts ComposedChart is standard for multi-axis charts
- Indicator computation: MEDIUM -- General formulas are well-known; exact NIPA line-item mappings for Shaikh/Tonak productive-labor adjustments are LOW confidence (require the book)
- Pitfalls: HIGH -- Recharts 3.x breaking changes verified via official migration guide; Next.js 16 params change verified via local docs

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable domain; Recharts/KaTeX release cadence is moderate)
