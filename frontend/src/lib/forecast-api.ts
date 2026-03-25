/**
 * TypeScript API client for forecasting endpoints.
 *
 * Mirrors Pydantic schemas from backend/ecpm/modeling/schemas.py.
 * Follows the pattern established in api.ts with apiFetch helper.
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ---------- Types (mirror backend Pydantic schemas) ----------

export interface ForecastPoint {
  date: string;
  point: number;
  lower_68: number;
  upper_68: number;
  lower_95: number;
  upper_95: number;
}

export interface IndicatorForecast {
  indicator: string;
  horizon_quarters: number;
  forecasts: ForecastPoint[];
  model_info: Record<string, unknown>;
}

export interface ForecastsResponse {
  forecasts: Record<string, IndicatorForecast>;
  generated_at: string;
}

export interface RegimeResult {
  current_regime: number;
  regime_label: string;
  regime_probabilities: Record<string, number>;
  transition_matrix: number[][];
  smoothed_probabilities: Array<Record<string, unknown>>;
  regime_durations?: Record<string, number>;
}

export interface CrisisIndex {
  current_value: number;
  trpf_component: number;
  realization_component: number;
  financial_component: number;
  history: Array<Record<string, unknown>>;
}

export interface BacktestResult {
  episode_name: string;
  start_date: string;
  end_date: string;
  crisis_index_series: Array<{ date: string; value: number }>;
  warning_12m: boolean | null;
  warning_24m: boolean | null;
  peak_value: number | null;
  peak_date: string | null;
  insufficient_data?: boolean;
}

export interface BacktestsResponse {
  backtests: BacktestResult[];
  generated_at: string;
}

export interface TrainingStep {
  name: string;
  status: string; // "pending" | "running" | "complete" | "error"
  timestamp: string;
  duration_ms?: number;
  detail?: string;
  error?: string;
}

export interface TrainingLogResponse {
  entries: TrainingStep[];
  count: number;
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

// ---------- Forecast API functions ----------

/**
 * Fetch VAR forecast results from cache.
 * @param indicator - Optional indicator slug to filter by
 * @param horizon - Forecast horizon in quarters (1-24, default 8)
 */
export async function fetchForecasts(
  indicator?: string,
  horizon?: number
): Promise<ForecastsResponse> {
  // Convert frontend slug format (hyphens) to backend format (underscores)
  const apiIndicator = indicator?.replace(/-/g, "_");
  return apiFetch<ForecastsResponse>("/api/forecasting/forecasts", {
    indicator: apiIndicator,
    horizon,
  });
}

/**
 * Fetch regime detection results from cache.
 */
export async function fetchRegime(): Promise<RegimeResult> {
  return apiFetch<RegimeResult>("/api/forecasting/regime");
}

/**
 * Fetch composite crisis index from cache.
 */
export async function fetchCrisisIndex(): Promise<CrisisIndex> {
  return apiFetch<CrisisIndex>("/api/forecasting/crisis-index");
}

/**
 * Fetch backtest results from cache.
 */
export async function fetchBacktests(): Promise<BacktestsResponse> {
  return apiFetch<BacktestsResponse>("/api/forecasting/backtests");
}

/**
 * Fetch the latest training log from the server.
 */
export async function fetchTrainingLog(): Promise<TrainingLogResponse> {
  return apiFetch<TrainingLogResponse>("/api/forecasting/training/log");
}
