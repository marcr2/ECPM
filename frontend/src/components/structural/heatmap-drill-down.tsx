"use client";

import { Dialog } from "@base-ui/react/dialog";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HeatmapDrillDownProps {
  open: boolean;
  onClose: () => void;
  rowCode: string;
  colCode: string;
  value: number;
  rowLabel?: string;
  colLabel?: string;
}

/**
 * Side panel drill-down for I-O matrix cell details.
 * Shows industry/commodity names and coefficient value.
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

  return (
    <Dialog.Root open={open} onOpenChange={(o) => !o && onClose()}>
      <Dialog.Portal>
        <Dialog.Backdrop className="fixed inset-0 bg-black/50 backdrop-blur-sm data-[ending-style]:opacity-0 data-[starting-style]:opacity-0" />
        <Dialog.Popup className="fixed right-0 top-0 h-full w-full max-w-md border-l border-border bg-card p-6 shadow-lg data-[ending-style]:translate-x-full data-[starting-style]:translate-x-full transition-transform duration-200">
          <div className="flex items-center justify-between mb-6">
            <Dialog.Title className="text-lg font-semibold">
              Cell Details
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
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-1">
                Row Industry
              </h3>
              <p className="text-base font-medium">{rowLabel || rowCode}</p>
              <p className="text-xs text-muted-foreground">Code: {rowCode}</p>
            </div>

            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-1">
                Column Commodity
              </h3>
              <p className="text-base font-medium">{colLabel || colCode}</p>
              <p className="text-xs text-muted-foreground">Code: {colCode}</p>
            </div>

            <div className="rounded-lg border border-border bg-muted/30 p-4">
              <h3 className="text-sm font-medium text-muted-foreground mb-1">
                Technical Coefficient
              </h3>
              <p className="text-2xl font-bold tabular-nums">
                {value.toFixed(6)}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Amount of {colCode} required per unit of {rowCode} output
              </p>
            </div>

            <div className="text-xs text-muted-foreground">
              <p>
                The technical coefficient represents the direct input
                requirements between industries in the I-O system.
              </p>
            </div>
          </div>
        </Dialog.Popup>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
