"use client";

import { useState } from "react";
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  ReferenceArea,
  ReferenceLine,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CheckCircle, XCircle } from "lucide-react";
import type { BacktestResult } from "@/lib/forecast-api";

interface BacktestTimelineProps {
  backtests: BacktestResult[];
}

/**
 * Backtest timeline visualization for historical crisis episodes.
 *
 * Features:
 * - Horizontal tabs for each crisis episode
 * - LineChart with crisis_index_series
 * - Shaded ReferenceArea for crisis period
 * - ReferenceLine markers at -12mo and -24mo from peak
 * - Badge showing warning success/failure
 */
export function BacktestTimeline({ backtests }: BacktestTimelineProps) {
  const [selectedEpisode, setSelectedEpisode] = useState(0);

  if (!backtests || backtests.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Historical Backtests</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No backtest data available. Run training first.
          </p>
        </CardContent>
      </Card>
    );
  }

  const episode = backtests[selectedEpisode];

  // Calculate warning dates (12 and 24 months before peak)
  const peakDate = new Date(episode.peak_date);
  const warning12Date = new Date(peakDate);
  warning12Date.setMonth(warning12Date.getMonth() - 12);
  const warning24Date = new Date(peakDate);
  warning24Date.setMonth(warning24Date.getMonth() - 24);

  // Format dates for display
  const formatDate = (d: Date) => d.toISOString().slice(0, 10);

  function formatDateTick(value: string): string {
    if (!value) return "";
    return value.slice(0, 7); // YYYY-MM
  }

  const hasAnyWarning = episode.warning_12m === true || episode.warning_24m === true;
  const isInsufficient = episode.peak_value == null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Historical Backtests</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Episode tabs */}
        <div className="flex flex-wrap gap-2">
          {backtests.map((bt, idx) => (
            <Button
              key={bt.episode_name}
              variant={selectedEpisode === idx ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedEpisode(idx)}
            >
              {bt.episode_name}
            </Button>
          ))}
        </div>

        {/* Episode details */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              {episode.start_date} to {episode.end_date}
            </span>
            {episode.peak_value != null ? (
              <span className="text-sm">
                Peak: <strong>{episode.peak_value.toFixed(1)}</strong> on{" "}
                {episode.peak_date}
              </span>
            ) : (
              <span className="text-sm text-muted-foreground italic">
                Insufficient data
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Badge
              variant={episode.warning_24m == null ? "outline" : episode.warning_24m ? "default" : "destructive"}
              className="flex items-center gap-1"
            >
              {episode.warning_24m == null ? (
                <span className="text-muted-foreground">—</span>
              ) : episode.warning_24m ? (
                <CheckCircle className="h-3 w-3" />
              ) : (
                <XCircle className="h-3 w-3" />
              )}
              24mo
            </Badge>
            <Badge
              variant={episode.warning_12m == null ? "outline" : episode.warning_12m ? "default" : "destructive"}
              className="flex items-center gap-1"
            >
              {episode.warning_12m == null ? (
                <span className="text-muted-foreground">—</span>
              ) : episode.warning_12m ? (
                <CheckCircle className="h-3 w-3" />
              ) : (
                <XCircle className="h-3 w-3" />
              )}
              12mo
            </Badge>
          </div>
        </div>

        {/* Crisis index chart */}
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={episode.crisis_index_series}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--border)"
            />
            <XAxis
              dataKey="date"
              tickFormatter={formatDateTick}
              stroke="var(--muted-foreground)"
              fontSize={12}
              tickLine={false}
            />
            <YAxis
              domain={[0, 100]}
              stroke="var(--muted-foreground)"
              fontSize={12}
              tickLine={false}
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

            {/* Crisis period shaded area */}
            <ReferenceArea
              x1={episode.start_date}
              x2={episode.end_date}
              fill="var(--destructive)"
              fillOpacity={0.15}
              stroke="var(--destructive)"
              strokeOpacity={0.3}
            />

            {/* Warning markers */}
            <ReferenceLine
              x={formatDate(warning24Date)}
              stroke="var(--chart-2)"
              strokeDasharray="5 3"
              label={{
                value: "-24mo",
                position: "top",
                fill: "var(--muted-foreground)",
                fontSize: 10,
              }}
            />
            <ReferenceLine
              x={formatDate(warning12Date)}
              stroke="var(--chart-3)"
              strokeDasharray="5 3"
              label={{
                value: "-12mo",
                position: "top",
                fill: "var(--muted-foreground)",
                fontSize: 10,
              }}
            />

            {/* Peak marker */}
            <ReferenceLine
              x={episode.peak_date}
              stroke="var(--destructive)"
              strokeWidth={2}
              label={{
                value: "Peak",
                position: "top",
                fill: "var(--destructive)",
                fontSize: 10,
              }}
            />

            {/* Crisis index line */}
            <Line
              type="monotone"
              dataKey="value"
              name="Crisis Index"
              stroke="var(--chart-1)"
              strokeWidth={2}
              dot={false}
              connectNulls
            />
          </ComposedChart>
        </ResponsiveContainer>

        {/* Summary */}
        <div className="rounded-lg bg-muted/50 p-4 text-sm">
          {isInsufficient ? (
            <p className="text-muted-foreground italic">
              Insufficient historical data to evaluate this episode (data starts after episode period).
            </p>
          ) : hasAnyWarning ? (
            <p className="text-emerald-400">
              Early warning signal detected{" "}
              {episode.warning_24m === true && episode.warning_12m === true
                ? "at both 24 and 12 months"
                : episode.warning_24m === true
                ? "at 24 months"
                : "at 12 months"}{" "}
              before the crisis peak.
            </p>
          ) : (
            <p className="text-red-400">
              No early warning signal detected before this crisis episode.
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
