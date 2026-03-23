# Phase 3: Predictive Modeling and Crisis Index - Research

**Researched:** 2026-03-23
**Domain:** Econometric time-series modeling (VAR/SVAR), regime-switching, crisis index construction, forecast visualization
**Confidence:** HIGH

## Summary

Phase 3 adds econometric forecasting, regime detection, and a composite crisis probability index on top of Phase 2's computed Marxist indicators. The core modeling stack is **statsmodels 0.14.6** -- it provides VAR, SVAR (with A/B matrix identification), Markov regime-switching (MarkovAutoregression), ADF/KPSS stationarity tests, and forecast confidence intervals all in one package. No additional econometric libraries are needed.

The backend work splits into three domains: (1) a stationarity-preprocessing + VAR/SVAR pipeline that produces forecasts with CI bands, (2) Markov regime-switching for crisis/normal/stagnation classification, and (3) a composite Crisis Probability Index that synthesizes TRPF, realization, and financial fragility sub-indices. All three are orchestrated as a Celery chain triggered after data refresh or manual button press, with SSE progress streaming reusing the existing sse-starlette + Redis pubsub pattern from Phase 1.

The frontend adds a `/forecasting` page with three main sections: a stacked-bar crisis gauge with sparkline and regime badge (hero), forecast-enabled indicator charts with CI bands (body), and backtest timeline visualizations (detail). Recharts ComposedChart (already used for indicator charts) supports forecast lines via dashed `<Line>` components and CI bands via paired `<Area>` components with `baseValue`. The existing crisis episodes from `lib/crisis-episodes.ts` serve double duty as both chart annotations and backtest targets.

**Primary recommendation:** Use statsmodels exclusively for all econometric modeling. Store model outputs (forecasts, backtest results, regime probabilities) as JSON in Redis with long TTL (24h), persisting only the serialized results -- not the fitted model objects. Celery chain orchestrates the pipeline steps sequentially, publishing progress to Redis pubsub at each step boundary.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Forecast toggle button on each indicator chart from Phase 2 -- off by default, chart looks exactly like Phase 2 when disabled
- When toggled on: dashed forecast line extending from end of historical data, with nested semi-transparent CI bands (darker 68%, lighter 95%)
- User-adjustable forecast horizon via dropdown: 4Q, 8Q, 12Q, 16Q -- default 8 quarters (2 years)
- All Marxist indicators computed in Phase 2 get forecast toggles -- VAR model includes all as endogenous variables
- Horizontal stacked bar showing Composite Crisis Probability Index (0-100%), decomposed by mechanism: TRPF, realization crisis, financial fragility -- each segment colored by mechanism type
- Sparkline below the bar showing composite index trend over last 5-10 years
- Regime classification badge (green 'Normal', amber 'Stagnation', red 'Crisis') on the gauge card corner -- from Markov regime-switching model
- Lives as hero element on dedicated /forecasting page, with forecast charts below
- Separate regime detail section further down the page: transition probability matrix, regime duration stats, historical regime timeline
- Interactive timeline chart for each crisis episode: shows composite Crisis Index over the period, crisis episode as shaded region, vertical marker at 12-month and 24-month warning windows
- Per-mechanism decomposition: stacked area beneath the composite line showing TRPF, realization, and financial fragility contributions
- All 6 crisis episodes from Phase 2 annotations available: Great Depression (1929), Oil/Stagflation (1973), Volcker (1980), Dot-com (2001), GFC (2007-09), COVID (2020)
- Pre-computed during model training pipeline -- results cached, always available after training completes
- Auto-retrain triggered after data refresh (daily Celery beat from Phase 1), plus manual "Train Models" button on /forecasting page
- Progress bar + collapsible live log stream via SSE: shows overall step progress with checkmarks, plus detailed diagnostic output
- Non-blocking: dashboard stays fully usable during training. Old forecasts remain visible until new results replace them
- Detailed diagnostics on failure: which step failed, error message, diagnostic context

