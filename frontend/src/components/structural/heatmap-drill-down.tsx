"use client";

import { Dialog } from "@base-ui/react/dialog";
import { X, ArrowRight, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getSectorName } from "@/lib/bea-sector-names";

interface HeatmapDrillDownProps {
  open: boolean;
  onClose: () => void;
  rowCode: string;
  colCode: string;
  value: number;
  rowLabel?: string;
  colLabel?: string;
}

function CoefficientBadge({ value }: { value: number }) {
  const abs = Math.abs(value);
  if (abs >= 0.1)
    return (
      <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium text-[#b4e0b4]" style={{ backgroundColor: "rgba(26,58,26,0.35)" }}>
        <TrendingUp className="h-3 w-3" /> High
      </span>
    );
  if (abs >= 0.05)
    return (
      <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium text-[#90c090]" style={{ backgroundColor: "rgba(78,128,78,0.25)" }}>
        <TrendingUp className="h-3 w-3" /> Moderate
      </span>
    );
  if (abs >= 0.01)
    return (
      <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium text-[#a0c8a0]" style={{ backgroundColor: "rgba(106,154,106,0.2)" }}>
        <TrendingDown className="h-3 w-3" /> Low
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium text-muted-foreground">
      <Minus className="h-3 w-3" /> Negligible
    </span>
  );
}

/**
 * Side panel drill-down for I-O matrix cell details.
 * Shows full industry names, coefficient value, interpretation, and context.
 */
export function HeatmapDrillDown({
  open,
  onClose,
  rowCode,
  colCode,
  value,
  rowLabel,
  colLabel,
}: HeatmapDrillDownProps) {
  if (!open) return null;

  const rowName = rowLabel ?? getSectorName(rowCode);
  const colName = colLabel ?? getSectorName(colCode);
  const isDiagonal = rowCode === colCode;
  const abs = Math.abs(value);
  const percentOfOutput = (abs * 100).toFixed(2);

  return (
    <Dialog.Root open={open} onOpenChange={(o) => !o && onClose()}>
      <Dialog.Portal>
        <Dialog.Backdrop className="fixed inset-0 bg-black/50 backdrop-blur-sm data-[ending-style]:opacity-0 data-[starting-style]:opacity-0" />
        <Dialog.Popup className="fixed right-0 top-0 h-full w-full max-w-lg border-l border-border bg-card p-6 shadow-lg data-[ending-style]:translate-x-full data-[starting-style]:translate-x-full transition-transform duration-200 overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <Dialog.Title className="text-lg font-semibold">
              Coefficient Detail
            </Dialog.Title>
            <Dialog.Close
              render={
                <Button variant="ghost" size="icon-sm" onClick={onClose}>
                  <X className="h-4 w-4" />
                </Button>
              }
            />
          </div>

          <div className="space-y-6">
            {/* Flow direction visual */}
            <div className="flex items-center gap-3 rounded-lg border border-border bg-muted/30 p-4">
              <div className="flex-1 text-center">
                <div className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground mb-1">
                  Input supplier
                </div>
                <div className="text-sm font-semibold">{rowName}</div>
                <div className="font-mono text-xs text-muted-foreground mt-0.5">
                  {rowCode}
                </div>
              </div>
              <ArrowRight className="h-5 w-5 flex-shrink-0 text-muted-foreground" />
              <div className="flex-1 text-center">
                <div className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground mb-1">
                  Consuming industry
                </div>
                <div className="text-sm font-semibold">{colName}</div>
                <div className="font-mono text-xs text-muted-foreground mt-0.5">
                  {colCode}
                </div>
              </div>
            </div>

            {/* Coefficient value */}
            <div className="rounded-lg border border-border bg-muted/30 p-4">
              <div className="flex items-start justify-between gap-4 mb-3">
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-1">
                    Technical Coefficient
                  </h3>
                  <p className="text-3xl font-bold tabular-nums">
                    {value.toFixed(6)}
                  </p>
                </div>
                <CoefficientBadge value={value} />
              </div>
              <p className="text-sm text-muted-foreground">
                This equals{" "}
                <span className="font-mono font-medium text-foreground">
                  {percentOfOutput}%
                </span>{" "}
                of the consuming industry&apos;s output.
              </p>
            </div>

            {/* Plain-language interpretation */}
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-muted-foreground">
                What this means
              </h3>
              <div className="rounded-lg border border-border p-4 text-sm leading-relaxed">
                {isDiagonal ? (
                  <p>
                    <span className="font-medium">{rowName}</span> recirculates
                    its own output as an input. For every dollar of output, it
                    requires{" "}
                    <span className="font-mono font-medium">
                      ${value.toFixed(4)}
                    </span>{" "}
                    of its own product as an intermediate input. This
                    intra-industry flow reflects internal supply chains and
                    self-consumption within the sector.
                  </p>
                ) : (
                  <p>
                    For every{" "}
                    <span className="font-medium">$1.00 of output</span> by{" "}
                    <span className="font-medium">{colName}</span>, it directly
                    purchases{" "}
                    <span className="font-mono font-medium">
                      ${value.toFixed(4)}
                    </span>{" "}
                    worth of goods/services from{" "}
                    <span className="font-medium">{rowName}</span>. This
                    captures only the <em>direct</em> input requirement
                    &mdash; indirect requirements through supply chains are
                    captured in the Leontief inverse.
                  </p>
                )}
              </div>
            </div>

            {/* Scale context */}
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-muted-foreground">
                Scale reference
              </h3>
              <div className="space-y-1.5 text-xs text-muted-foreground">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <span className="inline-block h-2 w-2 rounded-full bg-[#1a3a1a]" />
                    High dependency (&ge; 0.10)
                  </span>
                  <span>Strong supply-chain coupling</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <span className="inline-block h-2 w-2 rounded-full bg-[#4e804e]" />
                    Moderate (0.05 &ndash; 0.10)
                  </span>
                  <span>Notable input requirement</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <span className="inline-block h-2 w-2 rounded-full bg-[#90c090]" />
                    Low (0.01 &ndash; 0.05)
                  </span>
                  <span>Weak but present linkage</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <span className="inline-block h-2 w-2 rounded-full bg-white border border-border" />
                    Negligible (&lt; 0.01)
                  </span>
                  <span>Minimal or no direct linkage</span>
                </div>
              </div>
            </div>

            {/* Methodology note */}
            <div className="rounded-lg bg-muted/20 px-4 py-3 text-xs leading-relaxed text-muted-foreground">
              <p className="font-medium mb-1">About technical coefficients</p>
              <p>
                Technical coefficients (matrix A) are derived from BEA
                Input-Output Use tables by dividing each intermediate input
                flow Z<sub>ij</sub> by total industry output X<sub>j</sub>.
                They represent the economy&apos;s direct production
                technology. The full Leontief inverse L = (I - A)<sup>-1</sup>{" "}
                captures both direct and indirect requirements across all
                supply-chain tiers.
              </p>
            </div>
          </div>
        </Dialog.Popup>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
