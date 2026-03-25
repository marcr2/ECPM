"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import type { ShockRequest } from "@/lib/structural-api";
import { SearchableSelect } from "@/components/ui/searchable-select";

interface Industry {
  code: string;
  name: string;
}

interface ShockSimulatorProps {
  industries: Industry[];
  year: number;
  onSimulate: (req: ShockRequest) => Promise<void>;
  loading?: boolean;
}

/**
 * Shock simulation form.
 *
 * Controls:
 * - Industry selector (dropdown with 71 industries)
 * - Magnitude slider (-100% to +100%)
 * - Shock type radio (supply/demand)
 * - Simulate button
 */
export function ShockSimulator({
  industries,
  year,
  onSimulate,
  loading = false,
}: ShockSimulatorProps) {
  const [selectedIndustry, setSelectedIndustry] = useState(
    industries[0]?.code ?? ""
  );
  const [magnitude, setMagnitude] = useState(0);
  const [shockType, setShockType] = useState<"supply" | "demand">("demand");

  const industryOptions = useMemo(
    () =>
      [...industries]
        .sort((a, b) => a.name.localeCompare(b.name))
        .map((ind) => ({
          value: ind.code,
          label: ind.name,
          detail: ind.code,
        })),
    [industries],
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIndustry) return;

    await onSimulate({
      year,
      shocks: { [selectedIndustry]: magnitude / 100 },
      shock_type: shockType,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Industry selector */}
      <div className="space-y-2">
        <label
          htmlFor="industry-select"
          className="text-sm font-medium text-foreground"
        >
          Target Industry
        </label>
        <SearchableSelect
          id="industry-select"
          options={industryOptions}
          value={selectedIndustry}
          onChange={setSelectedIndustry}
          placeholder="Search industries…"
        />
      </div>

      {/* Magnitude slider */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label
            htmlFor="magnitude-slider"
            className="text-sm font-medium text-foreground"
          >
            Shock Magnitude
          </label>
          <span
            className={`text-sm font-bold tabular-nums ${
              magnitude > 0
                ? "text-green-500"
                : magnitude < 0
                ? "text-red-500"
                : "text-muted-foreground"
            }`}
          >
            {magnitude > 0 ? "+" : ""}
            {magnitude}%
          </span>
        </div>
        <input
          id="magnitude-slider"
          type="range"
          min={-100}
          max={100}
          value={magnitude}
          onChange={(e) => setMagnitude(Number(e.target.value))}
          className="w-full cursor-pointer accent-primary"
        />
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>-100%</span>
          <span>0</span>
          <span>+100%</span>
        </div>
      </div>

      {/* Shock type radio */}
      <div className="space-y-2">
        <span className="text-sm font-medium text-foreground">Shock Type</span>
        <div className="flex gap-4">
          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="radio"
              name="shock-type"
              value="demand"
              checked={shockType === "demand"}
              onChange={() => setShockType("demand")}
              className="accent-primary"
            />
            <span className="text-sm">Demand</span>
          </label>
          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="radio"
              name="shock-type"
              value="supply"
              checked={shockType === "supply"}
              onChange={() => setShockType("supply")}
              className="accent-primary"
            />
            <span className="text-sm">Supply</span>
          </label>
        </div>
        <p className="text-xs text-muted-foreground">
          {shockType === "demand"
            ? "Demand shock: Uses Leontief inverse to propagate final demand changes"
            : "Supply shock: Uses Ghosh inverse to propagate input disruptions"}
        </p>
      </div>

      {/* Submit button */}
      <Button
        type="submit"
        disabled={loading || !selectedIndustry}
        className="w-full"
      >
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Simulating...
          </>
        ) : (
          "Simulate Shock"
        )}
      </Button>
    </form>
  );
}
