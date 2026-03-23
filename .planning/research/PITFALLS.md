# Pitfalls Research

**Domain:** Macroeconomic data analysis, Marxist political economy modeling, crisis prediction dashboard
**Researched:** 2026-03-23
**Confidence:** HIGH (data pipeline, API integration), MEDIUM (econometric modeling, Marxist category translation), HIGH (deployment, visualization)

## Critical Pitfalls

### Pitfall 1: Look-Ahead Bias in Historical Crisis Calibration

**What goes wrong:**
When calibrating the model against known crisis episodes (1929, 1973, 2008, etc.), you inadvertently use data that was not available at the time. For example, GDP figures are revised multiple times after initial release -- the "final" value for Q1 GDP is not known until months later. If your model trains on revised data but claims to "predict" a crisis that occurred before those revisions, your accuracy is illusory.

**Why it happens:**
FRED and BEA serve the latest revised values by default. Developers pull the current vintage of a series without realizing it has been revised 3-5 times since initial publication. National accounts data is especially revision-heavy: BEA corporate profits undergo annual and comprehensive revisions that can shift values by billions.

**How to avoid:**
- Use FRED's "vintage dates" (ALFRED) to retrieve point-in-time data for all historical calibration. The `fredapi` Python library supports `get_series_all_releases()` and `get_series_as_of_date()`.
- For BEA, vintage data is NOT available through the official API. Use the `datapungibea` package which extends retrieval to include vintages, or manually archive snapshots.
- Separate "training" data (point-in-time vintages) from "display" data (latest revisions) in the database schema.
- Tag every observation with `vintage_date` alongside `observation_date` in TimescaleDB.

**Warning signs:**
- Crisis prediction accuracy that is suspiciously high (above 80% on historical episodes).
- No vintage date column in the time-series schema.
- Using `fredapi.get_series()` without specifying `realtime_start`/`realtime_end`.

**Phase to address:**
Phase 1 (data ingestion). The schema must support vintages from day one, even if the MVP only fetches latest values. Retrofitting vintage support into a flat time-series schema is painful.

---

### Pitfall 2: NIPA-to-Marxist Category Translation Is Methodologically Contested

**What goes wrong:**
The rate of profit, organic composition of capital (OCC), and rate of surplus value are not directly observable in national accounts. Translating NIPA categories into Marxist variables requires decisions on: (a) productive vs. unproductive labor, (b) what counts as constant vs. variable capital, (c) how to handle depreciation, and (d) whether to use current-cost or historical-cost valuation. Different Marxist economists (Shaikh, Moseley, Kliman, Roberts) make different choices and get qualitatively different results. There is no consensus.

**Why it happens:**
NIPA was designed for bourgeois national accounting. It does not distinguish productive from unproductive labor, does not separate surplus value from total value added, and aggregates corporate profits in ways that conflate interest, rent, and profit of enterprise. Developers assume there is a "standard" formula and implement whichever paper they read first.

**How to avoid:**
- Make the translation methodology explicit and configurable. Define a `TranslationConfig` or similar that specifies: which NIPA line items map to variable capital, constant capital, surplus value; whether to include or exclude unproductive sectors; current-cost vs. historical-cost capital stock.
- Implement at least two methodological variants (e.g., Shaikh/Tonak vs. Kliman) so the user can compare.
- Document every mapping decision with references to the source text (Marx Vol. I-III chapters, Shaikh & Tonak 1994, etc.).
- Store raw NIPA values alongside computed Marxist categories -- never discard the source data.

**Warning signs:**
- Hard-coded formulas with no documentation of which theoretical tradition they follow.
- Rate of profit calculation that cannot be reproduced from NIPA tables by hand.
- Only one methodology implemented with no indication alternatives exist.

**Phase to address:**
Phase 2 (feature engineering / indicator computation). This is the intellectual core of the project. Rushing it produces a tool that any Marxist economist would immediately question.

---

### Pitfall 3: Mixed-Frequency Data Alignment Corruption

