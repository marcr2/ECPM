"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { IndustryListItem } from "@/lib/concentration-api";

interface ConcentrationCardProps {
  industry: IndustryListItem;
  onClick: () => void;
}

/**
 * Card component showing industry concentration summary.
 * Includes name, CR4, HHI, level badge, and trend indicator.
 */
export function ConcentrationCard({ industry, onClick }: ConcentrationCardProps) {
  return (
    <Card
      className="cursor-pointer border-border bg-card transition-colors hover:border-foreground/20 hover:bg-card/80"
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="line-clamp-2 text-sm font-medium leading-tight">
            {industry.name}
          </CardTitle>
          <LevelBadge level={industry.level} />
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Metrics row */}
        <div className="flex items-baseline justify-between">
          <div>
            <span className="text-2xl font-bold text-foreground">
              {industry.cr4.toFixed(1)}
            </span>
            <span className="ml-1 text-sm text-muted-foreground">% CR4</span>
          </div>
          <div className="text-right">
            <span className="text-lg font-semibold text-foreground">
              {industry.hhi.toFixed(0)}
            </span>
            <span className="ml-1 text-xs text-muted-foreground">HHI</span>
          </div>
        </div>

        {/* Trend and NAICS */}
        <div className="flex items-center justify-between text-xs">
          <TrendIndicator direction={industry.trend_direction} />
          <span className="text-muted-foreground">NAICS: {industry.naics}</span>
        </div>

        {/* Mini sparkline placeholder */}
        <div className="flex h-8 items-end gap-0.5">
          {generateSparkline(industry.hhi).map((h, i) => (
            <div
              key={i}
              className="flex-1 rounded-t bg-blue-500/60 transition-all hover:bg-blue-500"
              style={{ height: `${h}%` }}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function LevelBadge({ level }: { level: string }) {
  const variants: Record<string, { bg: string; text: string; label: string }> = {
    monopoly: {
      bg: "bg-red-500/10",
      text: "text-red-500",
      label: "Monopoly",
    },
    highly_concentrated: {
      bg: "bg-orange-500/10",
      text: "text-orange-500",
      label: "High",
    },
    moderately_concentrated: {
      bg: "bg-yellow-500/10",
      text: "text-yellow-500",
      label: "Moderate",
    },
    competitive: {
      bg: "bg-green-500/10",
      text: "text-green-500",
      label: "Competitive",
    },
  };

  const variant = variants[level] || variants.competitive;

  return (
    <Badge
      variant="outline"
      className={`shrink-0 border-0 ${variant.bg} ${variant.text}`}
    >
      {variant.label}
    </Badge>
  );
}

function TrendIndicator({ direction }: { direction: string }) {
  const config: Record<string, { icon: string; color: string; label: string }> = {
    increasing: { icon: "\u2191", color: "text-red-500", label: "Increasing" },
    decreasing: { icon: "\u2193", color: "text-green-500", label: "Decreasing" },
    stable: { icon: "\u2192", color: "text-yellow-500", label: "Stable" },
  };

  const { icon, color, label } = config[direction] || config.stable;

  return (
    <span className={`inline-flex items-center gap-1 ${color}`}>
      <span>{icon}</span>
      <span>{label}</span>
    </span>
  );
}

/**
 * Generate fake sparkline data based on HHI value.
 * In production, this would use actual historical data.
 */
function generateSparkline(hhi: number): number[] {
  // Generate 8 bars with some variation around the HHI
  const base = (hhi / 10000) * 80 + 10;
  return Array.from({ length: 8 }, (_, i) => {
    const variation = (Math.sin(i * 0.5) + Math.cos(i * 0.3)) * 10;
    return Math.max(10, Math.min(100, base + variation));
  });
}
