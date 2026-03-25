/**
 * TypeScript API client for concentration analysis endpoints.
 *
 * Mirrors Pydantic schemas from backend/ecpm/schemas/concentration.py.
 * Follows the pattern established in structural-api.ts with apiFetch helper.
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ---------- Types (mirror backend Pydantic schemas) ----------

export type DataSource = "edgar" | "census" | "estimated";

export interface IndustryListItem {
  naics: string;
  name: string;
  cr4: number;
  hhi: number;
  level: "monopoly" | "highly_concentrated" | "moderately_concentrated" | "competitive";
  trend_direction: "increasing" | "decreasing" | "stable";
  data_source?: DataSource | null;
}

export interface IndustriesResponse {
  industries: IndustryListItem[];
}

export interface ConcentrationDataPoint {
  year: number;
  cr4: number;
  cr8: number;
  hhi: number;
}

export interface TrendInfo {
  slope: number;
  direction: "increasing" | "decreasing" | "stable";
  r_squared: number;
}

export interface ConcentrationHistoryResponse {
  naics: string;
  name: string;
  data: ConcentrationDataPoint[];
  trend: TrendInfo;
}

export interface FirmInfo {
  rank: number;
  name: string;
  parent?: string | null;
  market_share: number;
  revenue?: number | null;
}

export interface FirmsResponse {
  naics: string;
  year: number;
  firms: FirmInfo[];
}

export interface CorrelationInfo {
  indicator_slug: string;
  indicator_name: string;
  correlation: number;
  confidence: number;
  lag_months: number;
  relationship: "positive" | "negative" | "none";
}

export interface CorrelationsResponse {
  naics: string;
  name: string;
  correlations: CorrelationInfo[];
}

export interface TopCorrelationItem {
  naics: string;
  industry: string;
  indicator_slug: string;
  indicator_name: string;
  correlation: number;
  confidence: number;
}

export interface TopCorrelationsResponse {
  correlations: TopCorrelationItem[];
}

export interface DeptConcentration {
  cr4: number;
  hhi: number;
  trend_direction: "increasing" | "decreasing" | "stable";
}

export interface OverviewResponse {
  dept_i: DeptConcentration;
  dept_ii: DeptConcentration;
  most_concentrated: IndustryListItem[];
  fastest_increasing: IndustryListItem[];
}

// ---------- API client helpers ----------

async function apiFetch<T>(
  path: string,
  params?: Record<string, string | number | undefined>,
  options?: RequestInit
): Promise<T> {
  const url = new URL(path, API_BASE);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }

  const res = await fetch(url.toString(), {
    headers: { Accept: "application/json" },
    ...options,
  });

  if (!res.ok) {
    let errorMessage = res.statusText;
    try {
      const errorJson = await res.json();
      errorMessage = errorJson.detail || errorMessage;
    } catch {
      // Ignore JSON parse errors, use statusText
    }
    throw new Error(`API error ${res.status}: ${errorMessage}`);
  }

  return res.json() as Promise<T>;
}

// ---------- Concentration API functions ----------

/**
 * Fetch list of industries with concentration metrics.
 * @param department - Optional filter: "I" or "II"
 */
export async function fetchIndustries(
  department?: "I" | "II"
): Promise<IndustriesResponse> {
  return apiFetch<IndustriesResponse>("/api/concentration/industries", {
    department,
  });
}

/**
 * Fetch concentration history for an industry.
 * @param naicsCode - NAICS industry code
 */
export async function fetchIndustryHistory(
  naicsCode: string
): Promise<ConcentrationHistoryResponse> {
  return apiFetch<ConcentrationHistoryResponse>(
    `/api/concentration/industry/${naicsCode}/history`
  );
}

/**
 * Fetch top firms by market share for an industry and year.
 * @param naicsCode - NAICS industry code
 * @param year - Data year
 */
export async function fetchFirms(
  naicsCode: string,
  year: number
): Promise<FirmsResponse> {
  return apiFetch<FirmsResponse>(
    `/api/concentration/industry/${naicsCode}/firms/${year}`
  );
}

/**
 * Fetch correlations between industry concentration and crisis indicators.
 * @param naicsCode - NAICS industry code
 * @param minConfidence - Minimum confidence threshold (default 50)
 */
export async function fetchCorrelations(
  naicsCode: string,
  minConfidence?: number
): Promise<CorrelationsResponse> {
  return apiFetch<CorrelationsResponse>(
    `/api/concentration/correlations/${naicsCode}`,
    { min_confidence: minConfidence }
  );
}

/**
 * Fetch top industry-indicator correlations by confidence.
 * @param minConfidence - Minimum confidence threshold (default 50)
 */
export async function fetchTopCorrelations(
  minConfidence?: number
): Promise<TopCorrelationsResponse> {
  return apiFetch<TopCorrelationsResponse>(
    "/api/concentration/top-correlations",
    { min_confidence: minConfidence }
  );
}

/**
 * Fetch concentration overview with department-level aggregations.
 */
export async function fetchOverview(): Promise<OverviewResponse> {
  return apiFetch<OverviewResponse>("/api/concentration/overview");
}
