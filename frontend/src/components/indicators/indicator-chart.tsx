"use client";

import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Brush,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { CRISIS_EPISODES } from "@/lib/crisis-episodes";
import { CrisisAnnotations } from "./crisis-annotations";

interface IndicatorChartProps {
  data: { date: string; [key: string]: number | string }[];
  primaryKey: string;
  primaryLabel: string;
  overlayKey?: string;
  overlayLabel?: string;
  crisisMode: "shaded" | "lines" | "hidden";
  height?: number;
}

/**
 * Main chart component for indicator detail pages.
 *
 * Uses Recharts ComposedChart (not LineChart) to support mixing Line
 * with ReferenceArea crisis annotations. Supports:
 * - Primary indicator on left y-axis
 * - Optional overlay indicator on right y-axis (dual y-axis)
 * - Crisis episode annotations as shaded regions, lines, or hidden
 * - Brush component at the bottom for zoom/pan date range selection
 */
export function IndicatorChart({
  data,
  primaryKey,
  primaryLabel,
  overlayKey,
  overlayLabel,
  crisisMode,
  height = 400,
}: IndicatorChartProps) {
  /**
   * Format date as year only for the x-axis tick labels.
   * Full dates are shown in the tooltip.
   */
  function formatDateTick(value: string): string {
    if (!value) return "";
    const year = value.slice(0, 4);
    return year;
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data}>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="hsl(var(--border))"
        />
        <XAxis
          dataKey="date"
          tickFormatter={formatDateTick}
          stroke="hsl(var(--muted-foreground))"
          fontSize={12}
          tickLine={false}
        />
        <YAxis
          yAxisId="left"
          orientation="left"
          stroke="hsl(var(--muted-foreground))"
          fontSize={12}
          tickLine={false}
          label={{
            value: primaryLabel,
            angle: -90,
            position: "insideLeft",
            style: {
              fill: "hsl(var(--muted-foreground))",
              fontSize: 11,
            },
          }}
        />
        {overlayKey && (
          <YAxis
            yAxisId="right"
            orientation="right"
            stroke="hsl(var(--muted-foreground))"
            fontSize={12}
            tickLine={false}
            label={{
              value: overlayLabel ?? overlayKey,
              angle: 90,
              position: "insideRight",
              style: {
                fill: "hsl(var(--muted-foreground))",
                fontSize: 11,
              },
            }}
          />
        )}
        <Tooltip
          contentStyle={{
            backgroundColor: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "0.5rem",
            color: "hsl(var(--card-foreground))",
            fontSize: 12,
          }}
        />
        <Legend
          wrapperStyle={{
            fontSize: 12,
            color: "hsl(var(--muted-foreground))",
          }}
        />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey={primaryKey}
          name={primaryLabel}
          stroke="hsl(var(--chart-1))"
          strokeWidth={2}
          dot={false}
          connectNulls
        />
        {overlayKey && (
          <Line
            yAxisId="right"
            type="monotone"
            dataKey={overlayKey}
            name={overlayLabel ?? overlayKey}
            stroke="hsl(var(--chart-2))"
            strokeWidth={2}
            dot={false}
            connectNulls
            strokeDasharray="5 3"
          />
        )}
        <CrisisAnnotations
          crises={CRISIS_EPISODES}
          visible={crisisMode}
        />
        <Brush
          dataKey="date"
          height={30}
          stroke="hsl(var(--primary))"
          fill="hsl(var(--muted))"
          tickFormatter={formatDateTick}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
