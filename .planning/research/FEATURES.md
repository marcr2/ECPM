# Feature Research

**Domain:** Macroeconomic crisis prediction platform (Marxist political economy)
**Researched:** 2026-03-23
**Confidence:** MEDIUM -- niche domain with no direct competitors; features synthesized from adjacent platforms (Macrobond, FRED dashboards, IMF EWS tools, Mesa ABM) and academic literature on Marxist empirical economics

## Feature Landscape

### Table Stakes (Users Expect These)

Features a macroeconomic analysis/prediction platform must have or it feels broken.

#### Module A: Data Ingestion / ETL

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| FRED API data retrieval | Primary US macro data source (840K+ series). Every econ data tool supports it. | LOW | Use `fredapi` or `fedfred` Python package. Rate-limited but generous. |
| BEA NIPA table ingestion | Corporate profits, national income, fixed assets -- raw material for Marxist categories. Without NIPA data, cannot compute rate of profit. | MEDIUM | BEA API is clunkier than FRED. Need specific table/line mappings (Tables 1.14, 6.1, etc.) |
| Automated scheduled fetching | Users expect data to stay current without manual intervention. Every serious platform (Macrobond, CEIC, Trading Economics) auto-updates. | LOW | Cron job or APScheduler. Quarterly cadence matches NIPA release schedule. |
| Data caching and persistence | Re-fetching on every request is unacceptable. Must store locally. | LOW | TimescaleDB handles this. Cache raw series with metadata. |
| Series metadata management | Must know what each series is -- units, frequency, seasonality, source, last updated. | LOW | FRED API provides rich metadata. Store alongside data. |
| Missing data handling | Economic time series have gaps, revisions, frequency mismatches. Silent NaNs corrupt downstream calculations. | MEDIUM | Interpolation, forward-fill, explicit gap flagging. Critical for multi-frequency joins (monthly vs quarterly vs annual). |
| Data vintage / revision tracking | BEA revises NIPA data. Rate of profit calculated on first-release vs revised data can differ materially. | MEDIUM | Store vintages. MVP can skip this but must design schema to support it later. |

#### Module B: Feature Engineering (Theoretical Translation)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Rate of profit calculation | THE central indicator in Marxist crisis theory (s/(c+v)). Without it the platform has no reason to exist. | MEDIUM | Requires mapping NIPA categories to Marxist categories. Multiple methodologies exist (Shaikh, Moseley, Kliman, Roberts). Pick one canonical approach, document mapping. |
| Organic composition of capital (OCC) | c/v ratio -- the driver of TRPF. Inseparable from rate of profit analysis. | MEDIUM | Derived from same NIPA mappings. Constant capital approximated from BEA fixed assets tables. |
| Rate of surplus value | s/v -- exploitation rate. Core Marxist indicator alongside ROP and OCC. | MEDIUM | Variable capital approximated from compensation of employees. Surplus value = net value added minus compensation. |
| Mass vs rate of profit divergence | Marx's key counteracting tendency: mass of profit can rise while rate falls. Crisis occurs when mass peaks. | LOW | Derived calculation once ROP exists. Time-series comparison. |
| Productivity-wage gap | Realization crisis indicator. Every heterodox economics platform tracks this. Well-understood data. | LOW | BLS productivity data + real wage data. Straightforward. |
| Clear methodology documentation | Users of a theoretical economics tool MUST know how indicators are derived. Black-box Marxist calculations are useless. | LOW | In-app or linked documentation explaining each NIPA-to-Marx mapping. |

#### Module C: Predictive Modeling

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Time-series forecasting (VAR/SVAR) | Standard econometric method for macro forecasting. Any prediction platform needs at least one forecasting approach. | MEDIUM | statsmodels has VAR implementation. Need proper lag selection, stationarity testing. |
| Historical backtesting | Must validate against known crises (1929, 1973, 2001, 2008). Platform credibility depends on this. | MEDIUM | Define crisis episodes, compute indicators historically, check alignment. This is how IMF EWS papers validate. |
| Confidence intervals / uncertainty quantification | Predictions without uncertainty bounds are misleading. Academic and policy tools always show these. | LOW | Built into VAR forecasts. Display as fan charts or bands. |