### Claude's Discretion
- VAR/SVAR implementation details (lag selection criteria weights, identification restrictions)
- Markov regime-switching model specification (number of regimes, transition assumptions)
- Crisis Index weighting scheme for combining TRPF, realization, and financial fragility sub-indices
- Exact stacked bar color palette and sparkline styling
- API endpoint structure for forecasts, backtest results, and training status
- Celery task chaining for the training pipeline
- Redis caching strategy for model outputs and backtest results

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MODL-01 | VAR models on key Marxist indicators with proper lag selection (AIC/BIC/HQIC) | statsmodels VAR.fit(maxlags, ic='aic') + select_order(); all 8 Phase 2 indicators as endogenous variables |
| MODL-02 | Mandatory stationarity preprocessing (ADF + KPSS tests) before any VAR modeling | statsmodels adfuller() + kpss(); dual-test strategy confirms stationarity/non-stationarity |
| MODL-03 | SVAR with theoretically motivated identification restrictions from Marxist causal ordering | statsmodels SVAR with svar_type='A', A matrix encoding Marxist causal chain: OCC -> rate of profit -> mass of profit -> financial indicators |
| MODL-04 | Forecasts with confidence intervals / uncertainty quantification | VARResults.forecast_interval(alpha=0.32) for 68% CI, alpha=0.05 for 95% CI; returns (point, lower, upper) arrays |
| MODL-05 | Backtest against 2007-2009 GFC (indicators should rise 12-24 months prior) | Run model on data ending 2005-2006, generate forecasts through 2009, compare composite index trajectory against actual crisis timing |
| MODL-06 | Markov regime-switching models to detect crisis vs. normal vs. stagnation regimes | statsmodels MarkovAutoregression(k_regimes=3, switching_variance=True); smoothed_marginal_probabilities for regime classification |
| MODL-07 | Composite Crisis Probability Index synthesizing TRPF, realization, and financial fragility | Weighted combination of sub-indices from 3 mechanism categories; equal weighting as default, configurable |
| MODL-08 | Crisis Probability Index decomposable by crisis mechanism | Store individual mechanism scores alongside composite; frontend stacked bar renders each segment independently |
| DASH-06 | Composite Crisis Probability Index with mechanism decomposition gauge | Horizontal stacked bar (Recharts BarChart stacked), sparkline, regime badge; dedicated /forecasting page |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| statsmodels | 0.14.6 | VAR, SVAR, MarkovAutoregression, ADF, KPSS, IRF, FEVD | Only Python library with unified VAR + SVAR + Markov regime-switching; actively maintained |
| pandas | >=2.2 (already installed) | Data alignment, Series/DataFrame operations for model I/O | Already in project; statsmodels requires it |
| numpy | (statsmodels dependency) | Matrix operations for A/B identification matrices | Comes with statsmodels |
| scipy | (statsmodels dependency) | Optimization for MLE fitting | Comes with statsmodels |
| celery | >=5.4 (already installed) | Task orchestration via chain primitive for pipeline steps | Already in project; chain pattern for sequential model training steps |
| redis | >=5.0 (already installed) | Result caching + pubsub for SSE progress streaming | Already in project; pubsub pattern from Phase 1 fetch_stream |
| sse-starlette | >=2.0 (already installed) | SSE endpoint for training progress | Already in project; EventSourceResponse in status.py |
| recharts | >=3.8.0 (already installed) | Forecast charts, CI bands, gauge, sparkline, backtest timelines | Already in project; ComposedChart extended with Area + dashed Line |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| joblib | (stdlib-adjacent) | Parallel model fitting if needed | Optional: parallelize backtest runs across crisis episodes |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| statsmodels VAR | arch (Kevin Sheppard) | arch has better GARCH but no VAR/SVAR; statsmodels covers all needs |
| statsmodels MarkovAutoregression | hmmlearn | hmmlearn lacks economic-specific features; statsmodels integrates better with VAR ecosystem |
| Manual CI computation | conformal prediction (MAPIE) | Over-engineering for VAR where analytical CIs are standard |

**Installation:**
```bash
pip install statsmodels>=0.14.6
```

Only one new dependency needed. Everything else is already in `pyproject.toml`.

## Architecture Patterns

### Recommended Project Structure
```
backend/ecpm/
  modeling/
    __init__.py              # Exports ModelingPipeline, ForecastResult, etc.
    stationarity.py          # ADF + KPSS dual test, differencing logic
    var_model.py             # VAR fitting, lag selection, forecasting
    svar_model.py            # SVAR with A matrix identification
    regime_switching.py      # MarkovAutoregression wrapper
    crisis_index.py          # Composite Crisis Probability Index computation
    backtest.py              # Historical backtesting against crisis episodes
    schemas.py               # Pydantic models for all modeling outputs
  tasks/
    training_tasks.py        # Celery tasks for model training pipeline
  api/
    forecasting.py           # REST + SSE endpoints for forecasts, training, backtests

frontend/src/
  app/forecasting/
    page.tsx                 # /forecasting route
    loading.tsx              # Loading skeleton
    error.tsx                # Error boundary
  components/forecasting/
    crisis-gauge.tsx         # Stacked bar + sparkline + regime badge
    forecast-toggle.tsx      # Toggle button + horizon dropdown
    forecast-chart.tsx       # Extended indicator chart with CI bands
    backtest-timeline.tsx    # Per-episode backtest visualization
    training-status.tsx      # Progress bar + log stream (SSE consumer)
    regime-detail.tsx        # Transition matrix, duration stats, timeline
  lib/
    forecast-api.ts          # API client extensions for forecast endpoints
```

### Pattern 1: Stationarity Preprocessing Pipeline
**What:** Dual ADF + KPSS test on each series before VAR modeling. If both tests agree on non-stationarity, difference the series. Track differencing order for inverse transformation on forecasts.
**When to use:** Every time the VAR model is retrained (data refresh or manual trigger).
**Example:**
```python
# Source: statsmodels official docs (adfuller, kpss)
from statsmodels.tsa.stattools import adfuller, kpss
import pandas as pd
import numpy as np

def test_stationarity(series: pd.Series, alpha: float = 0.05) -> dict:
    """Dual ADF + KPSS stationarity test.

    ADF null: unit root (non-stationary)
    KPSS null: stationary

    Returns dict with test results and recommendation.
    """
    adf_stat, adf_pvalue, adf_lags, adf_nobs, adf_crit, _ = adfuller(
        series.dropna(), regression='c', autolag='AIC'
    )
    kpss_stat, kpss_pvalue, kpss_lags, kpss_crit = kpss(
        series.dropna(), regression='c', nlags='auto'
    )

    adf_stationary = adf_pvalue < alpha      # Reject unit root
    kpss_stationary = kpss_pvalue >= alpha    # Fail to reject stationarity

    return {
        "adf_pvalue": adf_pvalue,
        "kpss_pvalue": kpss_pvalue,
        "adf_stationary": adf_stationary,
        "kpss_stationary": kpss_stationary,
        "is_stationary": adf_stationary and kpss_stationary,
        "recommendation": "stationary" if (adf_stationary and kpss_stationary)
                          else "difference",
    }

def ensure_stationarity(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Difference all series uniformly if any are non-stationary.

    Returns (transformed data, differencing orders dict).
    All series must be same length, so if any need differencing, all get differenced.
    """
    diff_orders: dict[str, int] = {}
    needs_differencing = False

    for col in data.columns:
        result = test_stationarity(data[col])
        if not result["is_stationary"]:
            needs_differencing = True
            break

    if needs_differencing:
        transformed = data.diff().dropna()
        diff_orders = {col: 1 for col in data.columns}
    else:
        transformed = data
        diff_orders = {col: 0 for col in data.columns}

    return transformed, diff_orders
```

