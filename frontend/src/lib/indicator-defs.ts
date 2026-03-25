export interface IndicatorDef {
  slug: string;
  name: string;
  units: string;
  category: "core" | "financial";
  description: string;
}

export const INDICATOR_DEFS: IndicatorDef[] = [
  {
    slug: "rate-of-profit",
    name: "Rate of Profit",
    units: "ratio",
    category: "core",
    description: "r = S / (C + V)",
  },
  {
    slug: "occ",
    name: "Organic Composition of Capital",
    units: "ratio",
    category: "core",
    description: "OCC = C / V",
  },
  {
    slug: "rate-of-surplus-value",
    name: "Rate of Surplus Value",
    units: "ratio",
    category: "core",
    description: "s' = S / V",
  },
  {
    slug: "mass-of-profit",
    name: "Mass of Profit",
    units: "billions USD",
    category: "core",
    description: "S (absolute surplus)",
  },
  {
    slug: "productivity-wage-gap",
    name: "Productivity-Wage Gap",
    units: "index",
    category: "financial",
    description: "Output/hour vs. real compensation",
  },
  {
    slug: "credit-gdp-gap",
    name: "Credit-to-GDP Gap",
    units: "pp",
    category: "financial",
    description: "Credit/GDP ratio minus HP trend",
  },
  {
    slug: "financial-real-ratio",
    name: "Financial-to-Real Asset Ratio",
    units: "ratio",
    category: "financial",
    description: "Total financial assets (Z.1 B.103) / tangible assets for nonfinancial corporate sector",
  },
  {
    slug: "debt-service-ratio",
    name: "Corporate Debt Service Ratio",
    units: "%",
    category: "financial",
    description: "Interest / operating surplus",
  },
];

/** Hero indicators (TRPF trio) for overview dashboard */
export const HERO_INDICATORS = INDICATOR_DEFS.filter((d) =>
  ["rate-of-profit", "occ", "rate-of-surplus-value"].includes(d.slug)
);

/** Secondary indicators for overview dashboard */
export const SECONDARY_INDICATORS = INDICATOR_DEFS.filter(
  (d) => !["rate-of-profit", "occ", "rate-of-surplus-value"].includes(d.slug)
);
