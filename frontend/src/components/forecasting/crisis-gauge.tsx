"use client";

import { useMemo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { CrisisIndex } from "@/lib/forecast-api";

interface CrisisGaugeProps {
  data: CrisisIndex | null;
  loading?: boolean;
  regimeLabel?: string;
}

/**
 * Crisis index visualization with color-coded severity gauge.
 *
 * Shows:
 * - Horizontal progress bar with composite index (0-100)
 * - Color gradient: green (0-33), yellow (34-66), red (67-100)
 * - Three smaller bars for TRPF/realization/financial components
 * - 6-month sparkline of history
 */
export function CrisisGauge({ data, loading, regimeLabel }: CrisisGaugeProps) {
  // Prepare sparkline data (last 6 months)
  const sparklineData = useMemo(() => {
    if (!data?.history) return [];
    return data.history.slice(-24).map((h) => ({
      date: h.date as string,
      value: h.composite as number,
    }));
  }, [data?.history]);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Crisis Index</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-8 w-full" />
          <div className="grid grid-cols-3 gap-4">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
          </div>
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Crisis Index</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No crisis index data available. Run training first.
          </p>
        </CardContent>
      </Card>
    );
  }

  const compositeValue = data.current_value;

  // Determine color based on severity
  function getSeverityColor(value: number): string {
    if (value <= 33) return "hsl(142 76% 36%)"; // green
    if (value <= 66) return "hsl(48 96% 53%)"; // yellow
    return "hsl(0 84% 60%)"; // red
  }

  function getSeverityBg(value: number): string {
    if (value <= 33) return "bg-emerald-500/20";
    if (value <= 66) return "bg-yellow-500/20";
    return "bg-red-500/20";
  }

  const severityColor = getSeverityColor(compositeValue);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle>Crisis Index</CardTitle>
        {regimeLabel && (
          <Badge variant="outline" className="text-xs">
            {regimeLabel}
          </Badge>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Main composite index bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold tabular-nums">
              {compositeValue.toFixed(1)}
            </span>
            <span className="text-sm text-muted-foreground">/ 100</span>
          </div>
          <div className="relative h-6 w-full overflow-hidden rounded-full bg-muted">
            {/* Gradient background */}
            <div
              className="absolute inset-0"
              style={{
                background:
                  "linear-gradient(to right, hsl(142 76% 36% / 0.3), hsl(48 96% 53% / 0.3), hsl(0 84% 60% / 0.3))",
              }}
            />
            {/* Value bar */}
            <div
              className="absolute left-0 top-0 h-full transition-all duration-500"
              style={{
                width: `${Math.min(compositeValue, 100)}%`,
                backgroundColor: severityColor,
              }}
            />
          </div>
        </div>

        {/* Component breakdown */}
        <div className="grid grid-cols-3 gap-4">
          <ComponentBar
            label="TRPF"
            value={data.trpf_component}
            color="var(--chart-1)"
          />
          <ComponentBar
            label="Realization"
            value={data.realization_component}
            color="var(--chart-2)"
          />
          <ComponentBar
            label="Financial"
            value={data.financial_component}
            color="var(--chart-3)"
          />
        </div>

        {/* Sparkline history */}
        {sparklineData.length > 0 && (
          <div className="h-24">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={sparklineData}>
                <defs>
                  <linearGradient id="crisisGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop
                      offset="0%"
                      stopColor={severityColor}
                      stopOpacity={0.4}
                    />
                    <stop
                      offset="100%"
                      stopColor={severityColor}
                      stopOpacity={0.05}
                    />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" hide />
                <YAxis domain={[0, 100]} hide />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--card)",
                    border: "1px solid var(--border)",
                    borderRadius: "0.5rem",
                    color: "var(--card-foreground)",
                    fontSize: 12,
                  }}
                  labelFormatter={(label) => `Date: ${label}`}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke={severityColor}
                  strokeWidth={2}
                  fill="url(#crisisGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ComponentBar({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">{label}</span>
        <span className="text-xs font-medium tabular-nums">
          {value.toFixed(1)}
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full transition-all duration-300"
          style={{
            width: `${Math.min(value, 100)}%`,
            backgroundColor: color,
          }}
        />
      </div>
    </div>
  );
}