### Pattern 2: VAR Lag Selection + Fitting
**What:** Use information criteria to select optimal lag, fit VAR, produce forecasts with nested CIs.
**When to use:** Core model training step after stationarity preprocessing.
**Example:**
```python
# Source: statsmodels VAR docs
from statsmodels.tsa.api import VAR
import numpy as np

def fit_var_model(data: pd.DataFrame, max_lags: int = 12) -> dict:
    """Fit VAR with automatic lag selection.

    Uses AIC as primary criterion, BIC as tiebreaker.
    """
    model = VAR(data)

    # Select optimal lag order
    lag_results = model.select_order(max_lags)
    selected_lag = lag_results.aic  # AIC-optimal lag

    # Fit with selected lag
    results = model.fit(selected_lag)

    return {
        "results": results,
        "selected_lag": selected_lag,
        "aic": lag_results.aic,
        "bic": lag_results.bic,
        "hqic": lag_results.hqic,
        "lag_criteria": {
            "aic": lag_results.aic,
            "bic": lag_results.bic,
            "hqic": lag_results.hqic,
        },
    }

def generate_forecasts(
    results, data: pd.DataFrame, steps: int = 8
) -> dict[str, dict]:
    """Generate point forecasts with 68% and 95% CIs.

    Returns per-variable forecast dict with point, lower_68, upper_68, lower_95, upper_95.
    """
    lag_order = results.k_ar
    last_obs = data.values[-lag_order:]

    # 68% CI (1 sigma)
    point_68, lower_68, upper_68 = results.forecast_interval(
        last_obs, steps=steps, alpha=0.32
    )
    # 95% CI (2 sigma)
    point_95, lower_95, upper_95 = results.forecast_interval(
        last_obs, steps=steps, alpha=0.05
    )

    forecasts = {}
    for i, col in enumerate(data.columns):
        forecasts[col] = {
            "point": point_68[:, i].tolist(),
            "lower_68": lower_68[:, i].tolist(),
            "upper_68": upper_68[:, i].tolist(),
            "lower_95": lower_95[:, i].tolist(),
            "upper_95": upper_95[:, i].tolist(),
        }
    return forecasts
```

### Pattern 3: SVAR Identification with Marxist Causal Ordering
**What:** Define A matrix restrictions encoding theoretical causal structure. In Marxist theory: organic composition of capital (OCC) and rate of surplus value drive the rate of profit; falling rate of profit drives mass of profit divergence; financial indicators respond to profitability crisis.
**When to use:** After VAR fit, for structural impulse response analysis and decomposition.
**Example:**
```python
# Source: statsmodels SVAR docs
import numpy as np
from statsmodels.tsa.api import VAR

def build_svar_a_matrix(n_vars: int = 8) -> np.ndarray:
    """Build A matrix for SVAR identification.

    Causal ordering (Cholesky-like lower triangular):
    1. OCC (most exogenous - production technology)
    2. Rate of surplus value (exploitation conditions)
    3. Rate of profit (determined by OCC and s/v)
    4. Mass of profit (follows rate of profit trajectory)
    5. Productivity-wage gap (labor market response)
    6. Credit-GDP gap (financial sector response)
    7. Financial-real ratio (asset price response)
    8. Debt service ratio (most endogenous - financial fragility)

    'E' = estimate, numeric = constrained.
    Lower triangular: variable j can be contemporaneously
    affected by variables ordered before it.
    """
    A = np.zeros((n_vars, n_vars), dtype=object)

    # Diagonal = 1 (own normalization)
    np.fill_diagonal(A, 1)

    # Below diagonal = 'E' (free to estimate)
    for i in range(n_vars):
        for j in range(i):
            A[i, j] = 'E'

    # Above diagonal = 0 (identification restriction)
    # Already zeros from initialization

    return A

def fit_svar(var_results, a_matrix: np.ndarray):
    """Fit SVAR using pre-estimated VAR and A matrix restrictions."""
    svar = var_results.test_causality  # This is for testing
    # Actual SVAR fitting:
    from statsmodels.tsa.vector_ar.svar_model import SVAR
    svar_model = SVAR(
        var_results.endog,
        svar_type='A',
        A=a_matrix,
    )
    svar_results = svar_model.fit(maxlags=var_results.k_ar)
    return svar_results
```

