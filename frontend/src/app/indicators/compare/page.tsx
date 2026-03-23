"use client";

import { useEffect, useState, useMemo } from "react";
import {
  fetchIndicatorComparison,
  type IndicatorData,
} from "@/lib/indicators";
import { INDICATOR_DEFS } from "@/lib/indicator-defs";
import { IndicatorChart } from "@/components/indicators/indicator-chart";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

/**
 * Side-by-side methodology comparison view.
 *
 * Shows the same indicator computed under both Shaikh/Tonak and Kliman
 * methodologies overlaid on the same chart with different colors.
 */
export default function ComparePage() {
  const [selectedSlug, setSelectedSlug] = useState(
    INDICATOR_DEFS[0]?.slug ?? "rate-of-profit"
  );
  const [comparison, setComparison] = useState<Record<
    string,
    IndicatorData
  > | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const result = await fetchIndicatorComparison(selectedSlug);
        setComparison(result.methodologies);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load comparison data"
        );
        setComparison(null);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [selectedSlug]);

  const selectedDef = INDICATOR_DEFS.find((d) => d.slug === selectedSlug);

  // Merge data from both methodologies into a single chart dataset
  const chartData = useMemo(() => {
    if (!comparison) return [];

    const entries = Object.entries(comparison);
    if (entries.length === 0) return [];

    // Build a map: date -> { date, methodology1: value, methodology2: value }
    const dateMap = new Map<
      string,
      { date: string; [key: string]: number | string }
    >();

    for (const [methodologySlug, indData] of entries) {
      for (const dp of indData.data) {
        const existing = dateMap.get(dp.date) ?? { date: dp.date };
        existing[methodologySlug] = dp.value;
        dateMap.set(dp.date, existing);
      }
    }

    // Sort by date
    return [...dateMap.values()].sort((a, b) =>
      a.date.localeCompare(b.date)
    );
  }, [comparison]);

  // Get methodology keys for chart
  const methodologyKeys = comparison ? Object.keys(comparison) : [];
  const primaryKey = methodologyKeys[0] ?? "shaikh-tonak";
  const overlayKey = methodologyKeys[1] ?? undefined;

  // Human-readable labels
  const methodologyLabels: Record<string, string> = {
    "shaikh-tonak": "Shaikh/Tonak",
    kliman: "Kliman TSSI",
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Methodology Comparison</h2>
        <p className="text-sm text-muted-foreground">
          Compare the same indicator computed under different Marxist
          methodologies
        </p>
      </div>

      {/* Indicator selector */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-muted-foreground">
          Indicator:
        </span>
        <select
          value={selectedSlug}
          onChange={(e) => setSelectedSlug(e.target.value)}
          className="h-8 rounded-md border border-border bg-background px-3 text-sm text-foreground outline-none focus:ring-1 focus:ring-ring"
        >
          {INDICATOR_DEFS.map((def) => (
            <option key={def.slug} value={def.slug}>
              {def.name}
            </option>
          ))}
        </select>
      </div>

      {/* Chart */}
      {loading ? (
        <Skeleton className="h-[420px] w-full rounded-xl" />
      ) : error ? (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 text-center">
          <h2 className="mb-2 text-lg font-semibold">
            Failed to load comparison
          </h2>
          <p className="mb-4 text-sm text-muted-foreground">{error}</p>
          <Button variant="outline" onClick={() => window.location.reload()}>
            Retry
          </Button>
        </div>
      ) : chartData.length === 0 ? (
        <div className="rounded-xl border border-border bg-card p-8 text-center text-muted-foreground">
          No comparison data available for this indicator.
        </div>
      ) : (
        <div className="space-y-2">
          <div className="rounded-xl border border-border bg-card p-4">
            <IndicatorChart
              data={chartData}
              primaryKey={primaryKey}
              primaryLabel={
                methodologyLabels[primaryKey] ?? primaryKey
              }
              overlayKey={overlayKey}
              overlayLabel={
                overlayKey
                  ? (methodologyLabels[overlayKey] ?? overlayKey)
                  : undefined
              }
              crisisMode="shaded"
              height={420}
            />
          </div>

          {/* Legend */}
          <div className="flex items-center justify-center gap-6 text-xs text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <div className="h-0.5 w-6 rounded-full bg-[hsl(var(--chart-1))]" />
              <span>
                {methodologyLabels[primaryKey] ?? primaryKey}
              </span>
            </div>
            {overlayKey && (
              <div className="flex items-center gap-1.5">
                <div className="h-0.5 w-6 rounded-full bg-[hsl(var(--chart-2))]" style={{ backgroundImage: "repeating-linear-gradient(90deg, transparent, transparent 3px, hsl(var(--chart-2)) 3px, hsl(var(--chart-2)) 6px)" }} />
                <span>
                  {methodologyLabels[overlayKey] ?? overlayKey}
                </span>
              </div>
            )}
          </div>

          {/* Info */}
          {selectedDef && (
            <p className="text-center text-xs text-muted-foreground">
              {selectedDef.name} ({selectedDef.units}) -- {selectedDef.description}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
