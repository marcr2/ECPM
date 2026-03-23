"use client";

import { useEffect, useState, useCallback } from "react";
import { fetchIndicatorOverview, type IndicatorOverview } from "@/lib/indicators";
import {
  HERO_INDICATORS,
  SECONDARY_INDICATORS,
  INDICATOR_DEFS,
} from "@/lib/indicator-defs";
import { IndicatorCard } from "@/components/indicators/indicator-card";
import { useMethodology } from "./layout";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Indicator overview dashboard (DASH-04).
 *
 * Displays hero row (TRPF trio: Rate of Profit, OCC, Rate of Surplus Value)
 * and secondary row (remaining 5 indicators). Each card links to its detail
 * page. Auto-refreshes every 60 seconds.
 */
export default function IndicatorOverviewPage() {
  const { methodology } = useMethodology();
  const [overview, setOverview] = useState<IndicatorOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const data = await fetchIndicatorOverview(methodology);
      setOverview(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load indicators");
    } finally {
      setLoading(false);
    }
  }, [methodology]);

  useEffect(() => {
    setLoading(true);
    loadData();
  }, [loadData]);

  // Auto-refresh polling every 60 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      loadData();
    }, 60_000);
    return () => clearInterval(interval);
  }, [loadData]);

  if (loading) {
    return <OverviewSkeleton />;
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 text-center">
        <h2 className="mb-2 text-lg font-semibold">
          Failed to load indicators
        </h2>
        <p className="mb-4 text-sm text-muted-foreground">{error}</p>
        <button
          onClick={() => {
            setLoading(true);
            loadData();
          }}
          className="rounded-md bg-primary px-3 py-1.5 text-sm text-primary-foreground"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!overview) return null;

  // Build a lookup from slug to API summary data
  const summaryMap = new Map(
    overview.indicators.map((ind) => [ind.slug, ind])
  );

  return (
    <div className="space-y-6">
      {/* Hero row: TRPF trio (3 cards) */}
      <section>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wider text-muted-foreground">
          Tendency of the Rate of Profit to Fall
        </h2>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {HERO_INDICATORS.map((def) => {
            const summary = summaryMap.get(def.slug);
            if (!summary) return null;
            return (
              <IndicatorCard
                key={def.slug}
                indicator={summary}
                size="hero"
                def={def}
              />
            );
          })}
        </div>
      </section>

      {/* Secondary section: remaining indicators */}
      <section>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wider text-muted-foreground">
          Extended Indicators
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {SECONDARY_INDICATORS.map((def) => {
            const summary = summaryMap.get(def.slug);
            if (!summary) return null;
            return (
              <IndicatorCard
                key={def.slug}
                indicator={summary}
                size="secondary"
                def={def}
              />
            );
          })}
        </div>
      </section>
    </div>
  );
}

function OverviewSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={`hero-${i}`}
            className="rounded-xl bg-card p-4 ring-1 ring-foreground/10"
          >
            <Skeleton className="mb-3 h-5 w-40" />
            <Skeleton className="mb-2 h-8 w-24" />
            <Skeleton className="h-12 w-full" />
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={`sec-${i}`}
            className="rounded-xl bg-card p-4 ring-1 ring-foreground/10"
          >
            <Skeleton className="mb-2 h-4 w-32" />
            <Skeleton className="mb-2 h-6 w-20" />
            <Skeleton className="h-8 w-full" />
          </div>
        ))}
      </div>
    </div>
  );
}
