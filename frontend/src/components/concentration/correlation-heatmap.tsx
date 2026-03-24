"use client";

import { useMemo, useState } from "react";
import type { TopCorrelationItem } from "@/lib/concentration-api";
import { Slider } from "@/components/ui/slider";

interface CorrelationHeatmapProps {
  correlations: TopCorrelationItem[];
  minConfidence: number;
  onCellClick: (naics: string, indicatorSlug: string) => void;
}

// Indicator labels for display
const INDICATOR_LABELS: Record<string, string> = {
  "rate-of-profit": "RoP",
  "occ": "OCC",
  "rate-of-surplus-value": "RSV",
  "mass-of-profit": "MoP",
  "productivity-wage-gap": "PWG",
  "credit-gdp-gap": "CGG",
  "financial-real-ratio": "FRR",
  "debt-service-ratio": "DSR",
};

/**
 * 2D heatmap showing correlation between industries and indicators.
 * Color: diverging red-white-blue for correlation (-1 to +1).
 */
export function CorrelationHeatmap({
  correlations,
  minConfidence,
  onCellClick,
}: CorrelationHeatmapProps) {
  const [confidenceFilter, setConfidenceFilter] = useState(minConfidence);

  // Filter correlations by confidence
  const filteredCorrelations = useMemo(
    () => correlations.filter((c) => c.confidence >= confidenceFilter),
    [correlations, confidenceFilter]
  );

  // Build unique industries and indicators
  const industries = useMemo(
    () => [...new Set(filteredCorrelations.map((c) => c.naics))],
    [filteredCorrelations]
  );

  const indicators = Object.keys(INDICATOR_LABELS);

  // Build lookup map
  const correlationMap = useMemo(() => {
    const map = new Map<string, TopCorrelationItem>();
    filteredCorrelations.forEach((c) => {
      map.set(`${c.naics}:${c.indicator_slug}`, c);
    });
    return map;
  }, [filteredCorrelations]);

  if (correlations.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border border-border bg-card">
        <p className="text-muted-foreground">
          No correlation data available. Run data ingestion first.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">
          Concentration-Indicator Correlations
        </h3>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>Min confidence:</span>
          <Slider
            className="w-24"
            value={[confidenceFilter]}
            onValueChange={([v]) => setConfidenceFilter(v)}
            min={0}
            max={100}
            step={5}
          />
          <span>{confidenceFilter}%</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <div className="inline-block min-w-full">
          {/* Header row */}
          <div className="flex">
            <div className="w-32 shrink-0" />
            {indicators.map((ind) => (
              <div
                key={ind}
                className="w-12 shrink-0 text-center text-xs font-medium text-muted-foreground"
                title={ind}
              >
                {INDICATOR_LABELS[ind]}
              </div>
            ))}
          </div>

          {/* Data rows */}
          {industries.slice(0, 15).map((naics) => {
            const industryCorr = filteredCorrelations.find((c) => c.naics === naics);
            const industryName = industryCorr?.industry || naics;

            return (
              <div key={naics} className="flex items-center">
                <div
                  className="w-32 shrink-0 truncate pr-2 text-xs text-foreground"
                  title={industryName}
                >
                  {industryName.length > 15
                    ? industryName.slice(0, 12) + "..."
                    : industryName}
                </div>
                {indicators.map((ind) => {
                  const corr = correlationMap.get(`${naics}:${ind}`);
                  const value = corr?.correlation ?? 0;
                  const confidence = corr?.confidence ?? 0;

                  return (
                    <div
                      key={`${naics}:${ind}`}
                      className="h-8 w-12 shrink-0 cursor-pointer border border-border/50 transition-colors hover:border-foreground"
                      style={{ backgroundColor: getCorrelationColor(value) }}
                      onClick={() => onCellClick(naics, ind)}
                      title={`${industryName} x ${ind}\nCorrelation: ${value.toFixed(2)}\nConfidence: ${confidence.toFixed(0)}%`}
                    />
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
        <span>-1</span>
        <div
          className="h-3 w-32"
          style={{
            background: "linear-gradient(to right, #ef4444, #ffffff, #3b82f6)",
          }}
        />
        <span>+1</span>
      </div>
    </div>
  );
}

/**
 * Get diverging color for correlation coefficient.
 * Red (-1) -> White (0) -> Blue (+1)
 */
function getCorrelationColor(correlation: number): string {
  // Clamp to [-1, 1]
  const c = Math.max(-1, Math.min(1, correlation));

  if (c < 0) {
    // Red gradient
    const intensity = Math.abs(c);
    const r = 239;
    const g = Math.round(68 + (1 - intensity) * (255 - 68));
    const b = Math.round(68 + (1 - intensity) * (255 - 68));
    return `rgb(${r}, ${g}, ${b})`;
  } else if (c > 0) {
    // Blue gradient
    const intensity = c;
    const r = Math.round(255 - intensity * (255 - 59));
    const g = Math.round(255 - intensity * (255 - 130));
    const b = 246;
    return `rgb(${r}, ${g}, ${b})`;
  }

  return "#ffffff";
}