**What goes wrong:**
Macroeconomic data arrives at different frequencies: GDP is quarterly, employment is monthly, financial market data is daily, I-O tables are released every 5 years. Naively joining these series on a common time axis introduces errors: forward-filling quarterly GDP into monthly rows creates false precision; averaging monthly employment into quarterly values loses important within-quarter dynamics; aligning series with different publication lags creates temporal misalignment where "Q1 GDP" is paired with "March employment" but the GDP figure was not actually released until late April.

**Why it happens:**
Pandas makes it trivially easy to `resample()` or `merge_asof()` without thinking about what these operations mean economically. The data "looks right" in the dataframe but is subtly wrong for modeling.

**How to avoid:**
- Store all series at their native frequency in TimescaleDB. Never resample on ingestion.
- Create explicit frequency alignment functions that are invoked at model-time, not ingestion-time. Document the alignment strategy (last-known-value, interpolation, MIDAS weights).
- For VAR models, align to the lowest common frequency (quarterly) using end-of-period values, not averages, for stock variables (capital stock, debt levels), and period sums for flow variables (GDP, investment).
- Track publication dates separately from observation dates. The `publication_lag_days` metadata per series prevents temporal misalignment.

**Warning signs:**
- All series stored at a single frequency in the database.
- `pd.merge()` on date columns without considering publication lags.
- VAR model inputs that mix monthly and quarterly series without explicit alignment documentation.

**Phase to address:**
Phase 1 (data ingestion schema) and Phase 2 (feature engineering). The schema must support multi-frequency storage; the feature engineering layer must handle alignment explicitly.

---

### Pitfall 4: VAR/SVAR Model Misspecification Cascade

**What goes wrong:**
VAR models require stationary inputs, correct lag order selection, and (for SVAR) theoretically justified identification restrictions. Getting any of these wrong produces nonsense impulse response functions and forecasts. Specifically: (a) running VAR on non-stationary series produces spurious relationships; (b) wrong lag order either overfits or misses dynamics; (c) Cholesky decomposition in SVAR is ordering-dependent -- changing variable order changes the results.

Additionally, statsmodels' SVAR implementation has known issues: no unit tests for impulse response functions or forecast error variance decomposition, and bugs related to numpy shape mismatches in masked assignments. Post-estimation results may silently produce incorrect values.

**Why it happens:**
VAR looks easy: fit the model, call `.irf()`, plot. The API hides the statistical assumptions. Developers skip unit root tests (ADF/KPSS), use default lag order, and pick variable ordering arbitrarily.

