"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { IndustryListItem } from "@/lib/concentration-api";

interface IndustryRankingBarsProps {
  industries: IndustryListItem[];
  sortBy: "cr4" | "hhi" | "trend";
  onSelect: (naics: string) => void;
}

/**
 * Horizontal bar chart showing industries ranked by concentration.
 * Color gradient from green (competitive) to red (monopoly).
 */
export function IndustryRankingBars({
  industries,
  sortBy,
  onSelect,
}: IndustryRankingBarsProps) {
  // Sort industries based on selected metric
  const sortedIndustries = [...industries].sort((a, b) => {
    if (sortBy === "cr4") return b.cr4 - a.cr4;
    if (sortBy === "hhi") return b.hhi - a.hhi;
    // For trend, prioritize increasing
    const trendOrder = { increasing: 2, stable: 1, decreasing: 0 };
    return (
      (trendOrder[b.trend_direction as keyof typeof trendOrder] || 0) -
      (trendOrder[a.trend_direction as keyof typeof trendOrder] || 0)
    );
  });

  // Take top 20 for display
  const displayData = sortedIndustries.slice(0, 20).map((ind) => ({
    ...ind,
    displayName: ind.name.length > 25 ? ind.name.slice(0, 22) + "..." : ind.name,
    value: sortBy === "hhi" ? ind.hhi : ind.cr4,
  }));

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">
          Industry Ranking by {sortBy.toUpperCase()}
        </h3>
        <div className="flex gap-1 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-green-500" />
            Competitive
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-red-500" />
            Monopoly
          </span>
        </div>
      </div>

      <div className="h-[500px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            layout="vertical"
            data={displayData}
            margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
            onClick={(data) => {
              if (data?.activePayload?.[0]?.payload?.naics) {
                onSelect(data.activePayload[0].payload.naics);
              }
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              type="number"
              domain={sortBy === "hhi" ? [0, 10000] : [0, 100]}
              tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
            />
            <YAxis
              type="category"
              dataKey="displayName"
              width={95}
              tick={{ fill: "var(--muted-foreground)", fontSize: 10 }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--card)",
                border: "1px solid var(--border)",
              }}
              formatter={(value: number) => [
                sortBy === "hhi" ? value.toFixed(0) : `${value.toFixed(1)}%`,
                sortBy.toUpperCase(),
              ]}
              labelFormatter={(label) => {
                const item = displayData.find((d) => d.displayName === label);
                return item?.name || label;
              }}
            />
            <Bar
              dataKey="value"
              cursor="pointer"
              radius={[0, 4, 4, 0]}
            >
              {displayData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={getConcentrationColor(entry.hhi)}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

/**
 * Get color based on HHI concentration level.
 * Green (competitive) -> Yellow (moderate) -> Red (monopoly)
 */
function getConcentrationColor(hhi: number): string {
  if (hhi < 1500) return "#22c55e"; // green - competitive
  if (hhi < 2500) return "#eab308"; // yellow - moderately concentrated
  if (hhi < 5000) return "#f97316"; // orange - highly concentrated
  if (hhi < 7000) return "#ef4444"; // red - very concentrated
  return "#dc2626"; // dark red - monopoly
}
