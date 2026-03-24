"use client";

import { useCallback, useMemo } from "react";
import { HeatMapCanvas } from "@nivo/heatmap";
import type { MatrixResponse } from "@/lib/structural-api";

interface HeatMapDatum {
  x: string;
  y: number;
}

interface HeatMapSerieData {
  id: string;
  data: HeatMapDatum[];
}

interface CoefficientHeatmapProps {
  matrixData: MatrixResponse;
  onCellClick?: (row: string, col: string, value: number) => void;
}

/**
 * I-O coefficient matrix heatmap using Nivo HeatMapCanvas.
 * Uses Canvas renderer for performance with 71x71 matrices.
 *
 * Color scheme: diverging blue-white-red for negative/zero/positive coefficients.
 */
export function CoefficientHeatmap({
  matrixData,
  onCellClick,
}: CoefficientHeatmapProps) {
  // Transform matrix data for Nivo HeatMapCanvas format
  // Nivo 0.99 expects: { id: string, data: { x: string, y: number }[] }[]
  const data: HeatMapSerieData[] = useMemo(() => {
    return matrixData.row_labels.map((rowLabel, rowIndex) => ({
      id: rowLabel,
      data: matrixData.col_labels.map((colLabel, colIndex) => ({
        x: colLabel,
        y: matrixData.matrix[rowIndex]?.[colIndex] ?? 0,
      })),
    }));
  }, [matrixData]);

  // Get min and max values for color scale
  const { minValue, maxValue } = useMemo(() => {
    let min = Infinity;
    let max = -Infinity;
    for (const row of matrixData.matrix) {
      for (const val of row) {
        if (val < min) min = val;
        if (val > max) max = val;
      }
    }
    return { minValue: min, maxValue: max };
  }, [matrixData.matrix]);

  // Determine symmetric bounds for diverging scale
  const bound = Math.max(Math.abs(minValue), Math.abs(maxValue), 0.01);

  const handleCellClick = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (cell: any) => {
      if (onCellClick) {
        const row = String(cell.serieId);
        const col = String(cell.data.x);
        const value = cell.value ?? 0;
        onCellClick(row, col, value);
      }
    },
    [onCellClick]
  );

  return (
    <div className="h-[600px] w-full overflow-x-auto">
      <HeatMapCanvas
        data={data}
        width={1200}
        height={580}
        margin={{ top: 60, right: 60, bottom: 60, left: 100 }}
        valueFormat=">-.4f"
        pixelRatio={1}
        colors={{
          type: "diverging",
          scheme: "red_yellow_blue",
          divergeAt: 0.5,
          minValue: -bound,
          maxValue: bound,
        }}
        emptyColor="#555555"
        borderWidth={0}
        borderColor={{ from: "color", modifiers: [["darker", 0.4]] }}
        enableLabels={false}
        axisTop={{
          tickSize: 0,
          tickPadding: 5,
          tickRotation: -45,
          legend: "",
          legendOffset: 36,
          truncateTickAt: 0,
          format: (value) => {
            const s = String(value);
            return s.length > 6 ? s.slice(0, 6) + "..." : s;
          },
        }}
        axisLeft={{
          tickSize: 0,
          tickPadding: 5,
          tickRotation: 0,
          legend: "",
          legendOffset: -40,
          truncateTickAt: 0,
          format: (value) => {
            const s = String(value);
            return s.length > 10 ? s.slice(0, 10) + "..." : s;
          },
        }}
        hoverTarget="cell"
        tooltip={({ cell }) => (
          <div className="rounded-md border border-border bg-card px-3 py-2 text-sm shadow-lg">
            <div className="font-medium text-card-foreground">
              {String(cell.serieId)} &rarr; {String(cell.data.x)}
            </div>
            <div className="text-muted-foreground">
              Coefficient: {(cell.value ?? 0).toFixed(4)}
            </div>
          </div>
        )}
        onClick={handleCellClick}
        isInteractive={true}
        theme={{
          text: {
            fill: "hsl(var(--muted-foreground))",
            fontSize: 10,
          },
          tooltip: {
            container: {
              background: "hsl(var(--card))",
              color: "hsl(var(--card-foreground))",
              borderRadius: "0.5rem",
            },
          },
        }}
      />
    </div>
  );
}
