"use client";

import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { ConcentrationDataPoint, CorrelationInfo } from "@/lib/concentration-api";

interface IndicatorDataPoint {
  year: number;
  value: number;
}

interface IndustryIndicatorChartProps {
  concentrationData: ConcentrationDataPoint[];
  indicatorData: IndicatorDataPoint[];
  correlation: CorrelationInfo;
}

/**
 * Dual-axis time series chart showing concentration (left) vs indicator (right).
 * Visualizes the relationship captured in the correlation coefficient.
 */
export function IndustryIndicatorChart({
  concentrationData,
  indicatorData,
  correlation,
}: IndustryIndicatorChartProps) {
  // Merge data by year
  const mergedData = concentrationData.map((conc) => {
    const indPoint = indicatorData.find((i) => i.year === conc.year);
    return {
      year: conc.year,
      cr4: conc.cr4,
      hhi: conc.hhi,
      indicator: indPoint?.value ?? null,
    };
  });

  // Determine correlation color
  const corrColor =
    correlation.relationship === "positive"
      ? "#22c55e"
      : correlation.relationship === "negative"
        ? "#ef4444"
        : "#a3a3a3";

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">
          {correlation.indicator_name}
        </h3>
        <div className="flex items-center gap-4 text-xs">
          <span
            className="flex items-center gap-1 rounded px-2 py-0.5"
            style={{ backgroundColor: `${corrColor}20`, color: corrColor }}
          >
            r = {correlation.correlation.toFixed(2)}
          </span>
          {correlation.lag_months > 0 && (
            <span className="text-muted-foreground">
              Lag: {correlation.lag_months}mo
            </span>
          )}
          <span className="text-muted-foreground">
            Confidence: {correlation.confidence.toFixed(0)}%
          </span>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={mergedData}
            margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="year"
              tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
            />
            <YAxis
              yAxisId="left"
              tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
              label={{
                value: "CR4 (%)",
                angle: -90,
                position: "insideLeft",
                fill: "var(--muted-foreground)",
                fontSize: 10,
              }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
              label={{
                value: correlation.indicator_name,
                angle: 90,
                position: "insideRight",
                fill: "var(--muted-foreground)",
                fontSize: 10,
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
              dot={false}
              name="CR4"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="indicator"
              stroke={corrColor}
              strokeWidth={2}
              dot={false}
              name={correlation.indicator_name}
              connectNulls
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