**How to avoid:**
- Mandatory preprocessing pipeline: ADF + KPSS tests for each series; difference non-stationary series; document which series are I(0) vs. I(1).
- Use information criteria (AIC, BIC, HQIC) for lag selection, cross-validated against out-of-sample forecast error.
- For SVAR: derive identification restrictions from theory (Marxist crisis theory provides causal ordering), not convenience. Document the economic justification for the A and B matrices.
- Validate statsmodels SVAR output against a reference implementation (e.g., R's `vars` package) for at least one test case before trusting it in production.
- Consider cointegration testing (Johansen) when series are I(1) -- VECM may be more appropriate than differenced VAR.

**Warning signs:**
- No stationarity tests in the pipeline.
- Lag order hardcoded without selection criteria.
- Impulse response functions that don't converge to zero (sign of non-stationarity or explosive roots).
- SVAR results that change dramatically with variable reordering.

**Phase to address:**
Phase 3 (predictive modeling). Build the preprocessing/validation pipeline before the model itself. Stub the model in Phase 1, but do not ship VAR results without the validation layer.

---

### Pitfall 5: Leontief Inverse Computation Failure on Real I-O Data

**What goes wrong:**
The Leontief inverse `(I - A)^{-1}` requires that the technical coefficient matrix A satisfies specific conditions: spectral radius r(A) < 1 and the Hawkins-Simon conditions (all principal minors of I-A are positive). Real-world I-O tables, especially at fine sectoral granularity, can violate these conditions due to: (a) sectors that are pure intermediaries (rows of near-zeros in capital matrix), (b) aggregation artifacts, (c) negative entries from statistical discrepancies. A naive `np.linalg.inv(I - A)` will either raise a `LinAlgError` or, worse, return a numerically unstable result with huge values that silently corrupt downstream analysis.

**Why it happens:**
Textbook examples use clean 3x3 matrices. Real BEA I-O tables have 71+ sectors with messy data. The singular or near-singular case is common, not edge-case.

**How to avoid:**
- Check the condition number of (I-A) before inversion. If `np.linalg.cond(I_minus_A) > 1e10`, flag it.
- Verify Hawkins-Simon conditions programmatically before computing the inverse.
- Use `np.linalg.solve(I_minus_A, d)` instead of explicit inversion -- more numerically stable and faster.
- For near-singular cases, use regularized pseudo-inverse or aggregate problematic sectors.
- Validate results: all elements of the Leontief inverse should be non-negative. Negative values indicate numerical or data problems.

**Warning signs:**
- Leontief multipliers with negative values or values exceeding 100.
- `RuntimeWarning: invalid value encountered` from numpy.
- Shock propagation simulation producing infinite or NaN outputs.

**Phase to address:**
Phase 3 (Leontief structural analysis). This is a later-phase feature, but the data ingestion for I-O tables should happen in Phase 2 with validation built in.

---

### Pitfall 6: FRED/BEA API Fragility Treated as Reliable Infrastructure

**What goes wrong:**
The data pipeline assumes API calls will succeed consistently. In reality: FRED rate-limits at 120 requests/minute; BEA API has undocumented rate limits and periodic maintenance windows; series IDs change (BEA table names changed format between 2008 and 2018, e.g., `T10101` vs. `10101`); series get discontinued or redefined; API responses can return partial data without error codes.

**Why it happens:**
During development, you make a few API calls and everything works. The pipeline runs fine for weeks, then silently breaks on a Saturday when the API is under maintenance, or when you hit the rate limit during a bulk historical backfill.

**How to avoid:**
- Implement a retry strategy with exponential backoff (FRED's own retry waits 20 seconds between attempts, max 6 retries).
- Cache all raw API responses in TimescaleDB immediately. Never re-fetch data you already have.
- Build a series metadata registry: track series ID, last known name, expected frequency, last successful fetch, expected next update date.
- Implement data freshness checks: if a series that should update monthly hasn't updated in 45 days, alert (log warning, dashboard indicator).
- For BEA specifically: use the official `beaapi` Python package, but be aware that table/series naming is inconsistent across datasets (`SeriesCode` in NIPA vs. `TimeSeriesID` in IIP).

**Warning signs:**
- No retry logic in API client code.
- No local cache -- every dashboard load triggers API calls.
- Ingestion script that crashes on first API error.
- No monitoring of data freshness / last-update timestamps.

**Phase to address:**
Phase 1 (data ingestion). The API client must be robust from day one. This is the foundation of the entire system.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Single methodology for rate of profit | Ships faster | Cannot compare results, any Marxist economist will question it | MVP only, with clear TODO to add alternatives |
| Storing all series at one frequency | Simpler schema | Data loss, alignment bugs, impossible to add high-frequency data later | Never -- multi-frequency storage is not hard to implement upfront |
| Hardcoded FRED series IDs | Quick to wire up | Series get renamed/discontinued, no discoverability | MVP only, must add series registry in Phase 2 |
| Skipping vintage date support | Simpler ingestion | Historical calibration is meaningless without it, expensive to retrofit | MVP can fetch latest-only but schema must have the column |
| Using Recharts for all charts | Fast to prototype | Performance cliff at 5000+ data points, limited customization for I-O matrix viz | MVP only, plan migration to ECharts or custom D3 for complex views |
| Single Docker Compose for dev and prod | One config to maintain | Dev needs hot-reload volumes, prod needs optimized builds; conflating them causes both to be worse | Never -- use override files from day one |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| FRED API | Fetching ALL years with `observation_start=earliest` in one call | Paginate with `offset` parameter; max 100,000 observations per request |
| FRED API | Ignoring `realtime_start`/`realtime_end` parameters | Always set these for historical analysis to avoid look-ahead bias |
| BEA API | Using `X` or `ALL` for year parameter | Specify exact years needed; broad queries return massive payloads and may timeout |
| BEA API | Assuming consistent series identification | Use `SeriesCode` for NIPA, `TimeSeriesID` for IIP; validate per dataset |
| BEA API | Expecting vintage data from official API | Vintage data not available via BEA API; use `datapungibea` or manual archiving |
| TimescaleDB | Creating hypertable with wrong chunk interval | Match chunk interval to query patterns: 1 month for daily data, 1 year for quarterly data |
| TimescaleDB | Not enabling compression on historical data | Enable compression policies for data older than the active analysis window |
| Redis | Caching computed indicators without cache invalidation on data refresh | Use versioned cache keys that include the data vintage date |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| SVG-based charts with full historical series | Dashboard freezes on time-series page, browser tab uses 2GB+ RAM | Use Canvas/WebGL rendering (ECharts) or downsample to viewport resolution | >5,000 data points per chart |
| Recomputing all indicators on every dashboard load | 10+ second page loads, API timeout errors | Pre-compute indicators on data refresh, serve from cache/materialized views | >50 series with >20 derived indicators |
| Full I-O matrix rendered as interactive table | Browser unresponsive with 71x71 BEA sector matrix | Aggregate to ~15 major sectors for interactive view; full matrix as downloadable CSV | >30x30 matrix with hover/click interactions |
| Unbounded VAR forecast horizon | Memory explosion, nonsensical long-horizon forecasts | Cap forecast horizon at 8-12 quarters; display confidence intervals that widen appropriately | >20 quarter forecast with >6 variables |
| Docker volume mounts on macOS/Windows | 10x slower file I/O for hot reload, webpack watch misses changes | Use `WATCHPACK_POLLING=true` for Next.js; named volumes for `node_modules` and `.next` | Any non-Linux Docker host |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| API keys committed to repository | Key revocation, rate limit abuse | Use `.env` file excluded from git; Docker Compose `env_file` directive; document in README |
| API keys hardcoded in frontend code | Exposed in browser, key theft | All API calls go through FastAPI backend; frontend never contacts FRED/BEA directly |
| No input validation on simulation parameters | Agent-based model with malicious parameters runs forever, OOM | Validate all simulation inputs server-side: max agents, max steps, parameter bounds |
| TimescaleDB exposed on default port without password | Data tampering | Bind to `127.0.0.1` only in Docker Compose; set strong password even for local dev |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing derived Marxist indicators without methodology transparency | User cannot evaluate results, cannot compare with published research | Every indicator links to its formula, source series, and theoretical reference |
| Default chart timeframe too long (1947-present) | Clutter, slow rendering, trend dominates cycle | Default to last 20 years with easy expansion; highlight NBER recession bands |
| No indication of data freshness | User doesn't know if they're looking at stale data | Display "Data as of: [date]" and "Last refresh: [timestamp]" on every chart |
| Crisis probability as single number without decomposition | Black box, no analytical value | Show probability gauge with breakdown by crisis mechanism (TRPF, realization, financial, etc.) |
| I-O matrix as raw numbers | Impossible to interpret visually | Use heatmap with sector labels, highlight top-N linkages, allow drill-down |

## "Looks Done But Isn't" Checklist

- [ ] **Data ingestion:** Often missing retry logic and freshness monitoring -- verify that a failed API call does not crash the pipeline and that stale data is flagged
- [ ] **Rate of profit:** Often missing documentation of methodology -- verify that every formula maps to specific NIPA table/line items with theoretical citations
- [ ] **VAR model:** Often missing stationarity preprocessing -- verify ADF/KPSS tests run before model fitting and that non-stationary series are differenced
- [ ] **Historical calibration:** Often missing vintage-correct data -- verify that crisis episode analysis uses point-in-time data, not latest revisions
- [ ] **Dashboard charts:** Often missing loading states and error handling -- verify that API failures show informative messages, not blank charts or spinners
- [ ] **Docker deployment:** Often missing health checks -- verify that `docker compose up` waits for TimescaleDB to be ready before FastAPI starts
- [ ] **Leontief analysis:** Often missing numerical validation -- verify that Leontief inverse elements are non-negative and multipliers are reasonable (typically 1.0-3.0)
- [ ] **Composite crisis index:** Often missing confidence intervals -- verify that the index shows uncertainty, not just a point estimate

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Look-ahead bias in calibration | MEDIUM | Add vintage date column to schema, re-fetch historical data with ALFRED, rerun calibration |
| Wrong methodology for rate of profit | HIGH | Refactor indicator computation into pluggable strategies, recompute all derived series |
| Mixed-frequency corruption | HIGH | Redesign schema for native-frequency storage, rebuild alignment layer, revalidate all models |
| VAR misspecification | LOW | Add preprocessing pipeline (stationarity tests, lag selection), refit models |
| Leontief numerical failure | LOW | Add condition number check and Hawkins-Simon validation, switch to `np.linalg.solve` |
| API fragility | LOW | Add retry/backoff wrapper, implement local cache, add freshness monitoring |
| Chart performance collapse | MEDIUM | Swap charting library from Recharts to ECharts for heavy charts, implement data windowing |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Look-ahead bias | Phase 1: Data Ingestion | Schema has `vintage_date` column; ALFRED retrieval method exists |
| NIPA-to-Marxist translation | Phase 2: Feature Engineering | Methodology is configurable; at least one alternative can be toggled; formulas documented |
| Mixed-frequency alignment | Phase 1 (schema) + Phase 2 (alignment) | Series stored at native frequency; alignment functions have explicit strategy parameter |
| VAR/SVAR misspecification | Phase 3: Predictive Modeling | Preprocessing pipeline includes stationarity tests; lag selection uses information criteria |
| Leontief numerical failure | Phase 3: Structural Analysis | Condition number checked before inversion; Hawkins-Simon validated; output non-negativity asserted |
| API fragility | Phase 1: Data Ingestion | Retry with backoff implemented; local cache populated; freshness monitoring active |
| Chart performance | Phase 4: Dashboard | Charts handle 10,000+ points without freeze; complex visualizations use Canvas/WebGL |
| Docker deployment | Phase 1: Infrastructure | Separate dev/prod compose files; health checks on all services; hot reload confirmed working |

## Sources

- [FRED API Error Documentation](https://fred.stlouisfed.org/docs/api/fred/errors.html)
- [fedfred Advanced Usage (rate limiting, caching)](https://nikhilxsunder.github.io/fedfred/installation/advanced_usage.html)
- [BEA API User Guide (November 2024)](https://apps.bea.gov/api/_pdf/bea_web_service_api_user_guide.pdf)
- [datapungibea - BEA vintage data](https://github.com/jjotterson/datapungibea)
- [beaapi - Official BEA Python library](https://github.com/us-bea/beaapi)
- [NIPA Handbook Chapter 13: Corporate Profits (December 2024)](https://www.bea.gov/resources/methodologies/nipa-handbook/pdf/chapter-13.pdf)
- [Freeman - New Approach to Calculating Rate of Profit (methodological debate)](https://www.ppesydney.net/content/uploads/2020/05/Marxist-economics-On-Freemans-new-approach-to-calculating-the-rate-of-profit.pdf)
- [Michael Roberts - World Rate of Profit evidence](https://thenextrecession.wordpress.com/2022/01/22/a-world-rate-of-profit-important-new-evidence/)
- [Basu & Manolakos - Econometric test of TRPF](https://people.umass.edu/dbasu/Papers/BasuManolakos_RRPE_Preprint.pdf)
- [QuantEcon - Input-Output Models in Python](https://intro.quantecon.org/input_output.html)
- [statsmodels VAR documentation](https://www.statsmodels.org/stable/vector_ar.html)
- [statsmodels SVAR issue #6537 (known bugs)](https://github.com/statsmodels/statsmodels/issues/6537)
- [Seven Sins of Quantitative Investing (look-ahead bias)](https://bookdown.org/palomar/portfoliooptimizationbook/8.2-seven-sins.html)
- [Best React Chart Libraries 2025 (LogRocket)](https://blog.logrocket.com/best-react-chart-libraries-2025/)
- [Next.js Hot Reload in Docker](https://dev.to/yuvraajsj18/enabling-hot-reloading-for-nextjs-in-docker-4k39)
- [Next.js HMR Docker issue #36774](https://github.com/vercel/next.js/issues/36774)

---
*Pitfalls research for: Economic Crisis Prediction Model (Marxist political economy modeling platform)*
*Researched: 2026-03-23*
