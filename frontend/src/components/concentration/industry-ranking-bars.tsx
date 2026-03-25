"use client";

import { useEffect, useMemo, useRef, useState } from "react";
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

function formatTooltipNumber(v: number): string {
  return v.toFixed(2);
}

function formatRankingTooltipScore(
  sortBy: "cr4" | "hhi" | "trend",
  row: IndustryListItem
): string {
  if (sortBy === "cr4") {
    return `CR4=${formatTooltipNumber(row.cr4)}`;
  }
  if (sortBy === "hhi") {
    return `HHI=${formatTooltipNumber(row.hhi)}`;
  }
  const slope = row.trend_slope;
  if (slope == null || Number.isNaN(slope)) {
    return "TREND=—";
  }
  return `TREND=${formatTooltipNumber(slope)}`;
}

const Y_TICK_FONT = "10px system-ui, -apple-system, sans-serif";
const Y_TICK_PADDING = 12;
/** Minimum horizontal room kept for the value axis + bars (CR4 0–100 or HHI scale). */
const MIN_VALUE_PLOT_PX: Record<"cr4" | "hhi" | "trend", number> = {
  cr4: 108,
  hhi: 132,
  trend: 108,
};

function measureMaxTextWidthPx(texts: string[], font = Y_TICK_FONT): number {
  if (typeof document === "undefined") return 0;
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  if (!ctx) return 0;
  ctx.font = font;
  let max = 0;
  for (const t of texts) {
    max = Math.max(max, ctx.measureText(t).width);
  }
  return max;
}

/** Same ordering as the ranking chart — reuse for the correlation heatmap rows. */
export function sortIndustriesByMetric(
  industries: IndustryListItem[],
  sortBy: "cr4" | "hhi" | "trend"
): IndustryListItem[] {
  return [...industries].sort((a, b) => {
    if (sortBy === "cr4") return b.cr4 - a.cr4;
    if (sortBy === "hhi") return b.hhi - a.hhi;
    const trendOrder = { increasing: 2, stable: 1, decreasing: 0 };
    return (
      (trendOrder[b.trend_direction as keyof typeof trendOrder] || 0) -
      (trendOrder[a.trend_direction as keyof typeof trendOrder] || 0)
    );
  });
}

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
  const chartWrapRef = useRef<HTMLDivElement>(null);
  const [chartWidth, setChartWidth] = useState(0);

  useEffect(() => {
    const el = chartWrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setChartWidth(el.clientWidth));
    ro.observe(el);
    setChartWidth(el.clientWidth);
    return () => ro.disconnect();
  }, []);

  const sortedIndustries = useMemo(
    () => sortIndustriesByMetric(industries, sortBy),
    [industries, sortBy]
  );

  const top20Names = useMemo(
    () => sortedIndustries.slice(0, 20).map((i) => i.name),
    [sortedIndustries]
  );

  const measuredLabelWidth = useMemo(
    () => measureMaxTextWidthPx(top20Names),
    [top20Names]
  );

  const idealLabelBand = measuredLabelWidth + Y_TICK_PADDING;

  /** Outer chart margins only — Y-axis label width is set separately on `YAxis` to avoid double left gutter. */
  const marginL = 4;
  const marginR = 10;
  const minPlot = MIN_VALUE_PLOT_PX[sortBy];

  const labelBandPx = useMemo(() => {
    if (chartWidth <= 0) {
      return Math.ceil(Math.min(Math.max(idealLabelBand, 80), 240));
    }
    const inner = chartWidth - marginL - marginR;
    const maxBandForFullNames = Math.max(0, inner - minPlot);
    const band = Math.min(idealLabelBand, maxBandForFullNames);
    return Math.max(64, Math.ceil(band));
  }, [chartWidth, idealLabelBand, minPlot]);

  const mustTruncateLabels = idealLabelBand > labelBandPx + 0.5;
  const maxLabelChars = mustTruncateLabels
    ? Math.max(14, Math.floor(labelBandPx / 5.15))
    : Number.POSITIVE_INFINITY;

  const displayData = useMemo(() => {
    return sortedIndustries.slice(0, 20).map((ind) => ({
      ...ind,
      displayName:
        mustTruncateLabels && ind.name.length > maxLabelChars
          ? ind.name.slice(0, Math.max(1, maxLabelChars - 3)) + "..."
          : ind.name,
      value: sortBy === "hhi" ? ind.hhi : ind.cr4,
    }));
  }, [sortedIndustries, sortBy, mustTruncateLabels, maxLabelChars]);

  return (
    <div className="flex h-full min-w-0 flex-col gap-2">
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

      <div
        ref={chartWrapRef}
        className="min-h-[500px] w-full min-w-0 flex-1"
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            layout="vertical"
            data={displayData}
            margin={{
              top: 5,
              right: marginR,
              left: marginL,
              bottom: 5,
            }}
            barCategoryGap="5%"
            onClick={(data: unknown) => {
              const d = data as { activePayload?: Array<{ payload?: { naics?: string } }> } | null;
              if (d?.activePayload?.[0]?.payload?.naics) {
                onSelect(d.activePayload[0].payload.naics);
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
              width={labelBandPx}
              tick={{
                fill: "var(--foreground)",
                fontSize: 10,
                fontFamily: "system-ui, sans-serif",
              }}
              interval={0}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.[0]) return null;
                const row = payload[0].payload as IndustryListItem;
                return (
                  <div
                    className="rounded-md border px-2.5 py-1.5 text-xs shadow-md"
                    style={{
                      backgroundColor: "var(--card)",
                      border: "1px solid var(--border)",
                    }}
                  >
                    <p className="font-medium text-foreground">{row.name}</p>
                    <p className="mt-0.5 tabular-nums text-muted-foreground">
                      {formatRankingTooltipScore(sortBy, row)}
                    </p>
                  </div>
                );
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
