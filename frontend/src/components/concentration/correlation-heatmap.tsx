"use client";

import { Fragment, useMemo, useState } from "react";
import type { IndustryListItem, TopCorrelationItem } from "@/lib/concentration-api";
import { Slider } from "@/components/ui/slider";
import {
  coefficientToColor,
  ioHeatmapLegendGradientStops,
} from "@/lib/io-heatmap-colors";

interface CorrelationHeatmapProps {
  correlations: TopCorrelationItem[];
  minConfidence: number;
  onCellClick: (naics: string, indicatorSlug: string) => void;
  /** Rows in display order (e.g. same sort as industry ranking). Defaults to arbitrary order from data. */
  rowIndustries?: IndustryListItem[];
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
 * 2D heatmap: industry concentration vs national crisis indicators.
 * Colors match the structural I/O coefficient heatmap (red negative, green positive).
 */
export function CorrelationHeatmap({
  correlations,
  minConfidence,
  onCellClick,
  rowIndustries,
}: CorrelationHeatmapProps) {
  const [confidenceFilter, setConfidenceFilter] = useState(minConfidence);

  const indicators = Object.keys(INDICATOR_LABELS);

  /** Fixed column widths so header labels line up with every data row. */
  const gridTemplateColumns = useMemo(
    () =>
      `minmax(10rem, 19rem) repeat(${indicators.length}, 3rem)`,
    [indicators.length],
  );

  const correlationMap = useMemo(() => {
    const map = new Map<string, TopCorrelationItem>();
    correlations.forEach((c) => {
      map.set(`${c.naics}:${c.indicator_slug}`, c);
    });
    return map;
  }, [correlations]);

  const displayRows = useMemo((): { naics: string; name: string }[] => {
    if (rowIndustries?.length) {
      return rowIndustries.slice(0, 20).map((r) => ({
        naics: r.naics,
        name: r.name,
      }));
    }
    const seen = new Set<string>();
    const ordered: string[] = [];
    for (const c of correlations) {
      if (!seen.has(c.naics)) {
        seen.add(c.naics);
        ordered.push(c.naics);
      }
    }
    return ordered.slice(0, 20).map((naics) => ({
      naics,
      name: correlations.find((c) => c.naics === naics)?.industry || naics,
    }));
  }, [rowIndustries, correlations]);

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
        <div
          className="mx-auto grid w-max max-w-full min-w-0 px-1"
          style={{ gridTemplateColumns }}
        >
          <div className="min-h-8 pr-2.5" aria-hidden />
          {indicators.map((ind) => (
            <div
              key={`h-${ind}`}
              className="flex h-8 min-w-0 items-end justify-center self-end pb-0.5 text-center text-xs font-medium text-muted-foreground"
              title={ind}
            >
              {INDICATOR_LABELS[ind]}
            </div>
          ))}

          {displayRows.map((row) => {
            const naics = row.naics;
            const industryName = row.name || naics;

            return (
              <Fragment key={naics}>
                <div
                  className="flex min-h-8 min-w-0 items-center truncate pr-2.5 text-left text-xs text-foreground"
                  title={industryName}
                >
                  {industryName}
                </div>
                {indicators.map((ind) => {
                  const corr = correlationMap.get(`${naics}:${ind}`);
                  const passes =
                    corr != null && corr.confidence >= confidenceFilter;
                  const value = corr?.correlation ?? 0;
                  const confidence = corr?.confidence ?? 0;

                  return (
                    <div
                      key={`${naics}:${ind}`}
                      className="h-8 w-full min-w-0 cursor-pointer border border-border/50 transition-colors hover:border-foreground"
                      style={{
                        backgroundColor: passes
                          ? coefficientToColor(value, 1)
                          : "#252525",
                      }}
                      onClick={() => onCellClick(naics, ind)}
                      title={`${industryName} × ${ind}\nCorrelation: ${value.toFixed(2)}\nConfidence: ${confidence.toFixed(0)}%\n${passes ? "" : "(below min confidence)"}`}
                    />
                  );
                })}
              </Fragment>
            );
          })}
        </div>
      </div>

      {/* Legend — same ramp as I/O table; r is Pearson on aligned annual series */}
      <div className="space-y-2 border-t border-border pt-3">
        <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
          <span className="w-6 shrink-0 text-right font-medium text-foreground">
            −1
          </span>
          <div
            className="h-3 w-44 max-w-[min(100%,11rem)] rounded-sm border border-border/60"
            style={{ background: ioHeatmapLegendGradientStops() }}
          />
          <span className="w-6 shrink-0 font-medium text-foreground">+1</span>
        </div>
        <p className="mx-auto max-w-xl text-center text-[11px] leading-snug text-muted-foreground">
          <span className="text-foreground">Pearson correlation (r)</span> between industry
          concentration (CR4) and each national indicator on overlapping years.{" "}
          <span className="text-foreground">−1</span>: when one rises, the other tends to fall;{" "}
          <span className="text-foreground">0</span> (neutral band): little linear co-movement;{" "}
          <span className="text-foreground">+1</span>: they tend to rise and fall together.
          Dark cells are below the confidence slider or missing data.
        </p>
      </div>
    </div>
  );
}
