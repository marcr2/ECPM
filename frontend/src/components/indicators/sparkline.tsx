"use client";

import { LineChart, Line, ResponsiveContainer } from "recharts";

interface SparklineProps {
  data: number[];
  color?: string;
  height?: number;
}

/**
 * Mini line chart for overview cards. No axes, no tooltip, no grid.
 * Renders a simple trend line from an array of values.
 */
export function Sparkline({
  data,
  color = "var(--primary)",
  height = 40,
}: SparklineProps) {
  const chartData = data.map((value, index) => ({ value, index }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData}>
        <Line
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={1.5}
          dot={false}
          animationDuration={0}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
