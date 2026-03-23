"use client";

import { INDICATOR_DEFS } from "@/lib/indicator-defs";

interface OverlaySelectorProps {
  currentSlug: string;
  onOverlayChange: (slug: string | null) => void;
  activeOverlay: string | null;
}

/**
 * "Add overlay" dropdown for selecting a second indicator to overlay
 * on the chart with a dual y-axis. Shows all indicators except the
 * currently displayed one. When an overlay is active, shows a "Remove
 * overlay" option.
 */
export function OverlaySelector({
  currentSlug,
  onOverlayChange,
  activeOverlay,
}: OverlaySelectorProps) {
  const options = INDICATOR_DEFS.filter((d) => d.slug !== currentSlug);

  return (
    <select
      value={activeOverlay ?? ""}
      onChange={(e) => {
        const value = e.target.value;
        onOverlayChange(value === "" ? null : value);
      }}
      className="h-7 rounded-md border border-border bg-background px-2 text-xs text-foreground outline-none focus:ring-1 focus:ring-ring"
    >
      <option value="">
        {activeOverlay ? "Remove overlay" : "Add overlay..."}
      </option>
      {options.map((indicator) => (
        <option key={indicator.slug} value={indicator.slug}>
          {indicator.name}
        </option>
      ))}
    </select>
  );
}
