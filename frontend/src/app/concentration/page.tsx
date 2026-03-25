"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  fetchOverview,
  fetchIndustries,
  fetchTopCorrelations,
  type OverviewResponse,
  type IndustryListItem,
  type TopCorrelationItem,
} from "@/lib/concentration-api";
import { ConcentrationOverview } from "@/components/concentration/concentration-overview";
import { IndustryRankingBars } from "@/components/concentration/industry-ranking-bars";
import { CorrelationHeatmap } from "@/components/concentration/correlation-heatmap";
import { ConcentrationCard } from "@/components/concentration/concentration-card";
import { SearchableSelect } from "@/components/ui/searchable-select";
import { Skeleton } from "@/components/ui/skeleton";

type SortBy = "cr4" | "hhi" | "trend";

export default function ConcentrationPage() {
  const router = useRouter();
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [industries, setIndustries] = useState<IndustryListItem[]>([]);
  const [correlations, setCorrelations] = useState<TopCorrelationItem[]>([]);
  const [sortBy, setSortBy] = useState<SortBy>("cr4");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch all data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [overviewData, industriesData, correlationsData] = await Promise.all([
        fetchOverview(),
        fetchIndustries(),
        fetchTopCorrelations(25),
      ]);

      setOverview(overviewData);
      setIndustries(industriesData.industries);
      setCorrelations(correlationsData.correlations);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();

    // Auto-refresh every 60 seconds
    const interval = setInterval(loadData, 60000);
    return () => clearInterval(interval);
  }, [loadData]);

  const industryOptions = industries.map((ind) => ({
    value: ind.naics,
    label: ind.name,
    detail: ind.naics,
  }));

  // Navigation handlers
  const handleIndustrySelect = (naics: string) => {
    router.push(`/concentration/${naics}`);
  };

  const handleCellClick = (naics: string, indicatorSlug: string) => {
    router.push(`/concentration/${naics}/${indicatorSlug}`);
  };

  if (error) {
    return (
      <div className="flex min-h-[400px] items-center justify-center p-6">
        <div className="text-center">
          <p className="text-lg font-medium text-destructive">Error loading data</p>
          <p className="mt-1 text-sm text-muted-foreground">{error}</p>
          <button
            onClick={loadData}
            className="mt-4 rounded bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Page header */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              Corporate Concentration Analysis
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Market concentration metrics and crisis indicator correlations by industry
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Sort by:</span>
            {(["cr4", "hhi", "trend"] as const).map((option) => (
              <button
                key={option}
                onClick={() => setSortBy(option)}
                className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
                  sortBy === option
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                }`}
              >
                {option.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Industry search */}
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-muted-foreground whitespace-nowrap">
            Find industry:
          </label>
          <SearchableSelect
            options={industryOptions}
            value=""
            onChange={(naics) => {
              if (naics) handleIndustrySelect(naics);
            }}
            placeholder="Search by name or NAICS code…"
            aria-label="Search industries"
            className="w-full max-w-sm"
            disabled={loading || industries.length === 0}
          />
        </div>
      </div>

      {/* Hero section: Overview chart */}
      <div className="rounded-lg border border-border bg-card p-4">
        {loading || !overview ? (
          <div className="space-y-4">
            <Skeleton className="h-6 w-48" />
            <div className="grid grid-cols-2 gap-4">
              <Skeleton className="h-32" />
              <Skeleton className="h-32" />
            </div>
            <Skeleton className="h-64" />
          </div>
        ) : (
          <ConcentrationOverview data={overview} />
        )}
      </div>

      {/* Two-column layout: Ranking + Heatmap */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left: Industry ranking bars */}
        <div className="rounded-lg border border-border bg-card p-4">
          {loading ? (
            <div className="space-y-2">
              <Skeleton className="h-6 w-40" />
              <Skeleton className="h-[500px]" />
            </div>
          ) : (
            <IndustryRankingBars
              industries={industries}
              sortBy={sortBy}
              onSelect={handleIndustrySelect}
            />
          )}
        </div>

        {/* Right: Correlation heatmap */}
        <div className="rounded-lg border border-border bg-card p-4">
          {loading ? (
            <div className="space-y-2">
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-[400px]" />
            </div>
          ) : (
            <CorrelationHeatmap
              correlations={correlations}
              minConfidence={25}
              onCellClick={handleCellClick}
            />
          )}
        </div>
      </div>

      {/* Bottom grid: Most concentrated industries */}
      {overview && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground">
            Most Concentrated Industries
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {overview.most_concentrated.map((ind) => (
              <ConcentrationCard
                key={ind.naics}
                industry={ind}
                onClick={() => handleIndustrySelect(ind.naics)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Fastest increasing */}
      {overview && overview.fastest_increasing.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground">
            Fastest Increasing Concentration
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {overview.fastest_increasing.map((ind) => (
              <ConcentrationCard
                key={ind.naics}
                industry={ind}
                onClick={() => handleIndustrySelect(ind.naics)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
