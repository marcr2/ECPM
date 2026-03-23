"use client";

import { Button } from "@/components/ui/button";

interface DateRangeControlsProps {
  onRangeChange: (years: number | null) => void;
  activeRange: number | null;
}

const PRESETS: { label: string; years: number | null }[] = [
  { label: "5Y", years: 5 },
  { label: "10Y", years: 10 },
  { label: "25Y", years: 25 },
  { label: "50Y", years: 50 },
  { label: "All", years: null },
];

/**
 * Preset date range buttons for filtering chart data.
 * null = show all data (no range limit).
 */
export function DateRangeControls({
  onRangeChange,
  activeRange,
}: DateRangeControlsProps) {
  return (
    <div className="flex items-center gap-1">
      {PRESETS.map(({ label, years }) => (
        <Button
          key={label}
          variant={activeRange === years ? "default" : "outline"}
          size="xs"
          onClick={() => onRangeChange(years)}
        >
          {label}
        </Button>
      ))}
    </div>
  );
}
