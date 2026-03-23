const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ---------- Types ----------

export interface SeriesMetadata {
  series_id: string;
  source: "FRED" | "BEA";
  name: string;
  units: string | null;
  frequency: "D" | "M" | "Q" | "A";
  seasonal_adjustment: string | null;
  last_updated: string | null;
  last_fetched: string | null;
  observation_count: number;
  fetch_status: "pending" | "ok" | "stale" | "error";
  fetch_error: string | null;
}

export interface Observation {
  date: string;
  value: number;
  vintage_date: string | null;
}

export interface SeriesDataResponse {
  metadata: SeriesMetadata;
  observations: Observation[];
  total_observations: number;
}

export interface SeriesListResponse {
  series: SeriesMetadata[];
  total: number;
}

export interface FetchStatus {
  last_fetch_time: string | null;
  next_scheduled_run: string | null;
  total_series: number;
  ok_count: number;
  error_count: number;
  stale_count: number;
  errors: Array<{ series_id: string; error_message: string }>;
}

export interface FetchTriggerResponse {
  task_id: string;
  status: string;
}

// ---------- Query parameter types ----------

export interface SeriesListParams {
  source?: string;
  status?: string;
  search?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export interface SeriesDataParams {
  start_date?: string;
  end_date?: string;
  frequency?: string;
  fill_method?: string;
}

// ---------- API client ----------

async function apiFetch<T>(
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

export async function fetchSeries(
  params?: SeriesListParams
): Promise<SeriesListResponse> {
  return apiFetch<SeriesListResponse>("/api/data/series", params as Record<string, string | undefined>);
}

export async function fetchSeriesData(
  seriesId: string,
  params?: SeriesDataParams
): Promise<SeriesDataResponse> {
  return apiFetch<SeriesDataResponse>(
    `/api/data/series/${encodeURIComponent(seriesId)}`,
    params as Record<string, string | undefined>
  );
}

export async function fetchStatus(): Promise<FetchStatus> {
  return apiFetch<FetchStatus>("/api/data/status");
}

export async function triggerFetch(): Promise<FetchTriggerResponse> {
  const res = await fetch(`${API_BASE}/api/data/fetch`, {
    method: "POST",
    headers: { Accept: "application/json" },
  });

  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }

  return res.json() as Promise<FetchTriggerResponse>;
}
