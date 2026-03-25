"use client";

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
import type { OverviewResponse } from "@/lib/concentration-api";

interface ConcentrationOverviewProps {
  data: OverviewResponse;
}

/**
 * Hero chart showing Department I vs Department II concentration trends.
 * Uses dual lines to compare means-of-production vs means-of-consumption sectors.
 */
export function ConcentrationOverview({ data }: ConcentrationOverviewProps) {
  // Build comparison data for the chart
  const chartData = [
    {
      name: "Dept I (Production)",
      cr4: data.dept_i.cr4,
      hhi: data.dept_i.hhi,
      trend: data.dept_i.trend_direction,
    },
    {
      name: "Dept II (Consumption)",
      cr4: data.dept_ii.cr4,
      hhi: data.dept_ii.hhi,
      trend: data.dept_ii.trend_direction,
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-foreground">
          Economy-Wide Concentration
        </h2>
        <div className="flex gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-blue-500" />
            Dept I (Production)
          </span>
          <span className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-green-500" />
            Dept II (Consumption)
          </span>
        </div>
      </div>

      {/* Department comparison cards */}
      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-lg border border-border bg-card p-4">
          <h3 className="text-sm font-medium text-muted-foreground">
            Department I (Means of Production)
          </h3>
          <div className="mt-2 flex items-baseline gap-4">
            <div>
              <span className="text-2xl font-bold text-foreground">
                {data.dept_i.cr4.toFixed(1)}%
              </span>
              <span className="ml-1 text-sm text-muted-foreground">CR4</span>
            </div>
            <div>
              <span className="text-xl font-semibold text-foreground">
                {data.dept_i.hhi.toFixed(0)}
              </span>
              <span className="ml-1 text-sm text-muted-foreground">HHI</span>
            </div>
          </div>
          <div className="mt-2 text-sm">
            <TrendBadge direction={data.dept_i.trend_direction} />
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-4">
          <h3 className="text-sm font-medium text-muted-foreground">
            Department II (Means of Consumption)
          </h3>
          <div className="mt-2 flex items-baseline gap-4">
            <div>
              <span className="text-2xl font-bold text-foreground">
                {data.dept_ii.cr4.toFixed(1)}%
              </span>
              <span className="ml-1 text-sm text-muted-foreground">CR4</span>
            </div>
            <div>
              <span className="text-xl font-semibold text-foreground">
                {data.dept_ii.hhi.toFixed(0)}
              </span>
              <span className="ml-1 text-sm text-muted-foreground">HHI</span>
            </div>
          </div>
          <div className="mt-2 text-sm">
            <TrendBadge direction={data.dept_ii.trend_direction} />
          </div>
        </div>
      </div>

      {/* Bar comparison chart */}
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="name"
              tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
            />
            <YAxis
              yAxisId="left"
              tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
              label={{
                value: "CR4 (%)",
                angle: -90,
                position: "insideLeft",
                fill: "var(--muted-foreground)",
              }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
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
              formatter={(value, name) => [
                typeof value === "number" && Number.isFinite(value)
                  ? value.toFixed(2)
                  : String(value ?? "—"),
                name,
              ]}
            />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="cr4"
              stroke="#3b82f6"
              strokeWidth={2}
              name="CR4 (%)"
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
  );
}

function TrendBadge({ direction }: { direction: string }) {
  const colors = {
    increasing: "text-red-500 bg-red-500/10",
    decreasing: "text-green-500 bg-green-500/10",
    stable: "text-yellow-500 bg-yellow-500/10",
  };

  const arrows = {
    increasing: "\u2191",
    decreasing: "\u2193",
    stable: "\u2192",
  };

  const color = colors[direction as keyof typeof colors] || colors.stable;
  const arrow = arrows[direction as keyof typeof arrows] || arrows.stable;

  return (
    <span className={`inline-flex items-center gap-1 rounded px-2 py-0.5 ${color}`}>
      <span>{arrow}</span>
      <span className="capitalize">{direction}</span>
    </span>
  );
}
