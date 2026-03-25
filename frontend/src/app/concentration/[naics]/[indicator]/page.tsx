"use client";

import { useEffect, useState, useCallback, use } from "react";
import Link from "next/link";
import {
  fetchIndustryHistory,
  fetchCorrelations,
  type ConcentrationHistoryResponse,
  type CorrelationInfo,
} from "@/lib/concentration-api";
import { IndustryIndicatorChart } from "@/components/concentration/industry-indicator-chart";
import { ConfidenceBreakdown } from "@/components/concentration/confidence-breakdown";
import { Skeleton } from "@/components/ui/skeleton";
import { getPublicApiBase } from "@/lib/public-api-base";

// Indicator name mapping
const INDICATOR_NAMES: Record<string, string> = {
  "rate-of-profit": "Rate of Profit",
  "occ": "Organic Composition of Capital",
  "rate-of-surplus-value": "Rate of Surplus Value",
  "mass-of-profit": "Mass of Profit",
  "productivity-wage-gap": "Productivity-Wage Gap",
  "credit-gdp-gap": "Credit-to-GDP Gap",
  "financial-real-ratio": "Financial-to-Real Asset Ratio",
  "debt-service-ratio": "Corporate Debt Service Ratio",
};

interface PageProps {
  params: Promise<{ naics: string; indicator: string }>;
}

export default function IndustryIndicatorPage({ params }: PageProps) {
  const { naics, indicator } = use(params);

  const [history, setHistory] = useState<ConcentrationHistoryResponse | null>(null);
  const [correlation, setCorrelation] = useState<CorrelationInfo | null>(null);
  const [indicatorData, setIndicatorData] = useState<{ year: number; value: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [historyData, correlationsData] = await Promise.all([
        fetchIndustryHistory(naics),
        fetchCorrelations(naics, 0),
      ]);

      setHistory(historyData);

      // Find the specific indicator correlation
      const matchedCorr = correlationsData.correlations.find(
        (c) => c.indicator_slug === indicator
      );

      if (matchedCorr) {
        setCorrelation(matchedCorr);
      } else {
        setCorrelation({
          indicator_slug: indicator,
          indicator_name: INDICATOR_NAMES[indicator] || indicator,
          correlation: 0,
          confidence: 0,
          lag_months: 0,
          relationship: "none",
        });
      }

      // Fetch real indicator time series from the indicators API
      const apiSlug = indicator.replace(/-/g, "_");
      const apiBase = getPublicApiBase();
      try {
        const indRes = await fetch(
          `${apiBase}/api/indicators/${apiSlug}?methodology=shaikh-tonak`,
          { headers: { Accept: "application/json" } }
        );
        if (indRes.ok) {
          const indJson = await indRes.json();
          const points: { date: string; value: number }[] = indJson.data ?? [];
          // Aggregate to annual averages aligned with concentration years
          const yearMap = new Map<number, { sum: number; count: number }>();
          for (const pt of points) {
            if (pt.value == null) continue;
            const yr = new Date(pt.date).getFullYear();
            const entry = yearMap.get(yr) ?? { sum: 0, count: 0 };
            entry.sum += pt.value;
            entry.count += 1;
            yearMap.set(yr, entry);
          }
          const annualData = Array.from(yearMap.entries())
            .map(([yr, { sum, count }]) => ({ year: yr, value: sum / count }))
            .sort((a, b) => a.year - b.year);
          setIndicatorData(annualData);
        }
      } catch {
        // Non-fatal: indicator data may not be available
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, [naics, indicator]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (error) {
    return (
      <div className="flex min-h-[400px] items-center justify-center p-6">
        <div className="text-center">
          <p className="text-lg font-medium text-destructive">{error}</p>
          <button
            onClick={loadData}
            className="mt-4 rounded bg-primary px-4 py-2 text-sm text-primary-foreground"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm">
        <Link href="/concentration" className="text-muted-foreground hover:text-foreground">
          Concentration
        </Link>
        <span className="text-muted-foreground">/</span>
        <Link
          href={`/concentration/${naics}`}
          className="text-muted-foreground hover:text-foreground"
        >
          {loading ? <Skeleton className="inline-block h-4 w-24" /> : history?.name || naics}
        </Link>
        <span className="text-muted-foreground">/</span>
        <span className="font-medium text-foreground">
          {INDICATOR_NAMES[indicator] || indicator}
        </span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">
          {loading ? (
            <Skeleton className="h-8 w-96" />
          ) : (
            `${history?.name} vs ${INDICATOR_NAMES[indicator]}`
          )}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Correlation analysis between industry concentration and crisis indicator
        </p>
      </div>

      {/* Main content grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Chart - takes 2 columns */}
        <div className="rounded-lg border border-border bg-card p-4 lg:col-span-2">
          {loading || !history || !correlation ? (
            <Skeleton className="h-80" />
          ) : (
            <IndustryIndicatorChart
              concentrationData={history.data}
              indicatorData={indicatorData}
              correlation={correlation}
            />
          )}
        </div>

        {/* Confidence breakdown - takes 1 column */}
        <div>
          {loading || !correlation ? (
            <Skeleton className="h-80" />
          ) : (
            <ConfidenceBreakdown
              correlation={correlation.correlation}
              sampleSize={history?.data.length || 0}
              rSquared={history?.trend.r_squared || 0}
              confidence={correlation.confidence}
            />
          )}
        </div>
      </div>

      {/* Additional context */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Interpretation */}
        <div className="rounded-lg border border-border bg-card p-4">
          <h3 className="text-sm font-semibold text-foreground">Interpretation</h3>
          <div className="mt-2 space-y-2 text-sm text-muted-foreground">
            {correlation && (
              <>
                <p>
                  The correlation coefficient of{" "}
                  <span className="font-medium text-foreground">
                    r = {correlation.correlation.toFixed(2)}
                  </span>{" "}
                  indicates a{" "}
                  <span className="font-medium text-foreground">
                    {Math.abs(correlation.correlation) < 0.3
                      ? "weak"
                      : Math.abs(correlation.correlation) < 0.7
                        ? "moderate"
                        : "strong"}
                  </span>{" "}
                  {correlation.relationship} relationship between concentration and this indicator.
                </p>
                {correlation.lag_months > 0 && (
                  <p>
                    The optimal lag of{" "}
                    <span className="font-medium text-foreground">
                      {correlation.lag_months} months
                    </span>{" "}
                    suggests concentration changes may{" "}
                    <span className="font-medium text-foreground">lead</span> indicator movements,
                    potentially serving as an early warning signal.
                  </p>
                )}
              </>
            )}
          </div>
        </div>

        {/* Technical details */}
        <div className="rounded-lg border border-border bg-card p-4">
          <h3 className="text-sm font-semibold text-foreground">Technical Details</h3>
          <div className="mt-2 space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Industry NAICS:</span>
              <span className="font-mono text-foreground">{naics}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Indicator:</span>
              <span className="text-foreground">{indicator}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Data points:</span>
              <span className="text-foreground">{history?.data.length || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Time range:</span>
              <span className="text-foreground">
                {history && history.data.length > 0
                  ? `${history.data[0].year} - ${history.data[history.data.length - 1].year}`
                  : "-"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Concentration trend:</span>
              <span className="text-foreground capitalize">
                {history?.trend.direction || "-"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Back link */}
      <div className="flex justify-between">
        <Link
          href={`/concentration/${naics}`}
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          &larr; Back to {history?.name || naics}
        </Link>
        <Link
          href="/concentration"
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          View all industries &rarr;
        </Link>
      </div>
    </div>
  );
}
