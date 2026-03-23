"use client";

import { use, useEffect, useState, useCallback, useMemo } from "react";
import {
  fetchIndicatorData,
  fetchMethodologyDocs,
  type IndicatorData,
  type IndicatorMethodologyDoc,
} from "@/lib/indicators";
import { INDICATOR_DEFS, type IndicatorDef } from "@/lib/indicator-defs";
import { IndicatorChart } from "@/components/indicators/indicator-chart";
import { DateRangeControls } from "@/components/indicators/date-range-controls";
import { OverlaySelector } from "@/components/indicators/overlay-selector";
import { FormulaDisplay } from "@/components/indicators/formula-display";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useMethodology } from "../layout";

/**
 * Individual indicator detail page (DASH-01, DASH-02, DASH-03).
 *
 * Uses Next.js 16 async params via React.use().
 * Shows interactive Recharts chart with crisis annotations,
 * Brush zoom, date range presets, and overlay selector.
 */
export default function IndicatorDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);
  const { methodology } = useMethodology();

  const [data, setData] = useState<IndicatorData | null>(null);
  const [overlayData, setOverlayData] = useState<IndicatorData | null>(null);
  const [formulaDoc, setFormulaDoc] = useState<IndicatorMethodologyDoc | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [dateRange, setDateRange] = useState<number | null>(null);
  const [overlaySlug, setOverlaySlug] = useState<string | null>(null);
  const [crisisMode, setCrisisMode] = useState<"shaded" | "lines" | "hidden">("shaded");

  const def: IndicatorDef | undefined = INDICATOR_DEFS.find(
    (d) => d.slug === slug
  );

  // Load primary indicator data
  const loadData = useCallback(async () => {
    try {
      const result = await fetchIndicatorData(slug, { methodology });
      setData(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load indicator data");
    } finally {
      setLoading(false);
    }
  }, [slug, methodology]);

  useEffect(() => {
    setLoading(true);
    setOverlaySlug(null);
    setOverlayData(null);
    loadData();
  }, [loadData]);

  // Load formula documentation
  useEffect(() => {
    async function loadFormula() {
      try {
        const docs = await fetchMethodologyDocs(methodology);
        const doc = docs.indicators?.find(
          (d) => d.indicator_slug === slug
        );
        setFormulaDoc(doc ?? null);
      } catch {
        // Non-critical -- formula display is optional
        setFormulaDoc(null);
      }
    }
    loadFormula();
  }, [slug, methodology]);

  // Load overlay indicator data
  useEffect(() => {
    if (!overlaySlug) {
      setOverlayData(null);
      return;
    }
    async function loadOverlay() {
      try {
        const result = await fetchIndicatorData(overlaySlug!, { methodology });
        setOverlayData(result);
      } catch {
        setOverlayData(null);
      }
    }
    loadOverlay();
  }, [overlaySlug, methodology]);

  // Filter data by date range
  const filteredData = useMemo(() => {
    if (!data?.data) return [];
    if (dateRange === null) return data.data;

    const cutoff = new Date();
    cutoff.setFullYear(cutoff.getFullYear() - dateRange);
    const cutoffStr = cutoff.toISOString().slice(0, 10);

    return data.data.filter((dp) => dp.date >= cutoffStr);
  }, [data, dateRange]);

  // Merge primary + overlay data for chart
  const chartData = useMemo(() => {
    const primaryKey = "value";
    const overlayKey = overlaySlug ? "overlay" : undefined;

    if (!overlayData || !overlaySlug) {
      return filteredData.map((dp) => ({
        date: dp.date,
        [primaryKey]: dp.value,
      }));
    }

    // Build lookup for overlay
    const overlayMap = new Map(
      overlayData.data.map((dp) => [dp.date, dp.value])
    );

    return filteredData.map((dp) => ({
      date: dp.date,
      [primaryKey]: dp.value,
      ...(overlayMap.has(dp.date) ? { overlay: overlayMap.get(dp.date) } : {}),
    }));
  }, [filteredData, overlayData, overlaySlug]);

  const overlayDef = overlaySlug
    ? INDICATOR_DEFS.find((d) => d.slug === overlaySlug)
    : undefined;

  if (loading) {
    return <DetailSkeleton />;
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 text-center">
        <h2 className="mb-2 text-lg font-semibold">Failed to load indicator</h2>
        <p className="mb-4 text-sm text-muted-foreground">{error}</p>
        <Button
          variant="outline"
          onClick={() => {
            setLoading(true);
            loadData();
          }}
        >
          Retry
        </Button>
      </div>
    );
  }

  if (!data || !def) {
    return (
      <div className="p-6 text-center text-muted-foreground">
        Indicator not found.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold">{def.name}</h2>
          <p className="text-sm text-muted-foreground">{def.description}</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline">{def.units}</Badge>
          <Badge variant="secondary">{methodology}</Badge>
        </div>
      </div>

      {/* Main Chart */}
      <div className="rounded-xl border border-border bg-card p-4">
        <IndicatorChart
          data={chartData}
          primaryKey="value"
          primaryLabel={def.name}
          overlayKey={overlaySlug ? "overlay" : undefined}
          overlayLabel={overlayDef?.name}
          crisisMode={crisisMode}
          height={420}
        />
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-muted-foreground">
            Range:
          </span>
          <DateRangeControls
            onRangeChange={setDateRange}
            activeRange={dateRange}
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-muted-foreground">
            Overlay:
          </span>
          <OverlaySelector
            currentSlug={slug}
            onOverlayChange={setOverlaySlug}
            activeOverlay={overlaySlug}
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-muted-foreground">
            Crises:
          </span>
          <div className="inline-flex items-center gap-0.5 rounded-lg border border-border bg-muted p-0.5">
            {(["shaded", "lines", "hidden"] as const).map((mode) => (
              <Button
                key={mode}
                variant={crisisMode === mode ? "default" : "ghost"}
                size="xs"
                onClick={() => setCrisisMode(mode)}
                className="rounded-md capitalize"
              >
                {mode}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* Formula Display */}
      {formulaDoc?.formula_latex && (
        <div className="rounded-xl border border-border bg-card p-4">
          <h3 className="mb-2 text-sm font-medium text-muted-foreground">
            Formula
          </h3>
          <FormulaDisplay latex={formulaDoc.formula_latex} />
        </div>
      )}
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-5 w-16 rounded-full" />
          <Skeleton className="h-5 w-24 rounded-full" />
        </div>
      </div>
      <Skeleton className="h-[420px] w-full rounded-xl" />
      <div className="flex gap-4">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-6 w-36" />
        <Skeleton className="h-6 w-40" />
      </div>
    </div>
  );
}
