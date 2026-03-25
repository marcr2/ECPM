"use client";

import { cn } from "@/lib/utils";

interface YearSelectorProps {
  years: number[];
  /** Must be one of `years` when `years.length > 0`. */
  selected: number | null;
  onChange: (year: number) => void;
  className?: string;
  /** Shown when there are no years (e.g. no I-O data ingested yet). */
  emptyLabel?: string;
}

/**
 * Year selector for years returned by the API (stored coefficient I-O tables only).
 */
export function YearSelector({
  years,
  selected,
  onChange,
  className,
  emptyLabel = "No I-O data loaded",
}: YearSelectorProps) {
  if (years.length === 0) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <span className="text-sm font-medium text-muted-foreground">Year</span>
        <span className="text-sm text-muted-foreground">{emptyLabel}</span>
      </div>
    );
  }

  const value = selected !== null && years.includes(selected) ? selected : years[0];

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <label
        htmlFor="year-select"
        className="text-sm font-medium text-muted-foreground"
      >
        Year
      </label>
      <select
        id="year-select"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-8 min-w-[100px] rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none transition-colors focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 dark:bg-input/30"
      >
        {years.map((year) => (
          <option key={year} value={year} className="bg-background">
            {year}
          </option>
        ))}
      </select>
    </div>
  );
}