### Pattern 4: Markov Regime-Switching for Crisis Detection
**What:** 3-regime (Normal, Stagnation, Crisis) Markov-switching autoregression on a composite indicator.
**When to use:** Applied to the Composite Crisis Index or rate of profit series for regime classification.
**Example:**
```python
# Source: statsmodels MarkovAutoregression docs
from statsmodels.tsa.regime_switching.markov_autoregression import MarkovAutoregression

def fit_regime_model(series: pd.Series, k_regimes: int = 3, order: int = 2):
    """Fit Markov regime-switching autoregression.

    3 regimes: Normal (high mean, low variance),
               Stagnation (moderate mean, moderate variance),
               Crisis (low mean, high variance)
    """
    model = MarkovAutoregression(
        series.dropna(),
        k_regimes=k_regimes,
        order=order,
        trend='c',
        switching_ar=False,       # AR coefficients same across regimes
        switching_variance=True,  # Variance differs by regime
    )
    results = model.fit()

    # Smoothed regime probabilities
    smoothed_probs = results.smoothed_marginal_probabilities

    # Current regime = highest probability regime
    current_regime = smoothed_probs.iloc[-1].idxmax()

    # Transition probability matrix
    transition_matrix = results.regime_transition

    return {
        "results": results,
        "smoothed_probs": smoothed_probs,
        "current_regime": int(current_regime),
        "transition_matrix": transition_matrix.tolist(),
        "regime_labels": {0: "Normal", 1: "Stagnation", 2: "Crisis"},
    }
```

### Pattern 5: Celery Chain for Pipeline Orchestration
**What:** Sequential Celery tasks connected via `chain()`. Each task publishes progress to Redis pubsub. SSE endpoint consumes pubsub for frontend streaming.
**When to use:** Model training pipeline triggered by data refresh or manual button.
**Example:**
```python
# Source: Celery Canvas docs
from celery import chain
from ecpm.tasks.celery_app import celery_app

@celery_app.task(bind=True, name="ecpm.tasks.training.run_stationarity")
def run_stationarity(self, data_config: dict) -> dict:
    """Step 1: Stationarity tests on all indicators."""
    _publish_progress(self, step="stationarity", status="running")
    # ... run tests ...
    _publish_progress(self, step="stationarity", status="complete")
    return {"stationarity_results": results, "diff_orders": diff_orders}

@celery_app.task(bind=True, name="ecpm.tasks.training.run_var")
def run_var(self, prev_result: dict) -> dict:
    """Step 2: VAR fitting with lag selection."""
    _publish_progress(self, step="var", status="running")
    # ... fit VAR ...
    _publish_progress(self, step="var", status="complete")
    return {**prev_result, "var_forecasts": forecasts}

# Full pipeline as chain:
def trigger_training_pipeline():
    pipeline = chain(
        run_stationarity.s(data_config),
        run_var.s(),
        run_svar.s(),
        run_regime_switching.s(),
        run_backtests.s(),
        cache_results.s(),
    )
    return pipeline.apply_async()

def _publish_progress(task, step: str, status: str, detail: str = ""):
    """Publish training progress to Redis pubsub for SSE streaming."""
    import json
    from ecpm.config import get_settings
    import redis
    settings = get_settings()
    r = redis.from_url(settings.redis_url)
    r.publish("ecpm:training:progress", json.dumps({
        "task_id": task.request.id,
        "step": step,
        "status": status,
        "detail": detail,
    }))
```

### Pattern 6: Forecast CI Bands in Recharts
**What:** Extend existing ComposedChart with dashed forecast Line and nested semi-transparent Area bands for 68% and 95% CIs.
**When to use:** When forecast toggle is enabled on any indicator chart.
**Example:**
```tsx
// Pattern for CI bands in Recharts ComposedChart
// Uses Area with baseValue to create band between upper and lower bounds
<ComposedChart data={[...historicalData, ...forecastData]}>
  {/* Historical line (solid) */}
  <Line
    dataKey="value"
    stroke="hsl(var(--chart-1))"
    strokeWidth={2}
    dot={false}
  />
  {/* Forecast line (dashed) */}
  <Line
    dataKey="forecast"
    stroke="hsl(var(--chart-1))"
    strokeWidth={2}
    strokeDasharray="6 4"
    dot={false}
  />
  {/* 95% CI band (lighter, wider) */}
  <Area
    dataKey="upper_95"
    stroke="none"
    fill="hsl(var(--chart-1))"
    fillOpacity={0.08}
    baseValue="dataMin"
    type="monotone"
  />
  <Area
    dataKey="lower_95"
    stroke="none"
    fill="hsl(var(--background))"
    fillOpacity={1}
    baseValue="dataMin"
    type="monotone"
  />
  {/* 68% CI band (darker, narrower) */}
  <Area
    dataKey="upper_68"
    stroke="none"
    fill="hsl(var(--chart-1))"
    fillOpacity={0.15}
    baseValue="dataMin"
    type="monotone"
  />
  <Area
    dataKey="lower_68"
    stroke="none"
    fill="hsl(var(--background))"
    fillOpacity={1}
    baseValue="dataMin"
    type="monotone"
  />
</ComposedChart>
```

**Note:** The CI band approach above is a common pattern but may need adjustment. An alternative reliable approach is to compute `ci_95_range` (upper_95 - lower_95) and `ci_68_range` (upper_68 - lower_68) as data fields, then use stacked Areas with the lower bound as the baseline. Test both approaches during implementation. The key insight is that Recharts Area always fills from the data value down to baseValue -- to create a band between two lines, you typically layer two areas and clip. An easier alternative is to use ReferenceArea per data point or a custom SVG shape.