#### Module D: Frontend Dashboard

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Interactive time-series line charts | Fundamental visualization for economic data. Every platform (FRED, Macrobond, Trading Economics) centers on this. | LOW | Recharts, Plotly, or D3-based. Must support zoom, pan, date range selection. |
| Multi-series overlay | Must compare indicators on same chart (e.g., ROP vs OCC over time). Core analytical workflow. | LOW | Standard charting feature. Dual y-axes for different scales. |
| Date range selection | Drill into specific periods (e.g., pre-2008 buildup). Expected in any time-series tool. | LOW | Brush selector or date picker. |
| Data export (CSV/JSON) | Researchers need to take data into their own tools (R, Stata, spreadsheets). | LOW | API endpoint + download button. |
| Crisis episode annotations | Mark known crisis dates on charts. Contextualizes indicators against historical events. Standard in financial dashboards. | LOW | Vertical lines or shaded regions with labels. |
| Indicator dashboard / overview page | Single view showing current state of all key indicators. Every analytics platform has a summary view. | MEDIUM | Card/grid layout with sparklines and current values. |
| Loading states and error handling | Broken UI with no feedback is unacceptable. | LOW | Skeleton loaders, error boundaries, retry logic. |

### Differentiators (Competitive Advantage)

Features that make ECPM uniquely valuable. No existing tool does these things.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| NIPA-to-Marx category translation engine | The core intellectual contribution. No existing software automates the translation of national accounting data into Marxist categories. Researchers do this manually in spreadsheets. | HIGH | Must be configurable -- different Marxist economists use different mappings. Provide a canonical default (e.g., Shaikh/Tonak methodology) with ability to swap. |
| Six-crisis-typology decomposition | Synthesizing TRPF, realization, disproportionality, financial fragility, imperialist displacement, and cybernetic dysfunction into a unified framework is novel. Academic literature treats these separately. | HIGH | Each typology has its own indicator set. The synthesis into a composite index is original theoretical work. |
| Composite Crisis Probability Index | A single composite index decomposable into crisis mechanisms. IMF has Financial Stress Indexes but nothing that decomposes by Marxist crisis typology. | HIGH | Requires careful weighting methodology. Must be transparent and adjustable, not a black box. |
| Theoretical annotation layer | Linking every indicator, chart, and threshold back to the specific theoretical text (Marx Capital Vol III Ch 13, etc.). Turns a data tool into a pedagogical/research tool. | MEDIUM | Tooltip or sidebar with source references. Could link to marxists.org texts. |
| Leontief I-O reproduction schema visualizer | Interactive visualization of input-output matrices showing sectoral interdependencies. PyIO exists for computation but no one wraps it in an interactive web visualization tied to Marxist reproduction schema analysis. | HIGH | Matrix heatmap + Sankey/chord diagram for flows. Needs BEA I-O tables (published every 5 years, with annual estimates). |
| Regime-switching crisis detection | Markov regime-switching models that endogenously identify "crisis" vs "normal" periods rather than using arbitrary threshold definitions. Academic literature shows these outperform traditional EWS. | HIGH | Hamilton-type Markov-switching model. statsmodels has MarkovRegression. |
| Beer VSM cybernetic system diagram | Visualizing the economy through Stafford Beer's Viable System Model lens. Completely novel in economics software. | MEDIUM | More conceptual/structural than data-driven. Static SVG with dynamic data overlays showing regulatory capacity vs variety. |
| Agent-based simulation (Mesa) | Interactive simulation of capitalist dynamics -- accumulation, competition, crisis emergence from micro behavior. Goes beyond econometric extrapolation to structural modeling. | HIGH | Mesa framework provides visualization via Solara. Significant modeling work to define agents, behaviors, interactions. |
| Counterfactual scenario simulation | "What if OCC rises 10%?" or "What if wages kept pace with productivity?" -- lets researcher explore theoretical mechanisms interactively. | HIGH | Requires well-specified model. Build on top of VAR or ABM. |
| Simulation control panel | Interactive parameter adjustment for agent-based model. Adjust exploitation rate, accumulation rate, credit expansion rate and watch dynamics unfold. | MEDIUM | Mesa's Solara visualization provides a foundation. Custom controls for economic parameters. |

