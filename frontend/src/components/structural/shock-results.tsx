"use client";

import { useState, useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { ShockResultResponse } from "@/lib/structural-api";
import { getSectorName } from "@/lib/bea-sector-names";

interface ShockResultsProps {
  results: ShockResultResponse | null;
  loading?: boolean;
  error?: string | null;
}

/**
 * Shock simulation results visualization.
 *
 * Features:
 * - Bar chart showing impact by industry (sorted by magnitude)
 * - Top 10 by default with "Show All" toggle
 * - Color: red for negative, green for positive
 * - Stats: total impact, weakest link badge
 */
export function ShockResults({ results, loading = false, error }: ShockResultsProps) {
  const [showAll, setShowAll] = useState(false);

  // Sort impacts by absolute magnitude and prepare chart data,
  // excluding the shocked (target) sectors themselves.
  const chartData = useMemo(() => {
    if (!results) return [];

    const shockedSet = new Set(results.shocked_sectors);
    const filtered = results.impacts.filter((i) => !shockedSet.has(i.code));
    const sorted = filtered.sort(
      (a, b) => Math.abs(b.impact) - Math.abs(a.impact)
    );

    return showAll ? sorted : sorted.slice(0, 10);
  }, [results, showAll]);

  // Find weakest link (largest negative impact)
  const weakestLink = useMemo(() => {
    if (!results) return null;
    const negatives = results.impacts.filter((i) => i.impact < 0);
    if (negatives.length === 0) return null;
    return negatives.reduce((min, curr) =>
      curr.impact < min.impact ? curr : min
    );
  }, [results]);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Simulation Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-[350px] w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Simulation Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-[350px] items-center justify-center">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!results) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Simulation Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-[350px] items-center justify-center">
            <p className="text-sm text-muted-foreground">
              Configure and run a shock simulation to see results.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle>Simulation Results</CardTitle>
          <div className="flex flex-wrap items-center gap-3">
            {/* Total impact */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">
                Total Impact:
              </span>
              <span
                className={`text-lg font-bold tabular-nums ${
                  results.total_impact >= 0 ? "text-green-500" : "text-red-500"
                }`}
              >
                {results.total_impact >= 0 ? "+" : ""}
                {(results.total_impact * 100).toFixed(2)}%
              </span>
            </div>

            {/* Weakest link badge */}
            {weakestLink && (
              <Badge variant="destructive" className="text-xs">
                Weakest: {getSectorName(weakestLink.code)} ({(weakestLink.impact * 100).toFixed(1)}%)
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-2 flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            Showing {chartData.length} of {results.impacts.length - results.shocked_sectors.length} industries
          </span>
          {results.impacts.length - results.shocked_sectors.length > 10 && (
            <Button
              variant="ghost"
              size="xs"
              onClick={() => setShowAll(!showAll)}
            >
              {showAll ? "Show Top 10" : "Show All"}
            </Button>
          )}
        </div>

        <ResponsiveContainer width="100%" height={350}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <XAxis
              type="number"
              domain={["auto", "auto"]}
              tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
              stroke="var(--muted-foreground)"
              fontSize={11}
            />
            <YAxis
              type="category"
              dataKey="code"
              width={180}
              stroke="var(--muted-foreground)"
              fontSize={10}
              tickLine={false}
              tickFormatter={(code: string) => {
                const name = getSectorName(code);
                return name.length > 26 ? name.slice(0, 24) + "\u2026" : name;
              }}
            />
            <Tooltip
              cursor={{ fill: "oklch(var(--muted) / 0.3)" }}
              contentStyle={{
                backgroundColor: "var(--card)",
                border: "1px solid var(--border)",
                borderRadius: "0.5rem",
                color: "var(--card-foreground)",
                fontSize: 12,
              }}
              content={({ active, payload }) => {
                if (!active || !payload || !payload[0]) return null;
                const item = payload[0].payload as { sector: string; code: string; impact: number };
                const name = getSectorName(item.code);
                return (
                  <div className="rounded-md border border-border bg-card px-3 py-2 text-sm shadow-lg">
                    <p className="font-medium">{name}</p>
                    {name !== item.code && (
                      <p className="font-mono text-xs text-muted-foreground">{item.code}</p>
                    )}
                    <p className={`mt-1 font-bold tabular-nums ${item.impact >= 0 ? "text-green-500" : "text-red-500"}`}>
                      Impact: {item.impact >= 0 ? "+" : ""}{(item.impact * 100).toFixed(2)}%
                    </p>
                  </div>
                );
              }}
            />
            <ReferenceLine x={0} stroke="var(--muted-foreground)" />
            <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={
                    entry.impact >= 0
                      ? "var(--chart-2)"
                      : "var(--destructive)"
                  }
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        {/* Shocked sectors info */}
        <div className="mt-4 border-t border-border pt-3">
          <span className="text-xs text-muted-foreground">
            Shocked sectors:{" "}
            <span className="font-medium text-foreground">
              {results.shocked_sectors
                .map((code) => getSectorName(code))
                .join(", ")}
            </span>
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