### Anti-Patterns to Avoid
- **Persisting fitted statsmodels objects in Redis:** Pickle serialization is fragile across library versions and bloated in memory. Store computed results (forecast arrays, probabilities, diagnostics) as JSON instead.
- **Running model training synchronously in API endpoint:** Always use Celery tasks. Model training can take 30s-5min depending on data size and model complexity.
- **Differencing only non-stationary series in a VAR:** If any series needs differencing, all must be differenced to maintain equal length. The VAR model requires all endogenous variables to have the same number of observations.
- **Hard-coding lag order:** Always use information criteria (AIC primary, BIC tiebreaker). Macro data characteristics change as new observations arrive.
- **Blocking the frontend during training:** Old results must remain visible during retraining. New results replace old atomically after caching is complete.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| VAR model estimation | Custom OLS per equation | statsmodels VAR | Joint estimation, proper covariance, built-in lag selection, forecast_interval |
| Stationarity testing | Manual ADF implementation | statsmodels adfuller() + kpss() | MacKinnon critical values, auto lag selection, Hobijn bandwidth |
| Regime switching | Hidden Markov Model from scratch | statsmodels MarkovAutoregression | Hamilton filter, Kim smoother, EM + BFGS optimization, smoothed probabilities |
| SVAR identification | Manual matrix algebra | statsmodels SVAR | MLE estimation with constraints, handles over-identification testing |
| Forecast confidence intervals | Bootstrap resampling | VARResults.forecast_interval() | Analytical CIs from VAR forecast error covariance matrix; fast and correct |
| SSE streaming | Custom WebSocket server | sse-starlette EventSourceResponse | Already in project, handles client disconnect, heartbeat, graceful shutdown |
| Task pipeline orchestration | Manual asyncio chaining | Celery chain() | Retry logic, result passing between tasks, monitoring, already configured |
| Impulse response functions | Manual MA infinity computation | VARResults.irf() | Luetkepohl standard errors, orthogonalized responses, cumulative effects |

**Key insight:** Statsmodels provides the complete econometric pipeline for this phase. The only new dependency is statsmodels itself. Every other tool is already in the project.

## Common Pitfalls

### Pitfall 1: Series Length Mismatch in VAR
**What goes wrong:** VAR requires all endogenous variables to have identical length. Phase 2 indicators may have different start dates (e.g., financial indicators start later than profit rate).
**Why it happens:** Different FRED/BEA series have different historical coverage. Some indicators require multiple source series that start at different dates.
**How to avoid:** Before VAR fitting, find the common date range across all indicators (intersection, not union). Drop all observations outside this range. Log the effective sample size.
**Warning signs:** ValueError from statsmodels about shape mismatch; unexplained NaN values in forecast output.

### Pitfall 2: Non-Convergence in Markov Regime-Switching
**What goes wrong:** MarkovAutoregression.fit() fails to converge or produces degenerate regimes (one regime absorbs 99%+ of observations).
**Why it happens:** 3-regime models are harder to estimate than 2-regime. Bad starting parameters. Insufficient data variation to identify distinct regimes.
**How to avoid:** Start with switching_ar=False (fewer parameters). Use switching_variance=True (crisis regimes have higher volatility). If 3 regimes fail, fall back to 2 regimes. Increase EM iterations via em_iter parameter. Log convergence diagnostics.
**Warning signs:** RuntimeWarning about convergence; one regime probability always near 0 or 1; unrealistic transition probabilities.

### Pitfall 3: Stationarity Test Disagreement
**What goes wrong:** ADF says stationary, KPSS says non-stationary (or vice versa). The dual-test gives contradictory results.
**Why it happens:** Series may be near the stationarity boundary, have structural breaks, or be trend-stationary but not level-stationary.
**How to avoid:** When tests disagree, default to differencing (conservative approach). Log the disagreement. Consider testing with trend regression='ct' in addition to 'c'. Some economic series (like profit rate) may need trend removal rather than differencing.
**Warning signs:** ADF p-value near 0.05 threshold; KPSS p-value near 0.05 threshold; indicators that are conceptually bounded (ratios) testing as non-stationary.

### Pitfall 4: Forecast Explosion After Differencing
**What goes wrong:** Forecasts on differenced data are cumulated back to levels, but small errors in the differenced forecasts compound, producing unrealistic level forecasts that diverge sharply.
**Why it happens:** Integration (inverse differencing) amplifies forecast uncertainty. CI bands also widen dramatically with horizon.
**How to avoid:** Cap forecast horizon at 16 quarters maximum. Show CI bands -- they communicate genuine uncertainty. If forecasts are clearly unreasonable (e.g., negative profit rate), apply domain constraints. Consider using the VAR in levels if stability conditions allow (check eigenvalues of companion matrix).
**Warning signs:** Forecast values outside historical range by a large margin; CI bands wider than the entire historical range of the variable.

### Pitfall 5: SSE Connection Leaks
**What goes wrong:** SSE connections stay open indefinitely if client disconnects without proper cleanup, exhausting server resources.
**Why it happens:** Browser tab closed during training, network interruption, or frontend error.
**How to avoid:** Follow the existing pattern in `status.py`: timeout counter with max_timeouts, heartbeat events, pubsub cleanup in finally block. EventSourceResponse handles client disconnect detection automatically.
**Warning signs:** Increasing Redis pubsub subscriber count; memory growth in Uvicorn workers; stale connections visible in Redis CLIENT LIST.

