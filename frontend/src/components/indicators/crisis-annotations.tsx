"use client";

import { ReferenceArea, ReferenceLine } from "recharts";
import type { CrisisEpisode } from "@/lib/crisis-episodes";

interface CrisisAnnotationsProps {
  crises: CrisisEpisode[];
  visible: "shaded" | "lines" | "hidden";
}

/**
 * Renders crisis episode annotations inside a Recharts ComposedChart.
 *
 * - "shaded": translucent ReferenceArea regions spanning crisis duration
 * - "lines": dashed vertical ReferenceLine at start and end of each crisis
 * - "hidden": renders nothing
 */
export function CrisisAnnotations({
  crises,
  visible,
}: CrisisAnnotationsProps) {
  if (visible === "hidden") return null;

  if (visible === "lines") {
    return crises.flatMap((crisis) => [
      <ReferenceLine
        key={`${crisis.name}-start`}
        x={crisis.startDate}
        stroke={crisis.color}
        strokeDasharray="4 4"
        strokeOpacity={0.7}
        label={{
          value: crisis.name,
          position: "top",
          fontSize: 10,
          fill: crisis.color,
        }}
      />,
      <ReferenceLine
        key={`${crisis.name}-end`}
        x={crisis.endDate}
        stroke={crisis.color}
        strokeDasharray="4 4"
        strokeOpacity={0.7}
      />,
    ]);
  }

  // Default: "shaded"
  return crises.map((crisis) => (
    <ReferenceArea
      key={crisis.name}
      x1={crisis.startDate}
      x2={crisis.endDate}
      fill={crisis.color}
      fillOpacity={0.15}
      stroke={crisis.color}
      strokeOpacity={0.3}
      label={{
        value: crisis.name,
        position: "top",
        fontSize: 10,
        fill: "hsl(var(--muted-foreground))",
      }}
    />
  ));
}
