"use client";

import { useEffect, useState, useCallback } from "react";
import type { SeriesMetadata, FetchStatus } from "@/lib/api";
import { fetchSeries, fetchStatus } from "@/lib/api";
import { SeriesTable } from "@/components/data/series-table";
import { FetchStatusCard } from "@/components/data/fetch-status";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface IOStatus {
  years_loaded: number[];
  total_tables: number;
  last_updated: string | null;
}

interface ConcentrationStatus {
  total_rows: number;
  years_loaded: number[];
  num_industries: number;
}

export default function DataOverviewPage() {
  const [series, setSeries] = useState<SeriesMetadata[]>([]);
  const [status, setStatus] = useState<FetchStatus | null>(null);
  const [ioStatus, setIoStatus] = useState<IOStatus | null>(null);
  const [concStatus, setConcStatus] = useState<ConcentrationStatus | null>(null);
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

  const loadExtendedStatus = useCallback(async () => {
    try {
      const [ioRes, concRes] = await Promise.all([
        fetch(`${API_BASE}/api/data/io-status`).then((r) =>
          r.ok ? r.json() : null
        ),
        fetch(`${API_BASE}/api/data/concentration-status`).then((r) =>
          r.ok ? r.json() : null
        ),
      ]);
      setIoStatus(ioRes);
      setConcStatus(concRes);
    } catch {
      // Non-fatal
    }
  }, []);

  const loadAll = useCallback(() => {
    loadSeries();
    loadStatus();
    loadExtendedStatus();
  }, [loadSeries, loadStatus, loadExtendedStatus]);

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
      />

      {/* Extended data status: I-O Tables and Concentration */}
      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Input-Output Tables</CardTitle>
          </CardHeader>
          <CardContent>
            {ioStatus ? (
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Tables loaded</span>
                  <Badge variant={ioStatus.total_tables > 0 ? "default" : "secondary"}>
                    {ioStatus.total_tables}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Years</span>
                  <span className="text-foreground">
                    {ioStatus.years_loaded.length > 0
                      ? ioStatus.years_loaded.join(", ")
                      : "None"}
                  </span>
                </div>
                {ioStatus.last_updated && (
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Last updated</span>
                    <span className="text-xs text-foreground">
                      {new Date(ioStatus.last_updated).toLocaleDateString()}
                    </span>
                  </div>
                )}
                {ioStatus.total_tables === 0 && (
                  <p className="mt-2 text-xs text-muted-foreground">
                    No I-O data loaded. Trigger ingestion via the fetch-io endpoint or Celery task.
                  </p>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Loading...</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Concentration Data</CardTitle>
          </CardHeader>
          <CardContent>
            {concStatus ? (
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Industries</span>
                  <Badge variant={concStatus.num_industries > 0 ? "default" : "secondary"}>
                    {concStatus.num_industries}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Data rows</span>
                  <span className="text-foreground">{concStatus.total_rows}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Years</span>
                  <span className="text-foreground">
                    {concStatus.years_loaded.length > 0
                      ? concStatus.years_loaded.join(", ")
                      : "None"}
                  </span>
                </div>
                {concStatus.num_industries === 0 && (
                  <p className="mt-2 text-xs text-muted-foreground">
                    No concentration data loaded. Trigger ingestion via the fetch-concentration endpoint or Celery task.
                  </p>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Loading...</p>
            )}
          </CardContent>
        </Card>
      </div>

      <SeriesTable
        data={series}
        isLoading={isLoadingSeries}
        error={seriesError}
      />
    </div>
  );
}
