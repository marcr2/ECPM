"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { ChevronDown } from "lucide-react";
import type { ProportionalityCheck } from "@/lib/structural-api";

interface ProportionalityBadgeProps {
  proportionality: ProportionalityCheck;
}

/**
 * Badge showing Marx's reproduction proportionality condition status.
 *
 * Simple reproduction condition: I(v+s) = II(c)
 * - Green "Balanced" if condition_met is true
 * - Red "Imbalanced" if condition_met is false
 *
 * Expandable section shows formula, values, and deviation.
 */
export function ProportionalityBadge({
  proportionality,
}: ProportionalityBadgeProps) {
  const [expanded, setExpanded] = useState(false);

  const isBalanced = proportionality.condition_met;
  const deviation =
    proportionality.i_v_plus_s > 0
      ? ((proportionality.ii_c - proportionality.i_v_plus_s) /
          proportionality.i_v_plus_s) *
        100
      : 0;

  return (
    <div className="rounded-lg border border-border bg-muted/30 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Badge
            variant={isBalanced ? "default" : "destructive"}
            className={isBalanced ? "bg-green-500/20 text-green-500" : ""}
          >
            {isBalanced ? "Balanced" : "Imbalanced"}
          </Badge>
          <span className="text-sm text-muted-foreground">
            {proportionality.simple_reproduction_holds
              ? "Simple reproduction conditions met"
              : proportionality.expanded_reproduction_holds
              ? "Expanded reproduction conditions met"
              : "Reproduction disequilibrium detected"}
          </span>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          Details
          <ChevronDown
            className={`h-3.5 w-3.5 transition-transform ${
              expanded ? "rotate-180" : ""
            }`}
          />
        </button>
      </div>

      {expanded && (
        <div className="mt-4 space-y-3 border-t border-border pt-4">
          {/* Formula display */}
          <div className="rounded-md bg-muted/50 px-3 py-2 font-mono text-sm">
            {proportionality.formula_display}
          </div>

          {/* Values comparison */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-muted-foreground mb-1">I(v + s)</p>
              <p className="text-lg font-bold tabular-nums">
                {proportionality.i_v_plus_s.toLocaleString(undefined, {
                  maximumFractionDigits: 0,
                })}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">II(c)</p>
              <p className="text-lg font-bold tabular-nums">
                {proportionality.ii_c.toLocaleString(undefined, {
                  maximumFractionDigits: 0,
                })}
              </p>
            </div>
          </div>

          {/* Deviation */}
          {!isBalanced && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Deviation</span>
              <span
                className={`font-medium ${
                  deviation > 0 ? "text-red-500" : "text-green-500"
                }`}
              >
                {deviation > 0 ? "+" : ""}
                {deviation.toFixed(1)}%
              </span>
            </div>
          )}

          {/* Surplus ratio if available */}
          {proportionality.surplus_ratio != null && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Surplus Ratio</span>
              <span className="font-medium">
                {proportionality.surplus_ratio.toFixed(2)}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
