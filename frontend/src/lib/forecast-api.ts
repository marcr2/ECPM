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
  warning_12m: boolean;
  warning_24m: boolean;
  peak_value: number;
  peak_date: string;
}

export interface BacktestsResponse {
  backtests: BacktestResult[];
  generated_at: string;
}

export interface TrainingStep {
  name: string;
  status: string; // "pending" | "running" | "complete" | "error"
  duration_ms?: number;
  detail?: string;
}

export interface TrainingTriggerResponse {
  task_id: string;
  status: string;
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
  return apiFetch<ForecastsResponse>("/api/forecasting/forecasts", {
    indicator,
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
 * Trigger model training pipeline.
 * Returns task_id for tracking via SSE stream.
 */
export async function triggerTraining(): Promise<TrainingTriggerResponse> {
  const res = await fetch(`${API_BASE}/api/forecasting/train`, {
    method: "POST",
    headers: { Accept: "application/json" },
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

  return res.json() as Promise<TrainingTriggerResponse>;
}

/**
 * Subscribe to training progress SSE stream.
 *
 * @param onMessage - Callback for each progress event
 * @param onError - Optional callback for errors
 * @returns EventSource instance (call .close() to unsubscribe)
 */
export function subscribeToTrainingProgress(
  onMessage: (data: TrainingStep) => void,
  onError?: (err: Event) => void
): EventSource {
  const url = `${API_BASE}/api/forecasting/training/stream`;
  const eventSource = new EventSource(url);

  eventSource.addEventListener("progress", (event) => {
    try {
      const data = JSON.parse(event.data) as TrainingStep;
      onMessage(data);
    } catch {
      console.error("Failed to parse training progress event:", event.data);
    }
  });

  eventSource.addEventListener("done", () => {
    eventSource.close();
  });

  eventSource.onerror = (err) => {
    if (onError) {
      onError(err);
    }
    // Retry after 3s delay on error
    setTimeout(() => {
      if (eventSource.readyState === EventSource.CLOSED) {
        return; // Already closed, don't retry
      }
    }, 3000);
  };

  return eventSource;
}
