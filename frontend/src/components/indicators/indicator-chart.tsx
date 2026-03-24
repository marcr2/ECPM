"use client";

import {
  ComposedChart,
  Line,
  Area,
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
import type { ForecastPoint } from "@/lib/forecast-api";

interface IndicatorChartProps {
  data: { date: string; [key: string]: number | string }[];
  primaryKey: string;
  primaryLabel: string;
  overlayKey?: string;
  overlayLabel?: string;
  crisisMode: "shaded" | "lines" | "hidden";
  height?: number;
  forecastData?: ForecastPoint[];
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
  forecastData,
}: IndicatorChartProps) {
  /**
   * Merge historical data with forecast data for chart rendering.
   * Forecast points are added to the chartData with forecast-specific keys.
   */
  const chartData = forecastData
    ? mergeWithForecast(data, forecastData)
    : data;
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
      <ComposedChart data={chartData}>
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
        {/* Forecast confidence intervals and line */}
        {forecastData && forecastData.length > 0 && (
          <>
            {/* 95% CI band (lighter) */}
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="ci_95"
              name="95% CI"
              fill="hsl(var(--chart-3))"
              fillOpacity={0.1}
              stroke="none"
              legendType="none"
            />
            {/* 68% CI band (darker) */}
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="ci_68"
              name="68% CI"
              fill="hsl(var(--chart-3))"
              fillOpacity={0.2}
              stroke="none"
              legendType="none"
            />
            {/* Forecast point line (dashed) */}
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="forecast"
              name="Forecast (8Q horizon)"
              stroke="hsl(var(--chart-3))"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              connectNulls
            />
          </>
        )}
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

/**
 * Merge historical data with forecast data.
 *
 * For Area charts to render CI bands properly, we use an array format
 * where [lower, upper] defines the band boundaries. The forecast data
 * is appended after the historical data, with ci_68 and ci_95 arrays.
 */
function mergeWithForecast(
  data: { date: string; [key: string]: number | string }[],
  forecastData: ForecastPoint[]
): { date: string; [key: string]: number | string | [number, number] }[] {
  // Build a map from forecast dates to forecast points
  const forecastMap = new Map(forecastData.map((fp) => [fp.date, fp]));

  // Add forecast fields to existing data points if dates overlap
  const merged = data.map((dp) => {
    const fp = forecastMap.get(dp.date);
    if (fp) {
      forecastMap.delete(dp.date);
      return {
        ...dp,
        forecast: fp.point,
        ci_68: [fp.lower_68, fp.upper_68] as [number, number],
        ci_95: [fp.lower_95, fp.upper_95] as [number, number],
      };
    }
    return dp;
  });

  // Append remaining forecast points that extend beyond historical data
  const remaining = Array.from(forecastMap.values())
    .sort((a, b) => a.date.localeCompare(b.date))
    .map((fp) => ({
      date: fp.date,
      forecast: fp.point,
      ci_68: [fp.lower_68, fp.upper_68] as [number, number],
      ci_95: [fp.lower_95, fp.upper_95] as [number, number],
    }));

  return [...merged, ...remaining];
}