### Pitfall 6: Race Condition on Result Replacement
**What goes wrong:** Frontend fetches forecast data while backend is mid-write, getting partial/inconsistent results.
**Why it happens:** Model training produces many cache keys (per-indicator forecasts, backtest results, regime probabilities). If these are written individually, a read between writes gets a mix of old and new results.
**How to avoid:** Write all results under a versioned key prefix (e.g., `ecpm:model:v{timestamp}:{indicator}`). Only update the "current version" pointer after all results are cached. Frontend reads from the current version pointer. Atomic swap.
**Warning signs:** Chart showing forecast from new model but regime badge from old model; backtest results inconsistent with displayed forecasts.

## Code Examples

### SSE Progress Streaming (Reusing Phase 1 Pattern)
```python
# Source: existing ecpm/api/status.py fetch_stream pattern
@router.get("/training/stream")
async def training_stream():
    """Stream model training progress via SSE."""
    from sse_starlette.sse import EventSourceResponse

    async def _event_generator():
        redis = _get_redis()
        if redis is None:
            yield {"event": "error", "data": '{"status": "no_redis"}'}
            return

        pubsub = redis.pubsub()
        await pubsub.subscribe("ecpm:training:progress")

        yield {"event": "connected", "data": '{"status": "connected"}'}

        timeout_count = 0
        max_timeouts = 300  # 5 min max for training
        while timeout_count < max_timeouts:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message and message["type"] == "message":
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                yield {"event": "progress", "data": data}

                parsed = json.loads(data)
                if parsed.get("status") in ("complete", "error"):
                    break
                timeout_count = 0
            else:
                timeout_count += 1
                yield {"event": "heartbeat", "data": '{"status": "waiting"}'}

        await pubsub.unsubscribe("ecpm:training:progress")
        await pubsub.close()

    return EventSourceResponse(_event_generator())
```

### Redis Cache Strategy for Model Outputs
```python
# Pattern: Versioned cache keys for atomic result swap
import json
import time

CACHE_TTL = 86400  # 24 hours

async def cache_model_results(redis, results: dict) -> str:
    """Cache all model outputs under a versioned prefix.

    Returns the version key for the current run.
    """
    version = str(int(time.time()))
    prefix = f"ecpm:model:v{version}"

    # Cache forecasts per indicator
    for indicator, forecast in results["forecasts"].items():
        key = f"{prefix}:forecast:{indicator}"
        await redis.set(key, json.dumps(forecast), ex=CACHE_TTL)

    # Cache regime switching results
    await redis.set(
        f"{prefix}:regime",
        json.dumps(results["regime"]),
        ex=CACHE_TTL,
    )

    # Cache backtest results
    for episode, backtest in results["backtests"].items():
        key = f"{prefix}:backtest:{episode}"
        await redis.set(key, json.dumps(backtest), ex=CACHE_TTL)

    # Cache crisis index
    await redis.set(
        f"{prefix}:crisis_index",
        json.dumps(results["crisis_index"]),
        ex=CACHE_TTL,
    )

    # Atomic swap: update current version pointer
    await redis.set("ecpm:model:current_version", version)

    return version

async def get_current_forecast(redis, indicator: str) -> dict | None:
    """Fetch current forecast for an indicator."""
    version = await redis.get("ecpm:model:current_version")
    if not version:
        return None
    key = f"ecpm:model:v{version}:forecast:{indicator}"
    data = await redis.get(key)
    return json.loads(data) if data else None
```

### Composite Crisis Probability Index
```python
# Source: Custom implementation following Marxist crisis theory
import numpy as np
import pandas as pd

# Crisis mechanism sub-index weights (Claude's discretion: equal weighting default)
DEFAULT_WEIGHTS = {
    "trpf": 1/3,          # Tendency of Rate of Profit to Fall
    "realization": 1/3,    # Realization/underconsumption crisis
    "financial": 1/3,      # Financial fragility
}

# Indicator-to-mechanism mapping
MECHANISM_INDICATORS = {
    "trpf": ["rate_of_profit", "occ", "rate_of_surplus_value", "mass_of_profit"],
    "realization": ["productivity_wage_gap"],
    "financial": ["credit_gdp_gap", "financial_real_ratio", "debt_service_ratio"],
}

def compute_crisis_index(
    indicators: dict[str, pd.Series],
    weights: dict[str, float] | None = None,
) -> dict:
    """Compute Composite Crisis Probability Index with mechanism decomposition.

    Each indicator is normalized to [0, 1] range using historical percentiles,
    then combined within mechanism groups, then across mechanisms.

    For TRPF indicators: lower rate of profit = higher crisis probability.
    For financial indicators: higher values = higher crisis probability.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    mechanism_scores = {}

    for mechanism, indicator_slugs in MECHANISM_INDICATORS.items():
        available = [s for s in indicator_slugs if s in indicators]
        if not available:
            mechanism_scores[mechanism] = pd.Series(0, index=indicators[next(iter(indicators))].index)
            continue

        normalized = []
        for slug in available:
            series = indicators[slug].dropna()
            # Percentile rank within historical distribution
            percentile = series.rank(pct=True)

            # Invert TRPF indicators (lower profit rate = higher crisis signal)
            if mechanism == "trpf" and slug in ("rate_of_profit",):
                percentile = 1 - percentile

            normalized.append(percentile)

        # Average within mechanism
        mechanism_scores[mechanism] = pd.concat(normalized, axis=1).mean(axis=1)

    # Composite index = weighted sum across mechanisms
    composite = sum(
        weights[m] * mechanism_scores[m]
        for m in mechanism_scores
    ) * 100  # Scale to 0-100%

    return {
        "composite": composite,
        "trpf": mechanism_scores.get("trpf", pd.Series()),
        "realization": mechanism_scores.get("realization", pd.Series()),
        "financial": mechanism_scores.get("financial", pd.Series()),
    }
```

