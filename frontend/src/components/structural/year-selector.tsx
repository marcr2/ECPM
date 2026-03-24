"use client";

import { cn } from "@/lib/utils";

interface YearSelectorProps {
  years: number[];
  selected: number;
  onChange: (year: number) => void;
  className?: string;
}

/**
 * Year selector dropdown for I-O table years.
 * BEA benchmark I-O tables are published for years like 1997, 2002, 2007, 2012, 2017, 2022.
 */
export function YearSelector({
  years,
  selected,
  onChange,
  className,
}: YearSelectorProps) {
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
        value={selected}
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