### Anti-Features (Deliberately NOT Building)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Real-time streaming data | "Live crisis detection" sounds exciting | Macro data is released quarterly/monthly with lags. There is no meaningful real-time macro data stream. NIPA data is released with 1-3 month delays. Adds infrastructure complexity (Kafka, websockets) for zero analytical value. | Batch ingestion on data release schedule. Cron job checking for new releases. |
| Multi-user / collaborative features | "Share research with collaborators" | Single-user research tool. Auth, permissions, concurrent editing adds massive complexity. | Export features (CSV, PDF reports). Git-based sharing of configuration. |
| AI/LLM-powered "crisis chat" | Trendy to add LLM interfaces to everything | LLMs hallucinate economic analysis. Undermines the rigorous theoretical framework that is the entire point. Marxist crisis theory is precise -- it should not be mediated by probabilistic text generation. | Theoretical annotation layer with curated source texts. |
| Automated trading signals | "Predict market crashes for profit" | Misunderstands the purpose entirely. Marxist crisis theory analyzes structural contradictions on multi-year timescales, not trading opportunities. Also: legal liability. | Crisis probability index with explicit theoretical decomposition. |
| Mobile-responsive design | "Access on phone" | Dense economic data visualization requires screen real estate. Charts, matrices, multi-panel dashboards are unusable on mobile. Desktop research tool. | Desktop-optimized layout. |
| Cloud deployment / SaaS | "Deploy for others to use" | Adds hosting costs, auth, security, scaling concerns. Personal research tool. | Docker Compose for local deployment. |
| Custom indicator builder (visual/no-code) | "Let users define their own indicators with drag-and-drop" | Massive UI complexity. The translation from NIPA to Marxist categories requires economic expertise, not a visual builder. | Configuration files or Python modules for custom indicators. Extend via code. |
| Comprehensive global coverage (all countries) | "Model every country" | Each country has different statistical agencies, data formats, category definitions. Exponential complexity. | Start with US (FRED/BEA). Design data layer to be extensible. Add countries incrementally in future milestones. |

## Feature Dependencies

```
[FRED/BEA Data Ingestion]
    |
    +---> [Series Metadata Management]
    |
    +---> [Data Caching/Persistence (TimescaleDB)]
    |         |
    |         +---> [Missing Data Handling]
    |                   |
    |                   +---> [NIPA-to-Marx Translation Engine]
    |                             |
    |                             +---> [Rate of Profit]
    |                             +---> [OCC]
    |                             +---> [Rate of Surplus Value]
    |                             +---> [Mass vs Rate Divergence]
    |                             +---> [Productivity-Wage Gap]
    |                             |
    |                             +---> [VAR/SVAR Forecasting]
    |                             |         |
    |                             |         +---> [Historical Backtesting]
    |                             |         +---> [Confidence Intervals]
    |                             |
    |                             +---> [Regime-Switching Detection]
    |                             |
    |                             +---> [Composite Crisis Index]
    |                                       |
    |                                       +---> [Crisis Probability Gauge (Dashboard)]
    |
    +---> [Interactive Time-Series Charts (Dashboard)]
              |
              +---> [Multi-Series Overlay]
              +---> [Date Range Selection]
              +---> [Crisis Episode Annotations]
              +---> [Theoretical Annotation Layer]

[BEA I-O Tables Ingestion] ---> [Leontief I-O Analysis] ---> [Reproduction Schema Visualizer]

[NIPA-to-Marx Translation Engine] ---> [Agent-Based Model (Mesa)]
                                              |
                                              +---> [Simulation Control Panel]
                                              +---> [Counterfactual Scenarios]

[Beer VSM Diagram] --- independent of data pipeline (conceptual overlay)
```

### Dependency Notes

