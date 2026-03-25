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
  ReferenceArea,
  ReferenceLine,
} from "recharts";
import { CRISIS_EPISODES } from "@/lib/crisis-episodes";
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

  /**
   * Map crisis episodes to nearest actual data points.
   * Recharts ReferenceArea with type="category" XAxis requires exact matches.
   */
  function findNearestDate(targetDate: string): string | null {
    if (chartData.length === 0) return null;

    const target = new Date(targetDate).getTime();
    let nearest = chartData[0].date;
    let minDiff = Math.abs(new Date(chartData[0].date).getTime() - target);

    for (const point of chartData) {
      const diff = Math.abs(new Date(point.date).getTime() - target);
      if (diff < minDiff) {
        minDiff = diff;
        nearest = point.date;
      }
    }

    return nearest;
  }

  const firstDataDate = chartData[0]?.date;
  const lastDataDate = chartData[chartData.length - 1]?.date;

  const mappedCrises = CRISIS_EPISODES
    // Pre-filter: only keep crises whose original period overlaps the data range
    .filter(crisis => {
      if (!firstDataDate || !lastDataDate) return false;
      return crisis.endDate >= firstDataDate && crisis.startDate <= lastDataDate;
    })
    .map(crisis => {
      let mappedStart = findNearestDate(crisis.startDate) ?? crisis.startDate;
      let mappedEnd = findNearestDate(crisis.endDate) ?? crisis.endDate;

      // When a crisis is shorter than the data resolution (e.g. COVID on
      // annual data), both boundaries collapse to the same point. Expand the
      // range so the annotation still spans at least two adjacent data points.
      if (mappedStart === mappedEnd) {
        const idx = chartData.findIndex((d) => d.date === mappedStart);
        if (idx >= 0 && idx < chartData.length - 1) {
          mappedEnd = chartData[idx + 1].date;
        } else if (idx > 0) {
          // At the very last point – expand backwards instead
          mappedStart = chartData[idx - 1].date;
        }
      }

      return {
        ...crisis,
        originalStart: crisis.startDate,
        originalEnd: crisis.endDate,
        startDate: mappedStart,
        endDate: mappedEnd,
      };
    });




  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={chartData}>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="var(--border)"
          opacity={0.3}
        />
        <XAxis
          dataKey="date"
          tickFormatter={formatDateTick}
          stroke="var(--foreground)"
          fontSize={12}
          tickLine={false}
          opacity={0.7}
        />
        <YAxis
          yAxisId="left"
          orientation="left"
          stroke="var(--foreground)"
          fontSize={12}
          tickLine={false}
          opacity={0.7}
          label={{
            value: primaryLabel,
            angle: -90,
            position: "insideLeft",
            style: {
              fill: "var(--foreground)",
              fontSize: 11,
              opacity: 0.7,
            },
          }}
        />
        {overlayKey && (
          <YAxis
            yAxisId="right"
            orientation="right"
            stroke="var(--foreground)"
            fontSize={12}
            tickLine={false}
            opacity={0.7}
            label={{
              value: overlayLabel ?? overlayKey,
              angle: 90,
              position: "insideRight",
              style: {
                fill: "var(--foreground)",
                fontSize: 11,
                opacity: 0.7,
              },
            }}
          />
        )}
        <Tooltip
          contentStyle={{
            backgroundColor: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: "0.5rem",
            color: "var(--card-foreground)",
            fontSize: 12,
          }}
        />
        <Legend
          wrapperStyle={{
            fontSize: 12,
            color: "var(--muted-foreground)",
          }}
        />
        {/* Shaded crisis regions (back-most layer) */}
        {crisisMode === "shaded" && mappedCrises.map((crisis) => (
          <ReferenceArea
            key={crisis.name}
            x1={crisis.startDate}
            x2={crisis.endDate}
            fill={crisis.color}
            fillOpacity={0.15}
            stroke={crisis.color}
            strokeOpacity={0.4}
            yAxisId="left"
            ifOverflow="extendDomain"
          />
        ))}
        {/* Crisis labels: in front of shading, behind data lines */}
        {crisisMode === "shaded" && mappedCrises.map((crisis) => (
          <ReferenceArea
            key={`${crisis.name}-label`}
            x1={crisis.startDate}
            x2={crisis.endDate}
            fill="transparent"
            fillOpacity={0}
            stroke="none"
            yAxisId="left"
            ifOverflow="extendDomain"
            label={{
              value: crisis.name,
              position: "center",
              fill: crisis.color,
              fontSize: 14,
              fontWeight: 700,
              angle: -90,
            }}
          />
        ))}
        {crisisMode === "lines" && mappedCrises.flatMap((crisis) => [
          <ReferenceLine
            key={`${crisis.name}-start`}
            x={crisis.startDate}
            stroke={crisis.color}
            strokeWidth={3}
            strokeDasharray="5 5"
            yAxisId="left"
            ifOverflow="extendDomain"
          />,
          <ReferenceLine
            key={`${crisis.name}-end`}
            x={crisis.endDate}
            stroke={crisis.color}
            strokeWidth={3}
            strokeDasharray="5 5"
            yAxisId="left"
            ifOverflow="extendDomain"
          />,
        ])}
        {crisisMode === "lines" && mappedCrises.map((crisis) => (
          <ReferenceArea
            key={`${crisis.name}-label`}
            x1={crisis.startDate}
            x2={crisis.endDate}
            fill="transparent"
            fillOpacity={0}
            stroke="none"
            yAxisId="left"
            ifOverflow="extendDomain"
            label={{
              value: crisis.name,
              position: "center",
              fontSize: 14,
              fontWeight: 700,
              fill: crisis.color,
              angle: -90,
            }}
          />
        ))}
        <Line
          yAxisId="left"
          type="monotone"
          dataKey={primaryKey}
          name={primaryLabel}
          stroke="var(--chart-1)"
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
              fill="var(--chart-3)"
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
              fill="var(--chart-3)"
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
              stroke="var(--chart-3)"
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
            stroke="var(--chart-2)"
            strokeWidth={2}
            dot={false}
            connectNulls
            strokeDasharray="5 3"
          />
        )}
        <Brush
          dataKey="date"
          height={30}
          stroke="var(--primary)"
          fill="var(--muted)"
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
