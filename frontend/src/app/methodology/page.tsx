"use client";

import { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { FormulaDisplay } from "@/components/indicators/formula-display";
import { Badge } from "@/components/ui/badge";

function SectionCard({
  title,
  children,
  id,
}: {
  title: string;
  children: React.ReactNode;
  id?: string;
}) {
  return (
    <section
      id={id}
      className="rounded-xl border border-border bg-card p-5 space-y-4"
    >
      <h3 className="text-base font-semibold">{title}</h3>
      {children}
    </section>
  );
}

function Prose({ children }: { children: React.ReactNode }) {
  return (
    <div className="text-sm leading-relaxed text-foreground/80 space-y-3">
      {children}
    </div>
  );
}

function FormulaBlock({
  label,
  latex,
}: {
  label: string;
  latex: string;
}) {
  return (
    <div className="rounded-lg bg-muted/50 border border-border/50 p-4 space-y-1">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <FormulaDisplay latex={latex} />
    </div>
  );
}

function DefinitionList({
  items,
}: {
  items: { term: string; definition: string }[];
}) {
  return (
    <dl className="grid gap-2">
      {items.map((item) => (
        <div
          key={item.term}
          className="grid grid-cols-[160px_1fr] gap-2 text-sm"
        >
          <dt className="font-medium text-foreground">{item.term}</dt>
          <dd className="text-foreground/70">{item.definition}</dd>
        </div>
      ))}
    </dl>
  );
}

function SourceBadge({ source }: { source: string }) {
  const colors: Record<string, string> = {
    FRED: "bg-blue-500/15 text-blue-400 border-blue-500/20",
    BEA: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
    "BIS": "bg-purple-500/15 text-purple-400 border-purple-500/20",
    "Fed Z.1": "bg-amber-500/15 text-amber-400 border-amber-500/20",
    "SEC EDGAR": "bg-rose-500/15 text-rose-400 border-rose-500/20",
    Census: "bg-cyan-500/15 text-cyan-400 border-cyan-500/20",
    NBER: "bg-orange-500/15 text-orange-400 border-orange-500/20",
  };
  return (
    <Badge
      variant="outline"
      className={colors[source] ?? "bg-muted text-muted-foreground"}
    >
      {source}
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// Tab: Overview
// ---------------------------------------------------------------------------
function OverviewTab() {
  return (
    <div className="space-y-6">
      <SectionCard title="What is ECPM?">
        <Prose>
          <p>
            The <strong>Economic Crisis Prediction Model</strong> (ECPM) is a
            quantitative research platform that operationalises classical
            Marxist political economy with modern econometric methods. It
            translates the US National Income and Product Accounts (NIPA) into
            Marxian value categories&mdash;constant capital, variable capital,
            and surplus value&mdash;to compute time-series of key profitability
            and financial-fragility indicators from 1947 to the present.
          </p>
          <p>
            These indicators are then synthesised into a <strong>Composite
            Crisis Probability Index</strong> and fed into a Vector Error
            Correction Model (VECM) for multi-step-ahead forecasting. A
            separate structural analysis module uses Leontief input-output
            matrices to map inter-industry shock propagation, and a
            concentration module tracks monopolisation trends using SEC EDGAR
            and Census Bureau data.
          </p>
        </Prose>
      </SectionCard>

      <SectionCard title="Theoretical Foundations">
        <Prose>
          <p>
            ECPM rests on three interlocking crisis mechanisms derived from
            Marx&apos;s critique of political economy:
          </p>
        </Prose>
        <div className="grid gap-4 md:grid-cols-3">
          {[
            {
              name: "Tendency of the Rate of Profit to Fall (TRPF)",
              desc: "As capital accumulates, the organic composition of capital (C/V) rises faster than the rate of exploitation (S/V), compressing the general rate of profit r = S/(C+V). Falling profitability undermines investment incentives and triggers periodic crises of overaccumulation.",
              indicators: ["Rate of Profit", "OCC", "Rate of Surplus Value", "Mass of Profit"],
            },
            {
              name: "Realization Crisis",
              desc: "When productivity gains outstrip wage growth, aggregate demand cannot absorb the value produced. The widening gap between what workers produce and what they receive in compensation creates conditions for demand-deficiency crises.",
              indicators: ["Productivity-Wage Gap"],
            },
            {
              name: "Financial Fragility",
              desc: "Falling profit rates in the real economy push capital into financial speculation (fictitious capital). Credit bubbles, rising corporate leverage, and financialisation create fragility that amplifies underlying profitability crises.",
              indicators: ["Credit-to-GDP Gap", "Financial-to-Real Asset Ratio", "Debt Service Ratio"],
            },
          ].map((m) => (
            <div
              key={m.name}
              className="rounded-lg border border-border bg-muted/30 p-4 space-y-2"
            >
              <h4 className="text-sm font-semibold">{m.name}</h4>
              <p className="text-xs text-foreground/70 leading-relaxed">
                {m.desc}
              </p>
              <div className="flex flex-wrap gap-1 pt-1">
                {m.indicators.map((i) => (
                  <Badge key={i} variant="secondary" className="text-[10px]">
                    {i}
                  </Badge>
                ))}
              </div>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard title="Dual Methodology Approach">
        <Prose>
          <p>
            The four core indicators (rate of profit, organic composition,
            rate of surplus value, mass of profit) are computed under two
            independent methodologies. This dual-methodology design guards
            against results that are artefacts of a single accounting
            convention:
          </p>
        </Prose>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-border bg-muted/30 p-4 space-y-2">
            <h4 className="text-sm font-semibold">
              Shaikh &amp; Tonak (1994)
            </h4>
            <p className="text-xs text-foreground/70 leading-relaxed">
              Follows the framework in{" "}
              <em>Measuring the Wealth of Nations</em>. Surplus value is
              derived as national income minus employee compensation.
              Constant capital uses the current-cost net stock of fixed
              assets. Variable capital equals total employee compensation.
              This approach adheres to a simultaneous valuation framework.
            </p>
            <p className="text-[10px] text-muted-foreground">
              Shaikh, A. &amp; Tonak, E.A. (1994). <em>Measuring the Wealth
              of Nations</em>. Cambridge University Press.
            </p>
          </div>
          <div className="rounded-lg border border-border bg-muted/30 p-4 space-y-2">
            <h4 className="text-sm font-semibold">
              Kliman TSSI (2012)
            </h4>
            <p className="text-xs text-foreground/70 leading-relaxed">
              Follows the Temporal Single-System Interpretation outlined in{" "}
              <em>The Failure of Capitalist Production</em>. Uses
              historical-cost net stock for constant capital to preserve the
              temporal dimension of value. This captures how capital advanced
              at one period&apos;s prices generates surplus realised at
              another period&apos;s prices, consistent with Marx&apos;s
              distinction between value and price of production.
            </p>
            <p className="text-[10px] text-muted-foreground">
              Kliman, A. (2012). <em>The Failure of Capitalist Production</em>.
              Pluto Press.
            </p>
          </div>
        </div>
      </SectionCard>

      <SectionCard title="Data Sources">
        <Prose>
          <p>
            ECPM draws from five principal US federal statistical agencies
            and regulatory bodies:
          </p>
        </Prose>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {[
            {
              source: "FRED",
              full: "Federal Reserve Economic Data",
              desc: "Macroeconomic time series: GDP, compensation, labour productivity, corporate income, interest payments. Quarterly and monthly frequencies.",
            },
            {
              source: "BEA",
              full: "Bureau of Economic Analysis",
              desc: "NIPA tables (national income, corporate profits) and Fixed Assets tables (current-cost and historical-cost net stock of private fixed assets).",
            },
            {
              source: "Fed Z.1",
              full: "Financial Accounts of the United States",
              desc: "Flow of Funds data: nonfinancial corporate financial assets (TFAABSNNCB), corporate debt (BOGZ1FL073164003Q), interest payments.",
            },
            {
              source: "SEC EDGAR",
              full: "Securities and Exchange Commission",
              desc: "10-K annual filings for firm-level revenue extraction. Used to compute concentration ratios (CR4, CR8) and HHI by NAICS sector.",
            },
            {
              source: "Census",
              full: "US Census Bureau",
              desc: "Economic Census establishment counts and revenue totals by NAICS code. Provides benchmark concentration data every 5 years.",
            },
            {
              source: "NBER",
              full: "National Bureau of Economic Research",
              desc: "USREC recession indicator (binary monthly series). Used to construct the continuous crisis proximity target for supervised weight learning.",
            },
          ].map((s) => (
            <div
              key={s.source}
              className="rounded-lg border border-border bg-muted/30 p-3 space-y-1.5"
            >
              <div className="flex items-center gap-2">
                <SourceBadge source={s.source} />
                <span className="text-xs text-muted-foreground">{s.full}</span>
              </div>
              <p className="text-xs text-foreground/70 leading-relaxed">
                {s.desc}
              </p>
            </div>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab: Indicators
// ---------------------------------------------------------------------------
function IndicatorsTab() {
  return (
    <div className="space-y-6">
      <SectionCard title="Core Marxist Indicators">
        <Prose>
          <p>
            These four indicators derive directly from Marx&apos;s labour
            theory of value. They depend on the active methodology
            (Shaikh/Tonak or Kliman) because they require translating NIPA
            line items into the Marxian categories of constant capital (C),
            variable capital (V), and surplus value (S).
          </p>
        </Prose>

        <div className="space-y-4">
          <div className="rounded-lg border border-border p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold">Rate of Profit (r)</h4>
              <Badge variant="secondary">Core</Badge>
            </div>
            <FormulaBlock
              label="General rate of profit"
              latex="r = \frac{S}{C + V}"
            />
            <Prose>
              <p>
                The ratio of surplus value to total capital advanced
                (constant + variable). This is the central variable in
                Marx&apos;s theory of capitalist crisis. A tendential
                decline in <em>r</em> signals deteriorating conditions for
                capital accumulation.
              </p>
            </Prose>
            <DefinitionList
              items={[
                { term: "S (Surplus Value)", definition: "National income minus employee compensation. Shaikh/Tonak: BEA NIPA Table 1.12 Line 1 \u2212 FRED A576RC1 (units normalised from millions/billions). Kliman: FRED A053RC1Q027SBEA \u2212 A576RC1 (both billions USD). See per-methodology docs at /indicators/methodology." },
                { term: "C (Constant Capital)", definition: "Net stock of private fixed assets. Shaikh/Tonak: current-cost (K1PTOTL1ES000). Kliman: historical-cost (K1NTOTL1HI000, millions USD \u00f7 1000)." },
                { term: "V (Variable Capital)", definition: "Total employee compensation (FRED A576RC1)" },
              ]}
            />
          </div>

          <div className="rounded-lg border border-border p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold">
                Organic Composition of Capital (OCC)
              </h4>
              <Badge variant="secondary">Core</Badge>
            </div>
            <FormulaBlock
              label="Organic composition"
              latex="OCC = \frac{C}{V}"
            />
            <Prose>
              <p>
                The ratio of constant capital to variable capital, reflecting
                the technical composition of production. A rising OCC
                indicates mechanisation and labour-displacing technological
                change&mdash;the underlying driver of the TRPF.
              </p>
              <p>
                Marx argued that competitive pressure forces capitalists to
                increase the OCC (invest in machinery over labour), which
                paradoxically reduces the source of surplus value, since
                only living labour creates new value.
              </p>
            </Prose>
          </div>

          <div className="rounded-lg border border-border p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold">
                Rate of Surplus Value (s&apos;)
              </h4>
              <Badge variant="secondary">Core</Badge>
            </div>
            <FormulaBlock
              label="Rate of exploitation"
              latex="s' = \frac{S}{V}"
            />
            <Prose>
              <p>
                Also called the rate of exploitation. Measures how much
                surplus value is extracted per unit of variable capital
                (labour cost). A rising s&apos; can temporarily
                counteract a falling rate of profit, but Marx argued this
                counter-tendency has limits (workers&apos; subsistence
                needs, class struggle).
              </p>
            </Prose>
          </div>

          <div className="rounded-lg border border-border p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold">Mass of Profit</h4>
              <Badge variant="secondary">Core</Badge>
            </div>
            <FormulaBlock
              label="Absolute surplus value"
              latex="M = S \quad \text{(nominal, billions USD)}"
            />
            <Prose>
              <p>
                The total volume of surplus value extracted in a period.
                Even when the <em>rate</em> of profit falls, the{" "}
                <em>mass</em> of profit can continue rising as the total
                capital advanced grows. Marx noted that accumulation
                continues as long as the mass of profit expands, and
                crisis is triggered when even the mass begins to
                stagnate or decline.
              </p>
            </Prose>
          </div>
        </div>
      </SectionCard>

      <SectionCard title="Financial Fragility Indicators">
        <Prose>
          <p>
            These four indicators are methodology-independent&mdash;they
            compute the same values regardless of which Marxist methodology
            is selected. They capture the financial dimensions of crisis
            dynamics: credit expansion, financialisation, and leverage.
          </p>
        </Prose>

        <div className="space-y-4">
          <div className="rounded-lg border border-border p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold">
                Productivity-Wage Gap
              </h4>
              <Badge variant="outline">Financial</Badge>
            </div>
            <FormulaBlock
              label="Gap index (base = 100)"
              latex="\text{Gap} = \frac{\text{Output/Hour Index}}{\text{Real Comp/Hour Index}} \times 100"
            />
            <Prose>
              <p>
                Both series are normalised to base 100 at the first
                observation, then a 20-period rolling mean is applied for
                smoothing. Values above 100 indicate productivity growing
                faster than real compensation&mdash;a widening gap that
                points toward realization crisis conditions.
              </p>
            </Prose>
            <DefinitionList
              items={[
                { term: "Output per Hour", definition: "FRED OPHNFB \u2014 Nonfarm business sector output per hour of all persons" },
                { term: "Real Compensation", definition: "FRED PRS85006092 \u2014 Real compensation per hour, nonfarm business" },
              ]}
            />
          </div>

          <div className="rounded-lg border border-border p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold">Credit-to-GDP Gap</h4>
              <Badge variant="outline">Financial</Badge>
            </div>
            <FormulaBlock
              label="BIS one-sided HP filter methodology"
              latex="\text{Gap}_t = \frac{\text{Credit}_t}{\text{GDP}_t} \times 100 - \text{HP}^{(\text{one-sided})}_{\lambda=400{,}000}\!\left(\frac{\text{Credit}_t}{\text{GDP}_t}\right)"
            />
            <Prose>
              <p>
                The credit-to-GDP gap follows the Bank for International
                Settlements (BIS) methodology. The one-sided
                Hodrick-Prescott filter with &lambda;=400,000 (appropriate
                for quarterly data) produces a backward-looking trend.
                Positive gap values signal excessive credit growth
                relative to the long-run trend&mdash;a leading indicator
                of banking crises per BIS research.
              </p>
              <p>
                The one-sided filter is implemented recursively:
              </p>
            </Prose>
            <FormulaBlock
              label="Recursive HP filter"
              latex="\tau_t = \frac{y_t + \lambda(2\tau_{t-1} - \tau_{t-2})}{1 + \lambda}"
            />
            <DefinitionList
              items={[
                { term: "Credit Total", definition: "FRED BOGZ1FL073164003Q \u2014 Nonfinancial corporate business debt securities and loans" },
                { term: "Nominal GDP", definition: "FRED GDP \u2014 Gross Domestic Product (billions)" },
              ]}
            />
          </div>

          <div className="rounded-lg border border-border p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold">
                Financial-to-Real Asset Ratio
              </h4>
              <Badge variant="outline">Financial</Badge>
            </div>
            <FormulaBlock
              label="Financialisation ratio"
              latex="\text{Ratio} = \frac{\text{Total Financial Assets (NFC)}}{\text{Current-Cost Net Fixed Assets}}"
            />
            <Prose>
              <p>
                Measures the degree of financialisation in the nonfinancial
                corporate sector. Rising values indicate a growing share of
                corporate wealth held as financial instruments (stocks,
                bonds, derivatives) rather than real means of production
                (plant, equipment, structures).
              </p>
              <p>
                In Marxist terms, this captures the growth of{" "}
                <em>fictitious capital</em>&mdash;claims on future value
                that can decouple from actual value production and amplify
                crisis dynamics.
              </p>
              <p>
                Annual real-asset data is aligned to the quarterly
                financial-asset index using Last Observation Carried
                Forward (LOCF).
              </p>
            </Prose>
            <DefinitionList
              items={[
                { term: "Financial Assets", definition: "FRED TFAABSNNCB \u2014 Nonfinancial corporate business total financial assets (from Fed Z.1 B.103)" },
                { term: "Real Assets", definition: "FRED K1PTOTL1ES000 \u2014 Current-cost net stock of private fixed assets" },
              ]}
            />
          </div>

          <div className="rounded-lg border border-border p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold">
                Corporate Debt Service Ratio
              </h4>
              <Badge variant="outline">Financial</Badge>
            </div>
            <FormulaBlock
              label="Debt service burden"
              latex="\text{DSR} = \frac{\text{Interest Payments}}{\text{Corporate Profits (Pre-Tax)}} \times 100"
            />
            <Prose>
              <p>
                Corporate debt service payments as a share of pre-tax
                profits. High values indicate financial fragility:
                firms are dedicating a larger proportion of their income
                to servicing debt, leaving less for investment or crisis
                buffers. This makes the corporate sector vulnerable to
                interest rate shocks and profit squeezes.
              </p>
            </Prose>
            <DefinitionList
              items={[
                { term: "Debt Service", definition: "FRED BOGZ1FU106130001Q \u2014 Nonfinancial corporate business interest payments" },
                { term: "Corporate Income", definition: "FRED A445RC1Q027SBEA \u2014 Corporate profits before tax" },
              ]}
            />
          </div>
        </div>
      </SectionCard>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab: Crisis Index
// ---------------------------------------------------------------------------
function CrisisIndexTab() {
  return (
    <div className="space-y-6">
      <SectionCard title="Composite Crisis Probability Index">
        <Prose>
          <p>
            The Composite Crisis Index synthesises all eight indicators into
            a single 0&ndash;100 score representing the probability of
            economic crisis. It aggregates three mechanism-level
            sub-indices, each capturing a distinct crisis pathway from
            Marxist theory.
          </p>
        </Prose>
      </SectionCard>

      <SectionCard title="Sub-Index Construction">
        <Prose>
          <p>
            Each indicator is first normalised to [0, 1] via global
            percentile rank across the entire historical sample. For
            indicators where <em>lower</em> values signal higher crisis
            risk (rate of profit, rate of surplus value), the normalised
            score is inverted (1 &minus; rank). The mechanism sub-index
            is the arithmetic mean of its constituent normalised
            indicators:
          </p>
        </Prose>
        <FormulaBlock
          label="Sub-index construction"
          latex="\text{Sub}_{m} = \frac{1}{|I_m|} \sum_{i \in I_m} \tilde{x}_{i,t}"
        />
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border border-border p-3 space-y-2">
            <h4 className="text-xs font-semibold">TRPF Sub-Index</h4>
            <p className="text-xs text-foreground/70">
              Inverted rate of profit + OCC + inverted rate of surplus
              value + mass of profit
            </p>
          </div>
          <div className="rounded-lg border border-border p-3 space-y-2">
            <h4 className="text-xs font-semibold">Realization Sub-Index</h4>
            <p className="text-xs text-foreground/70">
              Productivity-wage gap
            </p>
          </div>
          <div className="rounded-lg border border-border p-3 space-y-2">
            <h4 className="text-xs font-semibold">Financial Sub-Index</h4>
            <p className="text-xs text-foreground/70">
              Credit-to-GDP gap + financial-to-real ratio + debt service
              ratio
            </p>
          </div>
        </div>
      </SectionCard>

      <SectionCard title="Weight Learning via Logistic Regression">
        <Prose>
          <p>
            When a crisis proximity target is available (built from NBER
            USREC data), ECPM learns mechanism weights via L2-regularised
            logistic regression rather than assuming equal weights.
          </p>
        </Prose>
        <FormulaBlock
          label="Binary target from continuous proximity"
          latex="y_t = \mathbb{1}\left[\text{target}(t) \geq 0.25\right]"
        />
        <Prose>
          <p>
            The three sub-indices serve as features. Coefficients are
            standardised (StandardScaler) before fitting. The logistic
            model uses balanced class weights to handle the low base rate
            of recessions. Final mechanism weights are the normalised
            absolute coefficient magnitudes:
          </p>
        </Prose>
        <FormulaBlock
          label="Weight normalisation"
          latex="w_m = \frac{|\beta_m|}{\sum_{k} |\beta_k|}"
        />
        <Prose>
          <p>
            Model quality is assessed via 5-fold cross-validated ROC-AUC.
            When fewer than 30 training observations are available, the
            model falls back to equal 1/3 weights per mechanism.
          </p>
        </Prose>
      </SectionCard>

      <SectionCard title="Crisis Proximity Target">
        <Prose>
          <p>
            The NBER&apos;s binary USREC indicator (1 = recession month)
            is transformed into a continuous 0&ndash;1 target measuring
            proximity to recession:
          </p>
        </Prose>
        <FormulaBlock
          label="12-month forward-looking window"
          latex="\text{target}(t) = \frac{1}{12} \sum_{k=1}^{12} \text{USREC}_{t+k}"
        />
        <Prose>
          <p>
            This yields approximately 800 continuous training observations
            rather than just 14 binary crisis labels, making supervised
            learning viable. A value of 0.5 means half of the next 12
            months are in recession; 0.0 means the economy is in a deep
            expansion phase.
          </p>
        </Prose>
      </SectionCard>

      <SectionCard title="Final Composite Score">
        <FormulaBlock
          label="Weighted composite"
          latex="\text{CPI}_t = 100 \times \sum_{m} w_m \cdot \text{Sub}_{m,t}"
        />
        <Prose>
          <p>
            The composite ranges from 0 (all indicators at historical
            lows of crisis risk) to 100 (all indicators at historical
            highs of crisis risk). The history panel on the Forecasting
            page shows this index over time alongside NBER recession
            shading.
          </p>
        </Prose>
      </SectionCard>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab: Forecasting
// ---------------------------------------------------------------------------
function ForecastingTab() {
  return (
    <div className="space-y-6">
      <SectionCard title="Vector Error Correction Model (VECM)">
        <Prose>
          <p>
            ECPM uses a VECM for multi-step-ahead forecasting of all
            indicator time series simultaneously. The VECM was chosen over
            a standard VAR because economic indicators exhibit
            cointegration&mdash;long-run equilibrium relationships that a
            VAR in differences would discard, and a VAR in levels would
            produce spurious results for.
          </p>
          <p>
            The VECM preserves both short-run dynamics and long-run level
            relationships via an error-correction term that pulls variables
            back toward their cointegrating relationships:
          </p>
        </Prose>
        <FormulaBlock
          label="VECM representation"
          latex="\Delta \mathbf{y}_t = \alpha \beta' \mathbf{y}_{t-1} + \sum_{i=1}^{p-1} \Gamma_i \Delta \mathbf{y}_{t-i} + \mu + \varepsilon_t"
        />
        <DefinitionList
          items={[
            { term: "\u03B1 (alpha)", definition: "Loading matrix \u2014 speed of adjustment to long-run equilibrium" },
            { term: "\u03B2 (beta)", definition: "Cointegrating vectors \u2014 defines the long-run relationships" },
            { term: "\u0393 (Gamma)", definition: "Short-run dynamics matrices for lagged differences" },
            { term: "\u03BC (mu)", definition: "Deterministic constant (restricted to cointegrating space)" },
            { term: "\u03B5 (epsilon)", definition: "White noise innovation vector" },
          ]}
        />
      </SectionCard>

      <SectionCard title="Johansen Cointegration Test">
        <Prose>
          <p>
            Before fitting the VECM, the cointegration rank is determined
            via the Johansen trace test. This tests how many independent
            cointegrating vectors exist among the indicator variables:
          </p>
        </Prose>
        <FormulaBlock
          label="Johansen trace statistic"
          latex="\lambda_{\text{trace}}(r) = -T \sum_{i=r+1}^{n} \ln(1 - \hat{\lambda}_i)"
        />
        <Prose>
          <p>
            The test proceeds sequentially: starting from rank 0, if the
            trace statistic exceeds the critical value at the 5%
            significance level, rank is incremented. If rank 0 is not
            rejected (no cointegration detected), the model falls back to
            rank 1 to preserve level dynamics.
          </p>
          <p>
            Data is resampled to quarterly frequency before fitting to
            avoid artificial variance suppression from forward-filling
            annual/quarterly source data to monthly. The lag order is kept
            at max 2 (in quarters) to avoid over-parameterisation.
          </p>
        </Prose>
      </SectionCard>

      <SectionCard title="Confidence Intervals: Recursive Residual Bootstrap">
        <Prose>
          <p>
            Forecast uncertainty is quantified via recursive residual
            bootstrap (1,000 replications). At each iteration:
          </p>
          <ol className="list-decimal pl-5 space-y-1 text-sm">
            <li>
              Random historical residuals are drawn (with replacement) for
              each forecast step.
            </li>
            <li>
              The VECM is simulated forward recursively&mdash;shocks at
              step <em>t</em> feed back into steps <em>t+1, t+2, ...</em>{" "}
              through the error-correction and lag structure.
            </li>
            <li>
              Cumulative deviation from the deterministic path captures
              how shocks compound, producing confidence intervals that
              widen realistically over long horizons.
            </li>
          </ol>
          <p>
            Two confidence bands are reported:
          </p>
        </Prose>
        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-lg border border-border p-3">
            <h4 className="text-xs font-semibold">68% Band</h4>
            <p className="text-xs text-foreground/70">
              16th&ndash;84th percentile of bootstrap paths. Roughly
              equivalent to &plusmn;1 standard deviation.
            </p>
          </div>
          <div className="rounded-lg border border-border p-3">
            <h4 className="text-xs font-semibold">95% Band</h4>
            <p className="text-xs text-foreground/70">
              2.5th&ndash;97.5th percentile. Captures tail scenarios
              including crisis-scale deviations.
            </p>
          </div>
        </div>
      </SectionCard>

      <SectionCard title="Historical Backtesting">
        <Prose>
          <p>
            The Composite Crisis Index is backtested against 14 historical
            crisis episodes (1929&ndash;2023). For each episode, the
            model evaluates:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-sm">
            <li>
              <strong>12-month early warning:</strong> Whether the composite
              index exceeded its 75th historical percentile at any point in
              the 12 months before the crisis start.
            </li>
            <li>
              <strong>24-month early warning:</strong> Same check over a
              24-month pre-crisis window.
            </li>
            <li>
              <strong>Peak value &amp; date:</strong> Maximum crisis index
              reading during the episode and when it occurred.
            </li>
          </ul>
          <p>
            This provides an honest assessment of the model&apos;s
            retrospective predictive power across different types of
            economic crises (demand-driven, financial, supply-shock, etc.).
          </p>
        </Prose>
      </SectionCard>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab: Structural Analysis
// ---------------------------------------------------------------------------
function StructuralTab() {
  return (
    <div className="space-y-6">
      <SectionCard title="Leontief Input-Output Model">
        <Prose>
          <p>
            The Structural Analysis module uses Wassily Leontief&apos;s
            input-output framework to model inter-industry dependencies in
            the US economy. The BEA&apos;s Make-Use tables are transformed
            into a direct requirements matrix <strong>A</strong>, from
            which the Leontief inverse is computed:
          </p>
        </Prose>
        <FormulaBlock
          label="Leontief inverse matrix"
          latex="\mathbf{L} = (\mathbf{I} - \mathbf{A})^{-1}"
        />
        <Prose>
          <p>
            Each element L<sub>ij</sub> represents the total output
            required from sector <em>i</em> (both directly and
            indirectly) to deliver one unit of final demand for sector{" "}
            <em>j</em>. This captures the full supply-chain multiplier
            effect.
          </p>
        </Prose>
      </SectionCard>

      <SectionCard title="Shock Propagation Simulation">
        <Prose>
          <p>
            Given a demand shock of magnitude <em>d</em> to sector{" "}
            <em>j</em>, the economy-wide impact is computed as:
          </p>
        </Prose>
        <FormulaBlock
          label="Single-sector shock"
          latex="\Delta \mathbf{x} = \mathbf{L} \cdot \mathbf{d}, \quad d_k = \begin{cases} d & k = j \\ 0 & k \neq j \end{cases}"
        />
        <Prose>
          <p>
            Multi-sector shocks use superposition (the combined impact
            is the sum of individual shock impacts through the Leontief
            inverse). The simulator ranks all sectors by absolute impact
            and computes the total economy-wide output change.
          </p>
        </Prose>
      </SectionCard>

      <SectionCard title="Backward & Forward Linkages">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-border p-4 space-y-2">
            <h4 className="text-sm font-semibold">Backward Linkage</h4>
            <FormulaBlock
              label="Column sum of L"
              latex="BL_j = \sum_{i=1}^{n} L_{ij}"
            />
            <p className="text-xs text-foreground/70">
              How much sector <em>j</em> pulls from other sectors when
              its final demand increases. High backward linkage means the
              sector has extensive supply-chain dependencies.
            </p>
          </div>
          <div className="rounded-lg border border-border p-4 space-y-2">
            <h4 className="text-sm font-semibold">Forward Linkage</h4>
            <FormulaBlock
              label="Row sum of L"
              latex="FL_i = \sum_{j=1}^{n} L_{ij}"
            />
            <p className="text-xs text-foreground/70">
              How much sector <em>i</em> pushes to other sectors when
              economy-wide demand increases. High forward linkage means
              the sector is a key supplier to many industries.
            </p>
          </div>
        </div>
      </SectionCard>

      <SectionCard title="Critical Sector Identification">
        <Prose>
          <p>
            A sector is flagged as &quot;critical&quot; if its output
            multiplier (column sum of <strong>L</strong>) exceeds
            (1 + &theta;) times the average multiplier, where &theta;
            defaults to 10%. These are the sectors whose disruption would
            cascade most widely through the production network.
          </p>
        </Prose>
        <FormulaBlock
          label="Critical threshold"
          latex="\text{Critical}_j = \mathbb{1}\left[BL_j > (1 + \theta) \cdot \overline{BL}\right]"
        />
        <Prose>
          <p>
            The &quot;weakest link&quot; analysis identifies the single
            sector with the highest output multiplier, along with its
            dependency count: the number of sectors whose Leontief
            inverse column entry exceeds 0.01 (i.e., sectors for which
            a unit increase in the weakest sector&apos;s final demand
            generates at least 1% of a unit of additional output). This
            highlights systemic vulnerabilities in the production
            structure.
          </p>
        </Prose>
      </SectionCard>

      <SectionCard title="Reproduction Schema Visualisation">
        <Prose>
          <p>
            The Sankey diagram on the Structural Analysis page visualises
            the flow of value through the production structure, drawing
            on Marx&apos;s reproduction schemas from Volume II of{" "}
            <em>Capital</em>. The two departments:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-sm">
            <li>
              <strong>Department I</strong> &mdash; Production of means of
              production (mining, manufacturing, heavy industry)
            </li>
            <li>
              <strong>Department II</strong> &mdash; Production of means of
              consumption (consumer goods, services, retail)
            </li>
          </ul>
          <p>
            The flows between departments must satisfy specific
            proportionality conditions for balanced reproduction.
            Imbalances (Department I growing disproportionately) signal
            overaccumulation tendencies.
          </p>
        </Prose>
      </SectionCard>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab: Concentration
// ---------------------------------------------------------------------------
function ConcentrationTab() {
  return (
    <div className="space-y-6">
      <SectionCard title="Market Concentration Analysis">
        <Prose>
          <p>
            The Concentration module tracks monopolisation and market
            power trends across US industries using three standard
            industrial organisation metrics. In Marxist theory,
            increasing concentration reflects the inherent tendency
            toward centralisation of capital&mdash;competitive dynamics
            drive capital into fewer, larger firms.
          </p>
        </Prose>
      </SectionCard>

      <SectionCard title="Concentration Metrics">
        <div className="space-y-4">
          <div className="rounded-lg border border-border p-4 space-y-3">
            <h4 className="text-sm font-semibold">
              Concentration Ratio (CR4, CR8)
            </h4>
            <FormulaBlock
              label="Top-k concentration ratio"
              latex="CR_k = \sum_{i=1}^{k} s_i"
            />
            <Prose>
              <p>
                The sum of market shares of the top <em>k</em> firms. CR4
                captures the four largest firms; CR8 the eight largest.
                Values range from 0% (perfect competition) to 100%
                (monopoly/oligopoly). The US Department of Justice considers
                CR4 above 60% as indicating high concentration.
              </p>
            </Prose>
          </div>

          <div className="rounded-lg border border-border p-4 space-y-3">
            <h4 className="text-sm font-semibold">
              Herfindahl-Hirschman Index (HHI)
            </h4>
            <FormulaBlock
              label="Sum of squared market shares"
              latex="HHI = \sum_{i=1}^{N} s_i^2 \times 10{,}000"
            />
            <Prose>
              <p>
                The sum of squared market shares of all firms, scaled to
                0&ndash;10,000. Unlike CR ratios, HHI accounts for the
                distribution of market shares across <em>all</em> firms,
                not just the top few. Federal merger guidelines classify:
              </p>
              <ul className="list-disc pl-5 space-y-1">
                <li>&lt;1,500: Unconcentrated</li>
                <li>1,500&ndash;2,500: Moderately concentrated</li>
                <li>&gt;2,500: Highly concentrated</li>
              </ul>
            </Prose>
          </div>
        </div>
      </SectionCard>

      <SectionCard title="Data Sources & Methodology">
        <Prose>
          <p>
            Concentration data is assembled from multiple sources with a
            tiered priority system:
          </p>
          <ol className="list-decimal pl-5 space-y-2 text-sm">
            <li>
              <strong>SEC EDGAR 10-K filings</strong> (highest quality):
              Firm-level annual revenue data extracted from financial
              statements filed with the SEC. Provides the most granular
              and recent data for publicly traded firms. Each firm is
              mapped to NAICS codes via SIC-NAICS concordance tables.
            </li>
            <li>
              <strong>Census Bureau Economic Census</strong> (benchmark):
              Published every 5 years, provides comprehensive
              establishment-level revenue and employment totals by NAICS
              code. Covers the full economy including private firms.
            </li>
            <li>
              <strong>Estimated</strong> (fallback): When neither EDGAR
              nor Census data is available, concentration is estimated
              from establishment count distributions and industry-level
              revenue data.
            </li>
          </ol>
          <p>
            The <code>data_source</code> field on each concentration
            record identifies which tier produced the estimate, enabling
            users to assess confidence in the data.
          </p>
        </Prose>
      </SectionCard>

      <SectionCard title="Trend Analysis">
        <Prose>
          <p>
            Concentration trends are computed via linear regression of CR4
            values over time. The trend slope (CR4 percentage-point change
            per year) classifies each industry using a &plusmn;0.5
            threshold to suppress noise:
          </p>
        </Prose>
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-lg border border-border p-3 text-center">
            <div className="text-lg font-bold text-emerald-400">&uarr;</div>
            <h4 className="text-xs font-semibold">Increasing</h4>
            <p className="text-[10px] text-muted-foreground">
              Slope &gt; +0.5 CR4 points/year
            </p>
          </div>
          <div className="rounded-lg border border-border p-3 text-center">
            <div className="text-lg font-bold text-zinc-400">&harr;</div>
            <h4 className="text-xs font-semibold">Stable</h4>
            <p className="text-[10px] text-muted-foreground">
              |Slope| &le; 0.5 CR4 points/year
            </p>
          </div>
          <div className="rounded-lg border border-border p-3 text-center">
            <div className="text-lg font-bold text-blue-400">&darr;</div>
            <h4 className="text-xs font-semibold">Decreasing</h4>
            <p className="text-[10px] text-muted-foreground">
              Slope &lt; &minus;0.5 CR4 points/year
            </p>
          </div>
        </div>
        <Prose>
          <p>
            R-squared values are provided to assess trend reliability.
            Industries with low R-squared may have volatile concentration
            levels that don&apos;t follow a clear directional trend.
          </p>
        </Prose>
      </SectionCard>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab: Data Verification
// ---------------------------------------------------------------------------
function DataVerificationTab() {
  return (
    <div className="space-y-6">
      <SectionCard title="Data Integrity Pipeline">
        <Prose>
          <p>
            ECPM implements a multi-stage data integrity pipeline from
            ingestion through computation. Every data point that enters
            the system is tracked, validated, and auditable.
          </p>
        </Prose>
      </SectionCard>

      <SectionCard title="Ingestion & Gap Detection">
        <Prose>
          <p>
            The ingestion pipeline fetches raw data from FRED and BEA APIs
            and stores it in PostgreSQL. Key integrity guarantees:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-sm">
            <li>
              <strong>No interpolation on ingestion:</strong> Missing values
              (NaN) are stored as NULL with <code>gap_flag=True</code>.
              Interpolation decisions are deferred to the computation
              layer so that raw data is always recoverable.
            </li>
            <li>
              <strong>Upsert semantics:</strong> ON CONFLICT handling
              ensures that re-running ingestion updates existing records
              rather than creating duplicates.
            </li>
            <li>
              <strong>Error isolation:</strong> Individual series failures
              do not abort the pipeline. Failed series are recorded with
              <code>fetch_status=&apos;error&apos;</code> and error messages
              for diagnosis.
            </li>
            <li>
              <strong>Metadata tracking:</strong> Each series has a metadata
              record with source, units, frequency, seasonal adjustment,
              last fetch time, observation count, and fetch status.
            </li>
          </ul>
        </Prose>
      </SectionCard>

      <SectionCard title="Frequency Alignment">
        <Prose>
          <p>
            ECPM data spans multiple frequencies (annual, quarterly,
            monthly). A single consistent strategy is used across all
            indicators:
          </p>
        </Prose>
        <div className="rounded-lg border border-border bg-muted/30 p-4 space-y-2">
          <h4 className="text-sm font-semibold">
            Last Observation Carried Forward (LOCF)
          </h4>
          <p className="text-xs text-foreground/70">
            All mixed-frequency inputs are aligned using LOCF. When
            annual data (e.g., fixed assets) needs to be combined with
            quarterly data, the most recent annual value is carried
            forward until the next annual observation. This avoids
            introducing artificial variation from interpolation while
            maintaining a continuous series for computation.
          </p>
        </div>
        <Prose>
          <p>
            For the VECM forecasting model, all data is resampled to
            quarterly frequency (taking the last value per quarter) to
            avoid variance suppression from forward-filling to monthly.
          </p>
        </Prose>
      </SectionCard>

      <SectionCard title="Unit Reconciliation">
        <Prose>
          <p>
            Different federal agencies report data in different units.
            ECPM performs explicit unit conversions during computation:
          </p>
        </Prose>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border">
                <th className="py-2 pr-4 text-left font-medium text-muted-foreground">Series</th>
                <th className="py-2 pr-4 text-left font-medium text-muted-foreground">Raw Units</th>
                <th className="py-2 pr-4 text-left font-medium text-muted-foreground">Conversion</th>
                <th className="py-2 text-left font-medium text-muted-foreground">Computed Units</th>
              </tr>
            </thead>
            <tbody className="text-foreground/80">
              <tr className="border-b border-border/50">
                <td className="py-2 pr-4">BEA National Income</td>
                <td className="py-2 pr-4">Millions USD</td>
                <td className="py-2 pr-4">None (matched)</td>
                <td className="py-2">Millions USD</td>
              </tr>
              <tr className="border-b border-border/50">
                <td className="py-2 pr-4">FRED Compensation (A576RC1)</td>
                <td className="py-2 pr-4">Billions USD</td>
                <td className="py-2 pr-4">&times; 1000</td>
                <td className="py-2">Millions USD</td>
              </tr>
              <tr className="border-b border-border/50">
                <td className="py-2 pr-4">Credit Total (BOGZ1FL...)</td>
                <td className="py-2 pr-4">Millions USD</td>
                <td className="py-2 pr-4">&divide; 1000</td>
                <td className="py-2">Billions USD</td>
              </tr>
              <tr className="border-b border-border/50">
                <td className="py-2 pr-4">Debt Service (BOGZ1FU...)</td>
                <td className="py-2 pr-4">Millions USD</td>
                <td className="py-2 pr-4">&divide; 1000</td>
                <td className="py-2">Billions USD</td>
              </tr>
              <tr>
                <td className="py-2 pr-4">GDP</td>
                <td className="py-2 pr-4">Billions USD</td>
                <td className="py-2 pr-4">None</td>
                <td className="py-2">Billions USD</td>
              </tr>
            </tbody>
          </table>
        </div>
      </SectionCard>

      <SectionCard title="Caching & Freshness">
        <Prose>
          <p>
            ECPM uses a two-layer caching strategy to balance fast
            responses with data freshness:
          </p>
        </Prose>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-border bg-muted/30 p-4 space-y-2">
            <h4 className="text-sm font-semibold">Disk Cache (Primary)</h4>
            <p className="text-xs text-foreground/70 leading-relaxed">
              The indicator overview and per-indicator detail endpoints store
              computed results as JSON files on disk under{" "}
              <code>/app/cache/indicators/&#123;methodology&#125;/</code> with
              a <strong>24-hour TTL</strong>. Each methodology has its own
              directory, preventing cross-contamination between Shaikh/Tonak
              and Kliman results.
            </p>
          </div>
          <div className="rounded-lg border border-border bg-muted/30 p-4 space-y-2">
            <h4 className="text-sm font-semibold">Redis (Secondary)</h4>
            <p className="text-xs text-foreground/70 leading-relaxed">
              The methodology documentation listing, compare endpoint, and
              forecasting results use Redis. Cache keys follow the pattern{" "}
              <code>ecpm:api:&#123;endpoint&#125;:&#123;hash&#125;</code>.
              Data endpoints use a <strong>1-hour TTL</strong>; methodology
              docs use a <strong>24-hour TTL</strong>. Redis also serves as
              the Celery broker and training progress pub/sub channel.
            </p>
          </div>
        </div>
        <Prose>
          <p>
            This two-tier approach ensures sub-10ms cache hits for the most
            common requests (overview and detail) while keeping
            aggregate/comparison queries fresh via Redis.
          </p>
        </Prose>
      </SectionCard>

      <SectionCard title="Input Validation">
        <Prose>
          <p>
            All user-supplied parameters are validated before reaching
            the database or computation layer:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-sm">
            <li>
              <strong>Series IDs:</strong> Must match{" "}
              <code>[A-Za-z0-9_-]&#123;1,64&#125;</code>
            </li>
            <li>
              <strong>NAICS codes:</strong> Must be 2&ndash;6 digits
            </li>
            <li>
              <strong>Search queries:</strong> Limited to 200 characters
              of safe characters (alphanumeric, spaces, basic punctuation)
            </li>
            <li>
              <strong>Pagination:</strong> Limit clamped to [1, 1000],
              offset clamped to [0, &infin;)
            </li>
          </ul>
          <p>
            This prevents SQL injection, parameter overflow, and
            unexpected query patterns from reaching internal systems.
          </p>
        </Prose>
      </SectionCard>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab: References
// ---------------------------------------------------------------------------
function ReferencesTab() {
  return (
    <div className="space-y-6">
      <SectionCard title="Primary Theoretical Sources">
        <div className="space-y-3">
          {[
            {
              authors: "Marx, K.",
              year: "1867/1885/1894",
              title: "Capital: A Critique of Political Economy, Volumes I\u2013III",
              publisher: "Various editions",
              note: "Foundational theory of surplus value, rate of profit, organic composition, and reproduction schemas.",
            },
            {
              authors: "Shaikh, A. & Tonak, E.A.",
              year: "1994",
              title: "Measuring the Wealth of Nations: The Political Economy of National Accounts",
              publisher: "Cambridge University Press",
              note: "Methodology for translating NIPA data into Marxian value categories. ECPM\u2019s \u201cShaikh/Tonak\u201d methodology implementation follows this text.",
            },
            {
              authors: "Kliman, A.",
              year: "2012",
              title: "The Failure of Capitalist Production: Underlying Causes of the Great Recession",
              publisher: "Pluto Press",
              note: "Temporal Single-System Interpretation (TSSI) of Marx\u2019s value theory. ECPM\u2019s \u201cKliman\u201d methodology uses historical-cost capital stock per this framework.",
            },
            {
              authors: "Shaikh, A.",
              year: "2016",
              title: "Capitalism: Competition, Conflict, Crises",
              publisher: "Oxford University Press",
              note: "Comprehensive modern treatment of classical/Marxist political economy with empirical applications.",
            },
          ].map((ref) => (
            <div
              key={ref.title}
              className="border-l-2 border-primary/40 pl-3 space-y-0.5"
            >
              <p className="text-sm font-medium">
                {ref.authors} ({ref.year})
              </p>
              <p className="text-sm italic text-foreground/80">{ref.title}</p>
              <p className="text-xs text-muted-foreground">{ref.publisher}</p>
              <p className="text-xs text-foreground/60">{ref.note}</p>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard title="Econometric & Statistical Methods">
        <div className="space-y-3">
          {[
            {
              authors: "Johansen, S.",
              year: "1991",
              title: "Estimation and Hypothesis Testing of Cointegration Vectors in Gaussian Vector Autoregressive Models",
              publisher: "Econometrica, 59(6), 1551\u20131580",
              note: "Theoretical basis for the Johansen cointegration test used to determine VECM rank.",
            },
            {
              authors: "L\u00FCtkepohl, H.",
              year: "2005",
              title: "New Introduction to Multiple Time Series Analysis",
              publisher: "Springer",
              note: "Reference for VECM specification, estimation, and forecasting methodology.",
            },
            {
              authors: "Drehmann, M. & Tsatsaronis, K.",
              year: "2014",
              title: "The Credit-to-GDP Gap and Countercyclical Capital Buffers",
              publisher: "BIS Quarterly Review, March 2014",
              note: "BIS methodology for the one-sided HP filter credit-to-GDP gap (\u03BB=400,000 for quarterly data).",
            },
            {
              authors: "Leontief, W.",
              year: "1986",
              title: "Input-Output Economics (2nd edition)",
              publisher: "Oxford University Press",
              note: "Foundation for the input-output structural analysis module, Leontief inverse, and linkage computations.",
            },
          ].map((ref) => (
            <div
              key={ref.title}
              className="border-l-2 border-blue-500/40 pl-3 space-y-0.5"
            >
              <p className="text-sm font-medium">
                {ref.authors} ({ref.year})
              </p>
              <p className="text-sm italic text-foreground/80">{ref.title}</p>
              <p className="text-xs text-muted-foreground">{ref.publisher}</p>
              <p className="text-xs text-foreground/60">{ref.note}</p>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard title="Data Sources">
        <div className="space-y-3">
          {[
            {
              name: "Federal Reserve Economic Data (FRED)",
              url: "https://fred.stlouisfed.org",
              desc: "Federal Reserve Bank of St. Louis. Macroeconomic time series including GDP, compensation, productivity, corporate financial flows.",
            },
            {
              name: "Bureau of Economic Analysis (BEA)",
              url: "https://www.bea.gov",
              desc: "NIPA tables (national income and product accounts) and Fixed Assets tables. Make-Use tables for input-output analysis.",
            },
            {
              name: "Financial Accounts (Z.1)",
              url: "https://www.federalreserve.gov/releases/z1/",
              desc: "Board of Governors of the Federal Reserve System. Balance sheet and flow of funds data for nonfinancial corporate business.",
            },
            {
              name: "SEC EDGAR",
              url: "https://www.sec.gov/edgar",
              desc: "10-K annual filings for publicly traded firms. Used for firm-level revenue data to compute concentration ratios.",
            },
            {
              name: "US Census Bureau",
              url: "https://www.census.gov/programs-surveys/economic-census.html",
              desc: "Economic Census (every 5 years). Comprehensive establishment-level data by NAICS code for concentration analysis.",
            },
            {
              name: "NBER Business Cycle Dating",
              url: "https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions",
              desc: "USREC recession indicator. Used to construct the continuous crisis proximity target for supervised weight learning.",
            },
          ].map((ds) => (
            <div
              key={ds.name}
              className="border-l-2 border-emerald-500/40 pl-3 space-y-0.5"
            >
              <p className="text-sm font-medium">{ds.name}</p>
              <p className="text-xs text-blue-400">{ds.url}</p>
              <p className="text-xs text-foreground/60">{ds.desc}</p>
            </div>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

const TABS = [
  { value: "overview", label: "Overview" },
  { value: "indicators", label: "Indicators" },
  { value: "crisis-index", label: "Crisis Index" },
  { value: "forecasting", label: "Forecasting" },
  { value: "structural", label: "Structural" },
  { value: "concentration", label: "Concentration" },
  { value: "verification", label: "Data Verification" },
  { value: "references", label: "References" },
] as const;

export default function MethodologyPage() {
  const [activeTab, setActiveTab] = useState("overview");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight">Methodology</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Mathematical foundations, economic theory, and data verification
          behind each module of the Economic Crisis Prediction Model.
        </p>
      </div>

      <Tabs defaultValue="overview" value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="flex flex-wrap h-auto gap-1 bg-muted/50 p-1">
          {TABS.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="overview">
          <OverviewTab />
        </TabsContent>
        <TabsContent value="indicators">
          <IndicatorsTab />
        </TabsContent>
        <TabsContent value="crisis-index">
          <CrisisIndexTab />
        </TabsContent>
        <TabsContent value="forecasting">
          <ForecastingTab />
        </TabsContent>
        <TabsContent value="structural">
          <StructuralTab />
        </TabsContent>
        <TabsContent value="concentration">
          <ConcentrationTab />
        </TabsContent>
        <TabsContent value="verification">
          <DataVerificationTab />
        </TabsContent>
        <TabsContent value="references">
          <ReferencesTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