- **Everything requires Data Ingestion:** No downstream feature works without FRED/BEA data flowing in and being stored. This is the absolute foundation.
- **NIPA-to-Marx Translation gates all Marxist indicators:** The translation engine is the critical bottleneck. Until it works, no rate of profit, no OCC, no crisis index.
- **Composite Crisis Index requires multiple indicator families:** Cannot build the composite index until at least 2-3 typology indicator sets are computed.
- **Agent-Based Model is semi-independent:** Can be developed with stylized parameters before real data integration. But calibration against empirical data requires the translation engine.
- **Leontief I-O analysis has its own data path:** BEA I-O tables are separate from NIPA. This is a parallel workstream.
- **Dashboard features can be developed incrementally:** Start with basic charts, add overlays, annotations, and advanced visualizations progressively.

## MVP Definition

### Launch With (v1)

Minimum viable product -- the wired skeleton with core path functional.

- [ ] FRED API data retrieval with caching -- foundation of everything
- [ ] BEA NIPA table ingestion for key tables (fixed assets, national income, corporate profits) -- required for Marxist indicators
- [ ] Automated scheduled fetching (cron) -- data stays current without manual intervention
- [ ] Missing data handling (interpolation, frequency alignment) -- multi-frequency joins are unavoidable
- [ ] NIPA-to-Marx translation engine (one canonical methodology) -- the core intellectual contribution
- [ ] Rate of profit, OCC, rate of surplus value computation -- the three fundamental Marxist indicators
- [ ] Productivity-wage gap indicator -- simplest realization crisis indicator
- [ ] Basic VAR forecasting on key indicators -- minimum viable prediction
- [ ] Historical backtesting against 2008 crisis -- single validation episode proves concept
- [ ] Interactive time-series dashboard with multi-series overlay -- must be able to SEE the indicators
- [ ] Indicator overview/summary page -- at-a-glance state of all computed indicators
- [ ] Crisis episode annotations on charts -- contextualize data against known crises
- [ ] Methodology documentation (in-app or linked) -- transparent derivations
- [ ] Docker Compose deployment -- one command to run the whole system

### Add After Validation (v1.x)

Features to add once core pipeline is proven working.

- [ ] Mass vs rate of profit divergence tracking -- once ROP is validated
- [ ] Consumer debt-to-income, inventory-to-sales ratios -- additional realization indicators
- [ ] Regime-switching crisis detection (Markov) -- upgrade from simple thresholds
- [ ] Composite Crisis Probability Index (initially from TRPF + realization indicators) -- synthesis begins
- [ ] Theoretical annotation layer -- links indicators to Marx/Luxemburg/Lenin source texts
- [ ] Data export (CSV/JSON) -- researcher workflow support
- [ ] Financial fragility indicators (credit expansion, debt-to-equity, fictitious capital proxies) -- third crisis typology
- [ ] Crisis probability gauge with mechanism decomposition on dashboard -- visual composite index

### Future Consideration (v2+)

Features to defer until core is mature.

- [ ] Leontief I-O reproduction schema analysis and visualizer -- separate data source, high complexity
- [ ] Agent-based simulation (Mesa) with control panel -- significant modeling effort, semi-independent workstream
- [ ] Beer VSM cybernetic system diagram -- conceptual innovation, lower data dependency
- [ ] Imperialist displacement indicators (requires World Bank/IMF/BIS data) -- new data sources
- [ ] Counterfactual scenario simulation -- requires mature model
- [ ] Data vintage / revision tracking -- important for rigor but not MVP-blocking
- [ ] Additional country support -- requires new data source integrations per country
- [ ] Anomaly detection (Isolation Forests) for crisis fingerprints -- ML upgrade path

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| FRED/BEA data ingestion + caching | HIGH | LOW | P1 |
| Automated scheduled fetching | HIGH | LOW | P1 |
| Missing data handling | HIGH | MEDIUM | P1 |
| NIPA-to-Marx translation engine | HIGH | HIGH | P1 |
| Rate of profit / OCC / rate of surplus value | HIGH | MEDIUM | P1 |
| Productivity-wage gap | MEDIUM | LOW | P1 |
| Interactive time-series charts | HIGH | LOW | P1 |
| Multi-series overlay + date range | HIGH | LOW | P1 |
| Indicator overview page | HIGH | MEDIUM | P1 |
| Crisis episode annotations | MEDIUM | LOW | P1 |
| Basic VAR forecasting | MEDIUM | MEDIUM | P1 |
| Historical backtesting (2008) | HIGH | MEDIUM | P1 |
| Methodology documentation | HIGH | LOW | P1 |
| Docker Compose deployment | HIGH | LOW | P1 |
| Regime-switching detection | HIGH | HIGH | P2 |
| Composite Crisis Index | HIGH | HIGH | P2 |
| Theoretical annotation layer | MEDIUM | MEDIUM | P2 |
| Financial fragility indicators | MEDIUM | MEDIUM | P2 |
| Data export (CSV/JSON) | MEDIUM | LOW | P2 |
| Crisis probability gauge | HIGH | MEDIUM | P2 |
| Leontief I-O analysis + visualizer | HIGH | HIGH | P3 |
| Agent-based simulation (Mesa) | HIGH | HIGH | P3 |
| Beer VSM diagram | MEDIUM | MEDIUM | P3 |
| Counterfactual scenarios | MEDIUM | HIGH | P3 |
| Imperialist displacement indicators | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for launch -- core data pipeline, fundamental Marxist indicators, basic visualization
- P2: Should have, add after core validates -- advanced modeling, composite indexes, richer dashboard
- P3: Nice to have, future milestones -- specialized visualizations, ABM simulation, new data sources

