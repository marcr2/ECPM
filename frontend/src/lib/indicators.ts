/**
 * API client for indicator endpoints.
 *
 * Follows the same apiFetch pattern used in lib/api.ts.
 * All functions call /api/indicators/... endpoints served by the backend.
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ---------- Types ----------

export interface IndicatorDataPoint {
  date: string;
  value: number;
}

export interface IndicatorData {
  slug: string;
  name: string;
  units: string;
  methodology: string;
  frequency: string;
  data: IndicatorDataPoint[];
  latest_value: number | null;
  latest_date: string | null;
}

export interface IndicatorSummary {
  slug: string;
  name: string;
  units: string;
  latest_value: number | null;
  latest_date: string | null;
  trend: string | null;
  sparkline: number[];
}

export interface IndicatorOverview {
  methodology: string;
  indicators: IndicatorSummary[];
}

export interface NIPAMappingDoc {
  marx_category: string;
  nipa_table: string;
  nipa_line: number;
  nipa_description: string;
  operation: string;
  notes: string;
}

export interface IndicatorMethodologyDoc {
  indicator_slug: string;
  indicator_name: string;
  formula_latex: string;
  interpretation: string;
  mappings: NIPAMappingDoc[];
  citations: string[];
}

export interface MethodologyDocResponse {
  methodology_slug: string;
  methodology_name: string;
  indicators: IndicatorMethodologyDoc[];
}

// ---------- Internal fetch helper ----------

async function indicatorFetch<T>(
  path: string,
  params?: Record<string, string | undefined>
): Promise<T> {
  const url = new URL(path, API_BASE);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== "") {
        url.searchParams.set(key, value);
      }
    }
  }

  const res = await fetch(url.toString(), {
    headers: { Accept: "application/json" },
  });

  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }

  return res.json() as Promise<T>;
}

// ---------- Public API ----------

/**
 * Fetch overview of all indicators with latest values and sparkline data.
 */
export async function fetchIndicatorOverview(
  methodology?: string
): Promise<IndicatorOverview> {
  return indicatorFetch<IndicatorOverview>("/api/indicators/", {
    methodology,
  });
}

/**
 * Fetch time-series data for a single indicator.
 */
export async function fetchIndicatorData(
  slug: string,
  params?: { methodology?: string; start?: string; end?: string }
): Promise<IndicatorData> {
  return indicatorFetch<IndicatorData>(
    `/api/indicators/${encodeURIComponent(slug)}`,
    params as Record<string, string | undefined>
  );
}

/**
 * Fetch the same indicator computed under all methodologies for comparison.
 */
export async function fetchIndicatorComparison(
  slug: string
): Promise<{ methodologies: Record<string, IndicatorData> }> {
  return indicatorFetch<{ methodologies: Record<string, IndicatorData> }>(
    `/api/indicators/${encodeURIComponent(slug)}/compare`
  );
}

/**
 * Fetch methodology documentation (formulas, NIPA mappings, citations).
 * If methodologySlug is provided, returns docs for that methodology only.
 */
export async function fetchMethodologyDocs(
  methodologySlug?: string
): Promise<MethodologyDocResponse> {
  const path = methodologySlug
    ? `/api/indicators/methodology/${encodeURIComponent(methodologySlug)}`
    : "/api/indicators/methodology";
  return indicatorFetch<MethodologyDocResponse>(path);
}
