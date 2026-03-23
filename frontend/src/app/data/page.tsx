"use client";

import { useEffect, useState, useCallback } from "react";
import type { SeriesMetadata, FetchStatus } from "@/lib/api";
import { fetchSeries, fetchStatus } from "@/lib/api";
import { SeriesTable } from "@/components/data/series-table";
import { FetchStatusCard } from "@/components/data/fetch-status";

export default function DataOverviewPage() {
  const [series, setSeries] = useState<SeriesMetadata[]>([]);
  const [status, setStatus] = useState<FetchStatus | null>(null);
  const [isLoadingSeries, setIsLoadingSeries] = useState(true);
  const [isLoadingStatus, setIsLoadingStatus] = useState(true);
  const [seriesError, setSeriesError] = useState<string | null>(null);

  const loadSeries = useCallback(async () => {
    setIsLoadingSeries(true);
    setSeriesError(null);
    try {
      const res = await fetchSeries();
      setSeries(res.series);
    } catch (err) {
      setSeriesError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setIsLoadingSeries(false);
    }
  }, []);

  const loadStatus = useCallback(async () => {
    setIsLoadingStatus(true);
    try {
      const res = await fetchStatus();
      setStatus(res);
    } catch {
      // Status card handles missing data gracefully
    } finally {
      setIsLoadingStatus(false);
    }
  }, []);

  const loadAll = useCallback(() => {
    loadSeries();
    loadStatus();
  }, [loadSeries, loadStatus]);

  useEffect(() => {
    loadAll();
    const interval = setInterval(loadAll, 30_000);
    return () => clearInterval(interval);
  }, [loadAll]);

  return (
    <div className="space-y-4">
      <FetchStatusCard
        status={status}
        isLoading={isLoadingStatus}
        onRefresh={loadAll}
      />
      <SeriesTable
        data={series}
        isLoading={isLoadingSeries}
        error={seriesError}
      />
    </div>
  );
}