## Competitor Feature Analysis

| Feature | Macrobond / CEIC | FRED Dashboard | IMF EWS Tools | This Platform (ECPM) |
|---------|------------------|----------------|---------------|----------------------|
| Data ingestion | 100+ sources, commercial | FRED only, free | Internal IMF data | FRED + BEA, free, automated |
| Indicator computation | Standard macro indicators | Raw series only | Financial stress indexes | Marxist categories (ROP, OCC, s/v) -- unique |
| Theoretical framework | None (atheoretical) | None | Mainstream (Minsky-adjacent) | Marxist political economy -- unique |
| Crisis prediction | None | None | ML-based EWS, logistic regression | VAR + regime-switching + composite index |
| I-O analysis | None | None | Limited | Leontief reproduction schema -- unique |
| Agent-based modeling | None | None | None | Mesa-based capitalist dynamics -- unique |
| Visualization | Polished, commercial | Basic FRED charts | Internal reports | Interactive Next.js dashboard |
| Price | $$$$ | Free | Internal | Free / open-source |
| Target user | Finance professionals | General public | IMF economists | Marxist researchers |

The competitive advantage is clear: no existing platform translates national accounting data into Marxist categories or models crisis through the lens of capital's structural contradictions. The closest things are academic spreadsheets shared in papers by Michael Roberts, Anwar Shaikh, and others -- but these are static, manual, and not interactive.

## Sources

- [Macrobond](https://www.macrobond.com/) -- commercial macro data platform, feature reference
- [FRED API Documentation](https://fred.stlouisfed.org/docs/api/fred/) -- primary data source capabilities
- [BEA NIPA Tables](https://apps.bea.gov/iTable/index_nipa.cfm) -- national accounting data structure
- [IMF Early Warning Systems paper](https://www.imf.org/en/Publications/WP/Issues/2016/12/30/Early-Warning-Systems-A-Survey-and-a-Regime-Switching-Approach-16293) -- EWS methodology reference
- [Mesa ABM Framework](https://mesa.readthedocs.io/stable/) -- agent-based modeling with Solara visualization
- [PyIO (REAL, Univ. of Illinois)](https://real.illinois.edu/pyio/) -- Python input-output analysis
- [leontief R package](https://cran.r-project.org/web/packages/leontief/vignettes/leontief.html) -- I-O analysis reference implementation
- [fredapi PyPI](https://pypi.org/project/fredapi/) -- Python FRED client
- [Trading Economics](https://tradingeconomics.com) -- commercial data platform, feature reference
- [CEIC Data](https://www.ceicdata.com/en) -- commercial macro data platform, feature reference
- [Springer: Predicting financial crises with ML and model explainability](https://link.springer.com/article/10.1007/s43253-024-00114-4) -- ML crisis prediction features
- [Springer: Indicators of economic crises via clustering](https://link.springer.com/article/10.1007/s41109-020-00280-4) -- crisis indicator methodology

---
*Feature research for: Macroeconomic crisis prediction platform (Marxist political economy)*
*Researched: 2026-03-23*
