"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ConfidenceBreakdownProps {
  correlation: number;
  sampleSize: number;
  rSquared: number;
  confidence: number;
}

/**
 * Card showing breakdown of confidence score components.
 * Visualizes each factor's contribution to the overall score.
 */
export function ConfidenceBreakdown({
  correlation,
  sampleSize,
  rSquared,
  confidence,
}: ConfidenceBreakdownProps) {
  // Calculate component contributions
  const corrContribution = Math.abs(correlation) * 100;
  const sizeContribution = Math.sqrt(sampleSize / 24) * 100;
  const r2Contribution = rSquared * 100;

  // Determine confidence level label
  const getConfidenceLabel = (conf: number): { label: string; color: string } => {
    if (conf >= 70) return { label: "High", color: "text-green-500 bg-green-500/10" };
    if (conf >= 30) return { label: "Medium", color: "text-yellow-500 bg-yellow-500/10" };
    return { label: "Low", color: "text-red-500 bg-red-500/10" };
  };

  const { label, color } = getConfidenceLabel(confidence);

  return (
    <Card className="border-border bg-card">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">Confidence Breakdown</CardTitle>
          <span className={`rounded px-2 py-0.5 text-xs font-medium ${color}`}>
            {label} Confidence
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Overall score */}
        <div className="flex items-center justify-between">
          <span className="text-2xl font-bold text-foreground">
            {confidence.toFixed(0)}
          </span>
          <span className="text-sm text-muted-foreground">/ 100</span>
        </div>

        {/* Component bars */}
        <div className="space-y-3">
          <ComponentBar
            label="Correlation Strength"
            value={Math.abs(correlation)}
            displayValue={`|r| = ${Math.abs(correlation).toFixed(2)}`}
            contribution={corrContribution}
          />
          <ComponentBar
            label="Sample Size"
            value={Math.min(1, Math.sqrt(sampleSize / 24))}
            displayValue={`n = ${sampleSize}`}
            contribution={sizeContribution}
          />
          <ComponentBar
            label="R-squared"
            value={rSquared}
            displayValue={`R\u00B2 = ${rSquared.toFixed(2)}`}
            contribution={r2Contribution}
          />
        </div>

        {/* Formula */}
        <div className="rounded bg-muted/50 p-2 text-xs text-muted-foreground">
          <span className="font-mono">
            confidence = |r| * 100 * \u221A(n/24) * R\u00B2
          </span>
        </div>

        {/* Interpretation */}
        <div className="text-xs text-muted-foreground">
          {confidence >= 70 && (
            <p>
              Strong, reliable signal. The correlation is statistically robust with
              sufficient data points.
            </p>
          )}
          {confidence >= 30 && confidence < 70 && (
            <p>
              Moderate signal. The relationship exists but may be affected by noise
              or limited data.
            </p>
          )}
          {confidence < 30 && (
            <p>
              Weak signal. Interpret with caution - the relationship may be spurious
              or data is insufficient.
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

interface ComponentBarProps {
  label: string;
  value: number;
  displayValue: string;
  contribution: number;
}

function ComponentBar({ label, value, displayValue, contribution }: ComponentBarProps) {
  // Normalize value to 0-1 for bar width
  const width = Math.min(100, Math.max(0, value * 100));

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium text-foreground">{displayValue}</span>
      </div>
      <div className="relative h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="absolute left-0 top-0 h-full rounded-full bg-blue-500 transition-all"
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}
