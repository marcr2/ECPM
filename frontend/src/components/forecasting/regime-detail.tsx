"use client";

import { useMemo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { RegimeResult } from "@/lib/forecast-api";

interface RegimeDetailProps {
  data: RegimeResult | null;
  loading?: boolean;
}

const REGIME_COLORS = [
  "hsl(142 76% 36%)", // green - expansion
  "hsl(48 96% 53%)",  // yellow - slowdown
  "hsl(0 84% 60%)",   // red - recession
];

/**
 * Regime detection detail visualization.
 *
 * Features:
 * - Transition matrix as heatmap table
 * - Expected durations per regime
 * - Timeline with smoothed probabilities (stacked area)
 * - Current regime probability bar chart
 */
export function RegimeDetail({ data, loading }: RegimeDetailProps) {
  // Prepare stacked area data for smoothed probabilities
  const smoothedData = useMemo(() => {
    if (!data?.smoothed_probabilities) return [];
    return data.smoothed_probabilities.map((sp) => {
      const point: Record<string, unknown> = { date: sp.date };
      Object.keys(sp).forEach((key) => {
        if (key !== "date") {
          point[key] = sp[key];
        }
      });
      return point;
    });
  }, [data?.smoothed_probabilities]);

  // Get regime names from transition matrix dimensions
  const regimeNames = useMemo(() => {
    if (!data?.transition_matrix) return [];
    return data.transition_matrix.map((_, i) => `Regime ${i}`);
  }, [data?.transition_matrix]);

  // Current probabilities for bar chart
  const currentProbData = useMemo(() => {
    if (!data?.regime_probabilities) return [];
    return Object.entries(data.regime_probabilities).map(([name, prob]) => ({
      name,
      probability: prob * 100,
    }));
  }, [data?.regime_probabilities]);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Regime Detection</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Regime Detection</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No regime data available. Run training first.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle>Regime Detection</CardTitle>
        <Badge
          style={{
            backgroundColor: REGIME_COLORS[data.current_regime] + "20",
            color: REGIME_COLORS[data.current_regime],
            borderColor: REGIME_COLORS[data.current_regime] + "40",
          }}
          className="border"
        >
          {data.regime_label}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Current probability bar chart */}
        <div>
          <h4 className="mb-2 text-sm font-medium text-muted-foreground">
            Current Probabilities
          </h4>
          <div className="h-20">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={currentProbData} layout="vertical">
                <XAxis type="number" domain={[0, 100]} hide />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={80}
                  tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--card)",
                    border: "1px solid var(--border)",
                    borderRadius: "0.5rem",
                    color: "var(--card-foreground)",
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="probability" radius={4}>
                  {currentProbData.map((_, idx) => (
                    <Cell
                      key={`cell-${idx}`}
                      fill={REGIME_COLORS[idx % REGIME_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Transition matrix heatmap */}
        <div>
          <h4 className="mb-2 text-sm font-medium text-muted-foreground">
            Transition Matrix
          </h4>
          <div className="overflow-hidden rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted/50">
                  <th className="border-r border-border px-3 py-2 text-left text-xs font-medium text-muted-foreground">
                    From / To
                  </th>
                  {regimeNames.map((name, i) => (
                    <th
                      key={i}
                      className="px-3 py-2 text-center text-xs font-medium text-muted-foreground"
                    >
                      {name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.transition_matrix.map((row, i) => (
                  <tr key={i} className="border-t border-border">
                    <td className="border-r border-border px-3 py-2 text-xs font-medium">
                      {regimeNames[i]}
                    </td>
                    {row.map((prob, j) => (
                      <td
                        key={j}
                        className="px-3 py-2 text-center tabular-nums"
                        style={{
                          backgroundColor: getHeatmapColor(prob),
                        }}
                      >
                        {(prob * 100).toFixed(0)}%
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Expected durations */}
        {data.regime_durations && (
          <div>
            <h4 className="mb-2 text-sm font-medium text-muted-foreground">
              Expected Durations
            </h4>
            <div className="flex flex-wrap gap-3">
              {Object.entries(data.regime_durations).map(([regime, quarters], idx) => (
                <div
                  key={regime}
                  className="rounded-lg border border-border px-3 py-2"
                  style={{
                    borderColor: REGIME_COLORS[idx % REGIME_COLORS.length] + "40",
                  }}
                >
                  <span className="text-xs text-muted-foreground">{regime}:</span>{" "}
                  <span className="font-medium tabular-nums">
                    {quarters.toFixed(1)} quarters
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Smoothed probabilities timeline */}
        {smoothedData.length > 0 && (
          <div>
            <h4 className="mb-2 text-sm font-medium text-muted-foreground">
              Regime History
            </h4>
            <div className="h-32">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={smoothedData}>
                  <XAxis dataKey="date" hide />
                  <YAxis domain={[0, 1]} hide />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "var(--card)",
                      border: "1px solid var(--border)",
                      borderRadius: "0.5rem",
                      color: "var(--card-foreground)",
                      fontSize: 12,
                    }}
                  />
                  {regimeNames.map((name, i) => (
                    <Area
                      key={name}
                      type="monotone"
                      dataKey={`regime_${i}`}
                      name={name}
                      stackId="1"
                      stroke={REGIME_COLORS[i]}
                      fill={REGIME_COLORS[i]}
                      fillOpacity={0.6}
                    />
                  ))}
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Generate heatmap background color based on probability value.
 * Higher values are more saturated.
 */
function getHeatmapColor(prob: number): string {
  const intensity = Math.floor(prob * 255);
  return `rgba(59, 130, 246, ${prob * 0.4})`; // blue with varying opacity
}
