"use client";

import { useEffect, useState, useCallback, use } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  fetchIndustryHistory,
  fetchFirms,
  fetchCorrelations,
  type ConcentrationHistoryResponse,
  type FirmsResponse,
  type CorrelationsResponse,
} from "@/lib/concentration-api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { TopFirmsTable } from "@/components/concentration/top-firms-table";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";

interface PageProps {
  params: Promise<{ naics: string }>;
}

export default function IndustryDetailPage({ params }: PageProps) {
  const { naics } = use(params);
  const router = useRouter();

  const [history, setHistory] = useState<ConcentrationHistoryResponse | null>(null);
  const [firms, setFirms] = useState<FirmsResponse | null>(null);
  const [correlations, setCorrelations] = useState<CorrelationsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const historyData = await fetchIndustryHistory(naics);
      setHistory(historyData);

      // Get latest year from history
      const latestYear = historyData.data.length > 0
        ? Math.max(...historyData.data.map((d) => d.year))
        : 2022;

      const [firmsData, correlationsData] = await Promise.all([
        fetchFirms(naics, latestYear).catch(() => null),
        fetchCorrelations(naics, 0).catch(() => null),
      ]);

      setFirms(firmsData);
      setCorrelations(correlationsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, [naics]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Get current concentration level
  const getCurrentLevel = () => {
    if (!history || history.data.length === 0) return "unknown";
    const latest = history.data[history.data.length - 1];
    if (latest.hhi > 7000) return "monopoly";
    if (latest.hhi > 2500) return "highly_concentrated";
    if (latest.hhi > 1500) return "moderately_concentrated";
    return "competitive";
  };

  const levelColors: Record<string, string> = {
    monopoly: "bg-red-500/10 text-red-500",
    highly_concentrated: "bg-orange-500/10 text-orange-500",
    moderately_concentrated: "bg-yellow-500/10 text-yellow-500",
    competitive: "bg-green-500/10 text-green-500",
    unknown: "bg-muted text-muted-foreground",
  };

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
        <span className="font-medium text-foreground">
          {loading ? <Skeleton className="inline-block h-4 w-32" /> : history?.name || naics}
        </span>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            {loading ? <Skeleton className="h-8 w-64" /> : history?.name}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">NAICS: {naics}</p>
        </div>
        {history && history.data.length > 0 && (
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-2xl font-bold text-foreground">
                {history.data[history.data.length - 1].cr4.toFixed(1)}%
              </div>
              <div className="text-xs text-muted-foreground">CR4</div>
            </div>
            <div className="text-right">
              <div className="text-xl font-semibold text-foreground">
                {history.data[history.data.length - 1].hhi.toFixed(0)}
              </div>
              <div className="text-xs text-muted-foreground">HHI</div>
            </div>
            <Badge
              variant="outline"
              className={`border-0 ${levelColors[getCurrentLevel()]}`}
            >
              {getCurrentLevel().replace("_", " ")}
            </Badge>
          </div>
        )}
      </div>

      {/* Tabs */}
      <Tabs defaultValue="history" className="space-y-4">
        <TabsList>
          <TabsTrigger value="history">History</TabsTrigger>
          <TabsTrigger value="firms">Firms</TabsTrigger>
          <TabsTrigger value="correlations">Crisis Correlations</TabsTrigger>
        </TabsList>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4">
          <div className="rounded-lg border border-border bg-card p-4">
            {loading || !history ? (
              <Skeleton className="h-64" />
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-foreground">
                    Concentration Over Time
                  </h3>
                  <div className="text-xs text-muted-foreground">
                    Trend: {history.trend.direction} (slope: {history.trend.slope.toFixed(2)}/yr)
                  </div>
                </div>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={history.data}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                      <XAxis
                        dataKey="year"
                        tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
                      />
                      <YAxis
                        yAxisId="left"
                        tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
                        label={{
                          value: "CR4/CR8 (%)",
                          angle: -90,
                          position: "insideLeft",
                          fill: "var(--muted-foreground)",
                        }}
                      />
                      <YAxis
                        yAxisId="right"
                        orientation="right"
                        tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
                        label={{
                          value: "HHI",
                          angle: 90,
                          position: "insideRight",
                          fill: "var(--muted-foreground)",
                        }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "var(--card)",
                          border: "1px solid var(--border)",
                        }}
                      />
                      <Legend />
                      <Line
                        yAxisId="left"
                        type="monotone"
                        dataKey="cr4"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        name="CR4"
                      />
                      <Line
                        yAxisId="left"
                        type="monotone"
                        dataKey="cr8"
                        stroke="#8b5cf6"
                        strokeWidth={2}
                        name="CR8"
                      />
                      <Line
                        yAxisId="right"
                        type="monotone"
                        dataKey="hhi"
                        stroke="#22c55e"
                        strokeWidth={2}
                        name="HHI"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </div>
        </TabsContent>

        {/* Firms Tab */}
        <TabsContent value="firms">
          <div className="rounded-lg border border-border bg-card p-4">
            {loading ? (
              <Skeleton className="h-64" />
            ) : firms ? (
              <TopFirmsTable firms={firms.firms} year={firms.year} />
            ) : (
              <p className="py-8 text-center text-muted-foreground">
                No firm data available for this industry.
              </p>
            )}
          </div>
        </TabsContent>

        {/* Correlations Tab */}
        <TabsContent value="correlations">
          <div className="rounded-lg border border-border bg-card p-4">
            {loading ? (
              <Skeleton className="h-64" />
            ) : correlations && correlations.correlations.length > 0 ? (
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-foreground">
                  Crisis Indicator Correlations
                </h3>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  {correlations.correlations.map((corr) => (
                    <Link
                      key={corr.indicator_slug}
                      href={`/concentration/${naics}/${corr.indicator_slug}`}
                      className="rounded-lg border border-border bg-background p-3 transition-colors hover:bg-muted"
                    >
                      <div className="text-sm font-medium text-foreground">
                        {corr.indicator_name}
                      </div>
                      <div className="mt-2 flex items-center justify-between">
                        <span
                          className={`text-lg font-bold ${
                            corr.relationship === "positive"
                              ? "text-blue-500"
                              : corr.relationship === "negative"
                                ? "text-red-500"
                                : "text-muted-foreground"
                          }`}
                        >
                          r = {corr.correlation.toFixed(2)}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {corr.confidence.toFixed(0)}% conf
                        </span>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            ) : (
              <p className="py-8 text-center text-muted-foreground">
                No correlation data available. Run data ingestion first.
              </p>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