### Pydantic Response Schemas for Forecast Endpoints
```python
# Source: follows existing ecpm/schemas/series.py pattern
from pydantic import BaseModel, ConfigDict
from typing import Optional
import datetime as dt

class ForecastPoint(BaseModel):
    """Single forecast data point with CI bands."""
    date: str  # ISO date
    point: float
    lower_68: float
    upper_68: float
    lower_95: float
    upper_95: float

class IndicatorForecast(BaseModel):
    """Forecast for a single indicator."""
    indicator: str
    horizon_quarters: int
    forecasts: list[ForecastPoint]
    model_info: dict  # lag order, AIC, differencing order, etc.

class RegimeResult(BaseModel):
    """Regime switching model results."""
    current_regime: int
    regime_label: str  # "Normal", "Stagnation", "Crisis"
    regime_probabilities: dict[str, float]
    transition_matrix: list[list[float]]
    smoothed_probabilities: list[dict]  # time series of probabilities

class CrisisIndex(BaseModel):
    """Composite Crisis Probability Index with decomposition."""
    current_value: float  # 0-100
    trpf_component: float
    realization_component: float
    financial_component: float
    history: list[dict]  # time series of composite + components

class BacktestResult(BaseModel):
    """Backtest against a specific crisis episode."""
    episode_name: str
    start_date: str
    end_date: str
    crisis_index_series: list[dict]  # time series of composite + components
    warning_12m: bool  # Did index rise in 12-month window?
    warning_24m: bool  # Did index rise in 24-month window?
    peak_value: float
    peak_date: str

class TrainingStatus(BaseModel):
    """Training pipeline progress."""
    task_id: str
    status: str  # "idle", "running", "complete", "error"
    current_step: str  # "stationarity", "var", "svar", "regime_switching", "backtests"
    steps: list[dict]  # [{name, status, duration_ms, detail}]
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-equation ARIMA forecasting | Multivariate VAR/SVAR | Standard since Sims (1980) | Captures cross-variable dynamics critical for Marxist indicator interdependence |
| Chow test for structural breaks | Markov regime-switching | Hamilton (1989), mature in statsmodels ~2017 | Probabilistic regime classification instead of binary break detection |
| Manual SVAR identification via exclusion | A/B matrix specification with 'E' markers | statsmodels standardized approach | Cleaner API than manual matrix algebra |
| statsmodels 0.13 forecast methods | statsmodels 0.14.6 forecast_interval | Dec 2025 | Stable API, improved numerical stability |

**Deprecated/outdated:**
- `statsmodels.tsa.api.SVAR()` direct import: Use `from statsmodels.tsa.vector_ar.svar_model import SVAR` for explicit import
- Custom bootstrap CI for VAR: `forecast_interval()` provides analytical CIs that are faster and standard

## Open Questions

1. **Optimal number of Markov regimes**
   - What we know: 3 regimes (Normal/Stagnation/Crisis) is theoretically motivated. Hamilton (1989) used 2 regimes for US GDP.
   - What's unclear: Whether macro data has sufficient variation to reliably estimate 3 distinct regimes, or if 2 (Normal/Crisis) converges better.
   - Recommendation: Try 3 regimes first. If convergence fails or one regime is degenerate (< 5% of observations), fall back to 2 regimes. Log which was used.

2. **Crisis Index weighting scheme**
   - What we know: Equal weighting (1/3 each for TRPF, realization, financial) is the simplest defensible approach.
   - What's unclear: Whether historically-calibrated weights (e.g., from GFC backtest) would improve predictive power without overfitting.
   - Recommendation: Start with equal weights. After backtesting, if one mechanism consistently dominates across all 6 episodes, consider marginal adjustment. Keep weights configurable.

3. **Handling short sample for backtests**
   - What we know: Some indicators (financial fragility) may not have data going back to 1929 (Great Depression) or 1973 (Oil crisis).
   - What's unclear: Whether to skip early backtests or use whatever data is available.
   - Recommendation: Run each backtest with available data. Report which indicators were included/excluded per episode. GFC (2007-2009) is the primary validation target per requirements.

4. **SVAR identification restrictions beyond recursive ordering**
   - What we know: Recursive (Cholesky) ordering is standard and sufficient for initial implementation. The ordering encodes the Marxist causal chain.
   - What's unclear: Whether non-recursive restrictions (e.g., blocking specific contemporaneous effects) would better capture Marxist theory.
   - Recommendation: Start with recursive (lower triangular A matrix). Revisit only if impulse responses show economically implausible patterns.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio 0.24.x |
| Config file | backend/pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `cd /home/marcellinor/Desktop/ECPM/backend && python -m pytest tests/ -x -q --timeout=30` |
| Full suite command | `cd /home/marcellinor/Desktop/ECPM/backend && python -m pytest tests/ -v --timeout=60` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MODL-01 | VAR fitting with lag selection produces valid results | unit | `pytest tests/test_var_model.py::test_var_lag_selection -x` | No -- Wave 0 |
| MODL-02 | ADF + KPSS tests run on all indicators before VAR | unit | `pytest tests/test_stationarity.py::test_dual_stationarity -x` | No -- Wave 0 |
| MODL-03 | SVAR fits with A matrix restrictions | unit | `pytest tests/test_svar_model.py::test_svar_identification -x` | No -- Wave 0 |
| MODL-04 | Forecasts include 68% and 95% CI bands | unit | `pytest tests/test_var_model.py::test_forecast_confidence_intervals -x` | No -- Wave 0 |
| MODL-05 | Backtest against GFC shows pre-crisis signal | integration | `pytest tests/test_backtest.py::test_gfc_backtest -x` | No -- Wave 0 |
| MODL-06 | Markov regime-switching detects regimes | unit | `pytest tests/test_regime_switching.py::test_regime_detection -x` | No -- Wave 0 |
| MODL-07 | Composite Crisis Index computes weighted score | unit | `pytest tests/test_crisis_index.py::test_composite_index -x` | No -- Wave 0 |
| MODL-08 | Crisis Index decomposes by mechanism | unit | `pytest tests/test_crisis_index.py::test_mechanism_decomposition -x` | No -- Wave 0 |
| DASH-06 | Forecast API returns properly structured JSON | integration | `pytest tests/test_api_forecasting.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `cd /home/marcellinor/Desktop/ECPM/backend && python -m pytest tests/ -x -q --timeout=30`
- **Per wave merge:** `cd /home/marcellinor/Desktop/ECPM/backend && python -m pytest tests/ -v --timeout=60`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_stationarity.py` -- covers MODL-02 (ADF + KPSS dual test)
- [ ] `tests/test_var_model.py` -- covers MODL-01, MODL-04 (VAR fitting, forecasts with CIs)
- [ ] `tests/test_svar_model.py` -- covers MODL-03 (SVAR identification)
- [ ] `tests/test_regime_switching.py` -- covers MODL-06 (Markov regime detection)
- [ ] `tests/test_crisis_index.py` -- covers MODL-07, MODL-08 (composite index, decomposition)
- [ ] `tests/test_backtest.py` -- covers MODL-05 (GFC backtest)
- [ ] `tests/test_api_forecasting.py` -- covers DASH-06 (API endpoints)
- [ ] `tests/conftest.py` additions -- mock indicator data fixtures (synthetic time series for testing VAR/regime models)
- [ ] Framework install: `pip install statsmodels>=0.14.6` (add to pyproject.toml dependencies)

## Sources

### Primary (HIGH confidence)
- [statsmodels VAR documentation](https://www.statsmodels.org/dev/vector_ar.html) -- VAR, SVAR, forecast_interval, IRF, lag selection API
- [statsmodels adfuller](https://www.statsmodels.org/dev/generated/statsmodels.tsa.stattools.adfuller.html) -- ADF test parameters and return values
- [statsmodels kpss](https://www.statsmodels.org/dev/generated/statsmodels.tsa.stattools.kpss.html) -- KPSS test null hypothesis and parameters
- [statsmodels MarkovAutoregression](https://www.statsmodels.org/dev/generated/statsmodels.tsa.regime_switching.markov_autoregression.MarkovAutoregression.html) -- Constructor params, fit method, smoothed probabilities
- [statsmodels SVAR](https://www.statsmodels.org/dev/generated/statsmodels.tsa.vector_ar.svar_model.SVAR.html) -- A/B matrix specification with 'E' markers
- [statsmodels PyPI](https://pypi.org/project/statsmodels/) -- Version 0.14.6, Dec 2025
- [Celery Canvas docs](https://docs.celeryq.dev/en/stable/userguide/canvas.html) -- chain, group, chord primitives
- [Recharts API](https://recharts.github.io/en-US/api/) -- Area, ReferenceArea, ComposedChart components
- Existing codebase: `ecpm/api/status.py` (SSE pattern), `ecpm/tasks/` (Celery pattern), `ecpm/cache.py` (Redis pattern)

### Secondary (MEDIUM confidence)
- [statsmodels Markov switching regression example](https://www.statsmodels.org/dev/examples/notebooks/generated/markov_regression.html) -- Verified regime switching usage patterns
- [VAR best practices (machinelearningplus)](https://machinelearningplus.com/time-series/vector-autoregression-examples-python/) -- Lag selection, stationarity preprocessing workflow
- [Recharts stacked area examples](https://recharts.github.io/en-US/examples/StackedAreaChart/) -- Stacking patterns for CI bands

### Tertiary (LOW confidence)
- Crisis Index weighting scheme: Custom design following Marxist economic theory; no established standard library or reference implementation exists. Equal weighting is a starting point, not empirically validated.
- Backtest "12-24 month warning window" criterion: Domain-specific success metric from requirements, not from an established backtesting framework.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- statsmodels is the established Python econometrics library; verified API via official docs
- Architecture: HIGH -- follows existing project patterns (Celery tasks, Redis cache, SSE streaming, Recharts charts)
- Modeling patterns: HIGH -- VAR/SVAR/ADF/KPSS APIs verified against official statsmodels documentation
- Regime switching: MEDIUM -- API verified, but 3-regime convergence behavior depends on actual data characteristics
- Crisis Index: MEDIUM -- custom implementation; weighting scheme is researcher's discretion, not library-provided
- Pitfalls: HIGH -- based on well-documented econometric challenges and observed project patterns
- Frontend CI bands: MEDIUM -- Recharts Area component works for bands but exact implementation may need iteration

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (statsmodels stable; Recharts stable; project patterns established)
