"use client";

import { useMemo, useState } from "react";
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Legend,
  Brush,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { IndicatorForecast } from "@/lib/forecast-api";

interface ForecastChartProps {
  data: IndicatorForecast;
  historicalData?: Array<{ date: string; value: number }>;
  title?: string;
}

const HORIZON_OPTIONS = [6, 12, 18, 24];

/**
 * Forecast chart with historical data and confidence intervals.
 *
 * Features:
 * - Solid line for historical data
 * - Dashed line for forecast point estimates
 * - Shaded areas for 68% and 95% confidence intervals
 * - Horizon dropdown to filter forecast length
 */
export function ForecastChart({
  data,
  historicalData = [],
  title,
}: ForecastChartProps) {
  const [selectedHorizon, setSelectedHorizon] = useState(
    data.horizon_quarters || 8
  );

  // Combine historical and forecast data
  const chartData = useMemo(() => {
    // Historical data points
    const historical = historicalData.map((d) => ({
      date: d.date,
      historical: d.value,
      forecast: null as number | null,
      lower_68: null as number | null,
      upper_68: null as number | null,
      lower_95: null as number | null,
      upper_95: null as number | null,
    }));

    // Filter forecasts to selected horizon
    const filteredForecasts = data.forecasts.slice(0, selectedHorizon);

    // Forecast data points
    const forecasts = filteredForecasts.map((f) => ({
      date: f.date,
      historical: null as number | null,
      forecast: f.point,
      lower_68: f.lower_68,
      upper_68: f.upper_68,
      lower_95: f.lower_95,
      upper_95: f.upper_95,
    }));

    // Connect historical to forecast with last historical value
    if (historical.length > 0 && forecasts.length > 0) {
      const lastHistorical = historical[historical.length - 1];
      forecasts[0] = {
        ...forecasts[0],
        historical: lastHistorical.historical,
      };
    }

    return [...historical, ...forecasts];
  }, [historicalData, data.forecasts, selectedHorizon]);

  // Calculate CI ranges for area chart
  const ciData = useMemo(() => {
    return chartData.map((d) => ({
      ...d,
      ci95: d.lower_95 !== null && d.upper_95 !== null
        ? [d.lower_95, d.upper_95] as [number, number]
        : null,
      ci68: d.lower_68 !== null && d.upper_68 !== null
        ? [d.lower_68, d.upper_68] as [number, number]
        : null,
    }));
  }, [chartData]);

  function formatDateTick(value: string): string {
    if (!value) return "";
    return value.slice(0, 4); // Year only
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle>{title || data.indicator}</CardTitle>
        <div className="flex gap-1">
          {HORIZON_OPTIONS.map((h) => (
            <Button
              key={h}
              variant={selectedHorizon === h ? "default" : "outline"}
              size="xs"
              onClick={() => setSelectedHorizon(h)}
            >
              {h}Q
            </Button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={350}>
          <ComposedChart data={ciData}>
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
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickLine={false}
            />
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

            {/* 95% CI area (wider, lighter) */}
            <Area
              type="monotone"
              dataKey="ci95"
              stroke="none"
              fill="hsl(var(--chart-4))"
              fillOpacity={0.2}
              name="95% CI"
              connectNulls={false}
            />

            {/* 68% CI area (narrower, darker) */}
            <Area
              type="monotone"
              dataKey="ci68"
              stroke="none"
              fill="hsl(var(--chart-3))"
              fillOpacity={0.3}
              name="68% CI"
              connectNulls={false}
            />

            {/* Historical data line (solid) */}
            <Line
              type="monotone"
              dataKey="historical"
              name="Historical"
              stroke="hsl(var(--chart-1))"
              strokeWidth={2}
              dot={false}
              connectNulls
            />

            {/* Forecast line (dashed) */}
            <Line
              type="monotone"
              dataKey="forecast"
              name="Forecast"
              stroke="hsl(var(--chart-2))"
              strokeWidth={2}
              strokeDasharray="5 3"
              dot={false}
              connectNulls
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

        {/* Model info */}
        {data.model_info && (
          <div className="mt-4 flex gap-4 text-xs text-muted-foreground">
            {data.model_info.lag_order !== undefined && (
              <span>Lag order: {String(data.model_info.lag_order)}</span>
            )}
            {data.model_info.aic !== undefined && (
              <span>AIC: {Number(data.model_info.aic).toFixed(2)}</span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
