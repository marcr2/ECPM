/**
 * TypeScript API client for structural analysis endpoints.
 *
 * Mirrors Pydantic schemas from backend/ecpm/schemas/structural.py.
 * Follows the pattern established in forecast-api.ts with apiFetch helper.
 */

import { getPublicApiBase } from "@/lib/public-api-base";

// ---------- Types (mirror backend Pydantic schemas) ----------

export interface YearsResponse {
  years: number[];
}

export interface MatrixResponse {
  year: number;
  matrix: number[][];
  row_labels: string[];
  col_labels: string[];
  matrix_type: string; // "coefficients", "inverse", "flows"
  diagnostics?: Record<string, unknown> | null;
  /** BEA description per row code when ingested; may be empty. */
  row_display_labels?: string[];
  /** BEA description per column code when ingested; may be empty. */
  col_display_labels?: string[];
}

export interface ShockRequest {
  year: number;
  shocks: Record<string, number>; // sector_code -> magnitude
  shock_type: "supply" | "demand";
}

export interface ShockImpact {
  sector: string;
  code: string;
  impact: number;
}

export interface ShockResultResponse {
  year: number;
  impacts: ShockImpact[];
  total_impact: number;
  shocked_sectors: string[];
}

export interface DepartmentValues {
  c: number; // Constant capital
  v: number; // Variable capital
  s: number; // Surplus value
}

/** Unit for c — see API `constant_capital_unit`. */
export type ConstantCapitalUnit =
  | "millions_of_dollars"
  | "coefficient_column_sum";

/** Unit for v and s — see API `labor_and_surplus_unit`. */
export type LaborSurplusUnit = "millions_of_dollars" | "billions_of_dollars";

export interface ProportionalityCheck {
  i_v_plus_s: number;
  ii_c: number;
  simple_reproduction_holds: boolean;
  expanded_reproduction_holds: boolean;
  surplus_ratio?: number | null;
  formula_display: string;
  condition_met: boolean;
}

export interface SankeyNode {
  id: string;
  label?: string | null;
}

export interface SankeyLink {
  source: string;
  target: string;
  value: number;
  color?: string | null;
}

export interface SankeyData {
  nodes: SankeyNode[];
  links: SankeyLink[];
}

export interface ReproductionResponse {
  year: number;
  dept_i: DepartmentValues;
  dept_ii: DepartmentValues;
  flows: number[][]; // 2x2 inter-department flow matrix
  proportionality: ProportionalityCheck;
  sankey_data?: SankeyData | null;
  constant_capital_unit: ConstantCapitalUnit;
  labor_and_surplus_unit: LaborSurplusUnit;
}

export interface CriticalSector {
  code: string;
  name?: string | null;
  backward_linkage: number;
  forward_linkage: number;
  multiplier?: number | null;
  critical: boolean;
}

export interface CriticalSectorsResponse {
  year: number;
  sectors: CriticalSector[];
  threshold: number;
}

// ---------- API client helpers ----------

async function apiFetch<T>(
  path: string,
  params?: Record<string, string | number | undefined>,
  options?: RequestInit
): Promise<T> {
  const url = new URL(path, getPublicApiBase());
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

// ---------- Structural API functions ----------

/**
 * Fetch available I-O table years.
 */
export async function fetchYears(): Promise<YearsResponse> {
  return apiFetch<YearsResponse>("/api/structural/years");
}

/**
 * Fetch I-O matrix for a given year and type.
 * @param year - BEA I-O table year
 * @param type - Matrix type: "coefficients", "inverse", or "flows"
 */
export async function fetchMatrix(
  year: number,
  type?: string
): Promise<MatrixResponse> {
  return apiFetch<MatrixResponse>(`/api/structural/matrix/${year}`, { type });
}

/**
 * Simulate shock propagation through I-O system.
 * @param req - Shock request with year, shock magnitudes, and type
 */
export async function simulateShock(
  req: ShockRequest
): Promise<ShockResultResponse> {
  const res = await fetch(`${getPublicApiBase()}/api/structural/shock`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    let errorMessage = res.statusText;
    try {
      const errorJson = await res.json();
      errorMessage = errorJson.detail || errorMessage;
    } catch {
      // Ignore JSON parse errors
    }
    throw new Error(`API error ${res.status}: ${errorMessage}`);
  }

  return res.json() as Promise<ShockResultResponse>;
}

/**
 * Fetch reproduction schema for a given year.
 * @param year - BEA I-O table year
 */
export async function fetchReproduction(
  year: number
): Promise<ReproductionResponse> {
  return apiFetch<ReproductionResponse>(`/api/structural/reproduction/${year}`);
}

/**
 * Fetch critical sectors based on linkage analysis.
 * @param year - BEA I-O table year
 * @param threshold - Threshold for critical classification (default 0.1)
 */
export async function fetchCriticalSectors(
  year: number,
  threshold?: number
): Promise<CriticalSectorsResponse> {
  return apiFetch<CriticalSectorsResponse>(
    `/api/structural/critical-sectors/${year}`,
    { threshold }
  );
}
