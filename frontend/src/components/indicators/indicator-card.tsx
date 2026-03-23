"use client";

import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sparkline } from "./sparkline";
import type { IndicatorSummary } from "@/lib/indicators";
import type { IndicatorDef } from "@/lib/indicator-defs";

interface IndicatorCardProps {
  indicator: IndicatorSummary;
  size: "hero" | "secondary";
  def: IndicatorDef;
}

function formatValue(value: number | null, units: string): string {
  if (value === null) return "N/A";
  if (units === "%" || units === "pp") {
    return `${value.toFixed(2)}${units}`;
  }
  if (units === "billions USD") {
    return `$${value.toFixed(1)}B`;
  }
  if (units === "index") {
    return value.toFixed(2);
  }
  // ratio or other
  return value.toFixed(4);
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", { year: "numeric", month: "short" });
}

function TrendBadge({ trend }: { trend: string | null }) {
  if (!trend) return null;

  const config: Record<string, { label: string; variant: "default" | "secondary" | "outline"; arrow: string }> = {
    rising: { label: "Rising", variant: "default", arrow: "\u2191" },
    falling: { label: "Falling", variant: "secondary", arrow: "\u2193" },
    flat: { label: "Flat", variant: "outline", arrow: "\u2192" },
  };

  const c = config[trend] ?? config.flat!;

  return (
    <Badge variant={c.variant} className="text-[10px]">
      <span>{c.arrow}</span> {c.label}
    </Badge>
  );
}

/**
 * Card component for the indicator overview dashboard.
 *
 * Hero cards (TRPF trio) are larger with prominent sparklines.
 * Secondary cards are compact with smaller text.
 */
export function IndicatorCard({ indicator, size, def }: IndicatorCardProps) {
  const isHero = size === "hero";

  return (
    <Link href={`/indicators/${def.slug}`} className="block">
      <Card
        size={isHero ? "default" : "sm"}
        className="cursor-pointer transition-all hover:ring-2 hover:ring-primary/30"
      >
        <CardHeader>
          <div className="flex items-start justify-between">
            <CardTitle className={isHero ? "text-base" : "text-sm"}>
              {def.name}
            </CardTitle>
            <TrendBadge trend={indicator.trend} />
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex items-baseline gap-1.5">
            <span className={isHero ? "text-2xl font-bold tabular-nums" : "text-lg font-semibold tabular-nums"}>
              {formatValue(indicator.latest_value, def.units)}
            </span>
            {indicator.latest_value !== null && (
              <span className="text-xs text-muted-foreground">{def.units}</span>
            )}
          </div>
          {indicator.latest_date && (
            <p className="text-[10px] text-muted-foreground">
              {formatDate(indicator.latest_date)}
            </p>
          )}
          {indicator.sparkline.length > 0 && (
            <Sparkline
              data={indicator.sparkline}
              height={isHero ? 48 : 32}
            />
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
