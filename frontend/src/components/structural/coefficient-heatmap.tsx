"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { HeatMapCanvas } from "@nivo/heatmap";
import { Info } from "lucide-react";
import type { MatrixResponse } from "@/lib/structural-api";
import { getSectorName } from "@/lib/bea-sector-names";
import { resolveIoAxisLabel } from "@/lib/structural-labels";
import {
  SearchableSelect,
  type SearchableOption,
} from "@/components/ui/searchable-select";

// Ends: negative (reds) → near-zero (dim whites / soft neutrals) → positive (greens)
const HEATMAP_COLORS = [
  "#2a0a0a",
  "#421010",
  "#5e1a1a",
  "#864040",
  "#c09090",
  "#c8bcbc",
  "#d1d1d1",
  "#bcc8bc",
  "#90c090",
  "#4e804e",
  "#2f5c2f",
  "#1a3a1a",
] as const;

const DIM_BLEND_BG = "#161616";

/** Neutral “no dependency” only in this band; outside uses full red/green ramps vs `bound`. */
const IO_NEUTRAL_EPS = 0.00001;

function coefficientToColor(
  value: number | null | undefined,
  bound: number,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "#252525";
  }
  if (Math.abs(value) <= IO_NEUTRAL_EPS) {
    return HEATMAP_COLORS[6];
  }
  const b = Math.max(bound, IO_NEUTRAL_EPS * 1.0001);
  const span = b - IO_NEUTRAL_EPS;
  if (value < -IO_NEUTRAL_EPS) {
    const clamped = Math.max(-b, Math.min(-IO_NEUTRAL_EPS, value));
    const t = (clamped + b) / span;
    const idx = Math.min(5, Math.floor(t * 6));
    return HEATMAP_COLORS[idx];
  }
  const clamped = Math.min(b, Math.max(IO_NEUTRAL_EPS, value));
  const t = (clamped - IO_NEUTRAL_EPS) / span;
  const idx = Math.min(11, 7 + Math.floor(t * 5));
  return HEATMAP_COLORS[idx];
}

function blendHex(fg: string, bg: string, bgWeight: number): string {
  const parse = (h: string) => {
    const s = h.slice(1);
    return [
      parseInt(s.slice(0, 2), 16),
      parseInt(s.slice(2, 4), 16),
      parseInt(s.slice(4, 6), 16),
    ];
  };
  const [fr, fgC, fb] = parse(fg);
  const [br, bgC, bb] = parse(bg);
  const w = Math.max(0, Math.min(1, bgWeight));
  const iw = 1 - w;
  const r = Math.round(fr * iw + br * w);
  const g = Math.round(fgC * iw + bgC * w);
  const b = Math.round(fb * iw + bb * w);
  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}

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

function classifyCoefficient(value: number): {
  level: string;
  color: string;
  description: string;
} {
  const abs = Math.abs(value);
  if (abs >= 0.1)
    return {
      level: "High",
      color: "text-[#b4e0b4]",
      description: "Strong direct dependency",
    };
  if (abs >= 0.05)
    return {
      level: "Moderate",
      color: "text-[#90c090]",
      description: "Notable input requirement",
    };
  if (abs >= 0.01)
    return {
      level: "Low",
      color: "text-[#a0c8a0]",
      description: "Weak linkage",
    };
  return {
    level: "Negligible",
    color: "text-muted-foreground",
    description: "Minimal or no direct linkage",
  };
}

const TOOLTIP_W = 320;
const TOOLTIP_H = 250;
const TOOLTIP_PAD = 16;
const TOOLTIP_SAFE = 8;

function TooltipPortal({ children }: { children: React.ReactNode }) {
  const [coords, setCoords] = useState<{ x: number; y: number } | null>(null);
  const rafId = useRef(0);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      cancelAnimationFrame(rafId.current);
      rafId.current = requestAnimationFrame(() => {
        setCoords({ x: e.clientX, y: e.clientY });
      });
    };
    window.addEventListener("mousemove", handler, { passive: true });
    return () => {
      window.removeEventListener("mousemove", handler);
      cancelAnimationFrame(rafId.current);
    };
  }, []);

  if (!coords) return null;

  let x = coords.x + TOOLTIP_PAD;
  let y = coords.y + TOOLTIP_PAD;

  if (x + TOOLTIP_W > window.innerWidth - TOOLTIP_SAFE) {
    x = coords.x - TOOLTIP_W - TOOLTIP_PAD;
  }
  if (y + TOOLTIP_H > window.innerHeight - TOOLTIP_SAFE) {
    y = coords.y - TOOLTIP_H - TOOLTIP_PAD;
  }

  x = Math.max(TOOLTIP_SAFE, Math.min(x, window.innerWidth - TOOLTIP_W - TOOLTIP_SAFE));
  y = Math.max(TOOLTIP_SAFE, Math.min(y, window.innerHeight - TOOLTIP_H - TOOLTIP_SAFE));

  return createPortal(
    <div
      style={{
        position: "fixed",
        left: x,
        top: y,
        zIndex: 9999,
        pointerEvents: "none",
      }}
    >
      {children}
    </div>,
    document.body,
  );
}
function cellMatchesIndustryHighlight(
  cell: { serieId: string; data: { x: string | number } },
  inputCode: string,
  outputCode: string,
): boolean {
  const row = String(cell.serieId);
  const col = String(cell.data.x);
  if (!inputCode && !outputCode) return true;
  if (inputCode && row === inputCode) return true;
  if (outputCode && col === outputCode) return true;
  return false;
}

/** I/O axis titles (HTML only — canvas fill cannot rely on CSS variables) */
const IO_AXIS_TITLE_PX = 17;
/** Narrow strip for vertical “Supplier”; row tick labels stay inside canvas margin.left */
const SUPPLIER_TITLE_STRIP_PX = 28;
/** Baseline Nivo right margin before extra space for rotated column tick labels */
const HEATMAP_MARGIN_RIGHT_BASE_PX = 0;
/** Nivo truncates tick *values* before `format` when 0 < truncateTickAt < len — use a huge cap */
const AXIS_TICK_NO_TRUNCATE = 99999;
/** ~px per character at 11px sans-serif for margin sizing */
const TICK_LABEL_CHAR_PX = 6.6;
/** Cell outline when not filtering — Nivo draws grid *under* opaque cells, so borders/padding carry row/column lines */
const HEATMAP_CELL_GRID_STROKE = "rgba(255,255,255,0.14)";
const HEATMAP_CELL_GRID_STROKE_DIMMED = "rgba(255,255,255,0.08)";
/** Band-scale gap so background shows between cells (scales with zoom better than 1px strokes alone) */
const HEATMAP_INNER_PADDING = 0.02;
/** Must match canvas clear color so inner-padding gaps read as grid, not a different fill */
const HEATMAP_CANVAS_BG = "#161616";

export function CoefficientHeatmap({
  matrixData,
  onCellClick,
}: CoefficientHeatmapProps) {
  const [inputIndustry, setInputIndustry] = useState("");
  const [outputIndustry, setOutputIndustry] = useState("");
  const measureRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(1400);

  const data: HeatMapSerieData[] = useMemo(() => {
    return matrixData.row_labels.map((rowLabel, rowIndex) => ({
      id: rowLabel,
      data: matrixData.col_labels.map((colLabel, colIndex) => ({
        x: colLabel,
        y: matrixData.matrix[rowIndex]?.[colIndex] ?? 0,
      })),
    }));
  }, [matrixData]);

  const { minValue, maxValue, nonZeroCount, meanNonZero, totalCells } =
    useMemo(() => {
      let min = Infinity;
      let max = -Infinity;
      let nz = 0;
      let sum = 0;
      let total = 0;
      for (const row of matrixData.matrix) {
        for (const val of row) {
          total++;
          if (val < min) min = val;
          if (val > max) max = val;
          if (Math.abs(val) > 1e-10) {
            nz++;
            sum += val;
          }
        }
      }
      return {
        minValue: min,
        maxValue: max,
        nonZeroCount: nz,
        meanNonZero: nz > 0 ? sum / nz : 0,
        totalCells: total,
      };
    }, [matrixData.matrix]);

  const bound = Math.max(Math.abs(minValue), Math.abs(maxValue), 0.01);
  const sparsity = ((1 - nonZeroCount / totalCells) * 100).toFixed(1);
  const nRows = matrixData.row_labels.length;
  const nCols = matrixData.col_labels.length;

  const inputOptions: SearchableOption[] = useMemo(() => {
    return [...matrixData.row_labels]
      .filter((code, i, arr) => arr.indexOf(code) === i)
      .map((code) => {
        const label = resolveIoAxisLabel(matrixData, code, "row");
        return {
          value: code,
          label: label !== code ? label : getSectorName(code),
          detail: code,
        };
      })
      .sort((a, b) => a.label.localeCompare(b.label));
  }, [matrixData]);

  const outputOptions: SearchableOption[] = useMemo(() => {
    return [...matrixData.col_labels]
      .filter((code, i, arr) => arr.indexOf(code) === i)
      .map((code) => {
        const label = resolveIoAxisLabel(matrixData, code, "col");
        return {
          value: code,
          label: label !== code ? label : getSectorName(code),
          detail: code,
        };
      })
      .sort((a, b) => a.label.localeCompare(b.label));
  }, [matrixData]);

  const rowAxisTick = useMemo(() => {
    const m = new Map<string, string>();
    for (const code of matrixData.row_labels) {
      m.set(code, resolveIoAxisLabel(matrixData, code, "row"));
    }
    return m;
  }, [matrixData]);

  const colAxisTick = useMemo(() => {
    const m = new Map<string, string>();
    for (const code of matrixData.col_labels) {
      m.set(code, resolveIoAxisLabel(matrixData, code, "col"));
    }
    return m;
  }, [matrixData]);

  const maxRowLabelChars = useMemo(() => {
    let m = 0;
    for (const code of matrixData.row_labels) {
      const label = rowAxisTick.get(code) ?? code;
      if (label.length > m) m = label.length;
    }
    return m;
  }, [matrixData.row_labels, rowAxisTick]);

  const maxColLabelChars = useMemo(() => {
    let m = 0;
    for (const code of matrixData.col_labels) {
      const label = colAxisTick.get(code) ?? code;
      if (label.length > m) m = label.length;
    }
    return m;
  }, [matrixData.col_labels, colAxisTick]);

  /** Rotated top-axis labels extend past the last column; widen canvas + margin.right together */
  const computedRightMargin = useMemo(() => {
    const approx =
      Math.ceil(maxColLabelChars * TICK_LABEL_CHAR_PX * 0.82) + 52;
    return Math.min(
      440,
      Math.max(HEATMAP_MARGIN_RIGHT_BASE_PX, approx),
    );
  }, [maxColLabelChars]);

  useEffect(() => {
    const el = measureRef.current;
    if (!el) return;
    const apply = () => {
      const w = el.clientWidth;
      setContainerWidth(Math.max(720, w - 8));
    };
    apply();
    const ro = new ResizeObserver(apply);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const filterActive = Boolean(inputIndustry || outputIndustry);

  const heatmapCellColor = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (cell: any) => {
      const base = coefficientToColor(cell.value, bound);
      if (!filterActive) return base;
      if (cellMatchesIndustryHighlight(cell, inputIndustry, outputIndustry)) {
        return base;
      }
      return blendHex(base, DIM_BLEND_BG, 0.78);
    },
    [bound, filterActive, inputIndustry, outputIndustry],
  );

  const heatmapCellBorderColor = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (cell: any) => {
      if (!filterActive) return HEATMAP_CELL_GRID_STROKE;
      if (cellMatchesIndustryHighlight(cell, inputIndustry, outputIndustry)) {
        return "rgba(250, 204, 21, 0.9)";
      }
      return HEATMAP_CELL_GRID_STROKE_DIMMED;
    },
    [filterActive, inputIndustry, outputIndustry],
  );

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
    [onCellClick],
  );

  const containerHeight = "h-[1000px]";

  const chartWidth = containerWidth;

  const leftTickMargin = Math.min(
    560,
    Math.max(232, Math.ceil(maxRowLabelChars * TICK_LABEL_CHAR_PX)),
  );

  const heatmapMargins = useMemo(
    () => ({
      top: 335,
      right: computedRightMargin,
      bottom: 48,
      left: leftTickMargin,
    }),
    [leftTickMargin, computedRightMargin],
  );

  const heatmapCanvasWidth =
    chartWidth -
    SUPPLIER_TITLE_STRIP_PX +
    (computedRightMargin - HEATMAP_MARGIN_RIGHT_BASE_PX);

  const chartBodyHeight = useMemo(() => {
    const innerHAvail = 640;
    const cellY = Math.max(
      12,
      Math.min(26, innerHAvail / Math.max(nRows, 1)),
    );
    return Math.round(nRows * cellY);
  }, [nRows]);

  const chartHeight =
    heatmapMargins.top + heatmapMargins.bottom + chartBodyHeight;

  return (
    <div className="space-y-4">
      {/* Toolbar: stats + expand toggle */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-muted-foreground">
          <span>
            <span className="font-medium text-foreground">{nRows}</span>
            &times;
            <span className="font-medium text-foreground">{nCols}</span>{" "}
            sectors
          </span>
          <span>
            <span className="font-medium text-foreground">
              {nonZeroCount.toLocaleString()}
            </span>{" "}
            nonzero cells ({sparsity}% sparse)
          </span>
          <span>
            Range{" "}
            <span className="font-mono font-medium text-foreground">
              {minValue.toFixed(4)}
            </span>{" "}
            to{" "}
            <span className="font-mono font-medium text-foreground">
              {maxValue.toFixed(4)}
            </span>
          </span>
          <span>
            Mean (nonzero){" "}
            <span className="font-mono font-medium text-foreground">
              {meanNonZero.toFixed(4)}
            </span>
          </span>
        </div>

      </div>

      {/* Industry highlight filters */}
      <div className="flex flex-col gap-3 rounded-lg border border-border bg-muted/15 px-3 py-3 sm:flex-row sm:flex-wrap sm:items-end sm:gap-4">
        <div className="grid min-w-0 flex-1 gap-1.5 sm:max-w-md">
          <label
            htmlFor="io-heatmap-input-industry"
            className="text-xs font-medium text-muted-foreground"
          >
            Supplier
          </label>
          <SearchableSelect
            id="io-heatmap-input-industry"
            aria-label="Filter heatmap by supplier industry"
            options={inputOptions}
            value={inputIndustry}
            onChange={setInputIndustry}
            placeholder="Search suppliers…"
            emptyOptionLabel="All suppliers"
          />
        </div>
        <div className="grid min-w-0 flex-1 gap-1.5 sm:max-w-md">
          <label
            htmlFor="io-heatmap-output-industry"
            className="text-xs font-medium text-muted-foreground"
          >
            Consumer
          </label>
          <SearchableSelect
            id="io-heatmap-output-industry"
            aria-label="Filter heatmap by consumer industry"
            options={outputOptions}
            value={outputIndustry}
            onChange={setOutputIndustry}
            placeholder="Search consumers…"
            emptyOptionLabel="All industries"
          />
        </div>
        {filterActive ? (
          <p className="text-xs text-muted-foreground sm:pb-2 sm:pl-1">
            Highlighting the selected supplier and/or consumer; other cells are
            dimmed.
          </p>
        ) : null}
      </div>

      {/* Color legend */}
      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <span className="font-medium">Color scale:</span>
        <div className="flex items-center gap-1.5">
          <span className="font-mono">{(-bound).toFixed(3)}</span>
          <div
            className="h-3 w-44 rounded-sm"
            style={{
              background:
                "linear-gradient(to right, #2a0a0a, #5e1a1a, #a86060, #c8bcbc, #d1d1d1, #bcc8bc, #6a9a6a, #1a3a1a)",
            }}
          />
          <span className="font-mono">{bound.toFixed(3)}</span>
        </div>
        <div className="ml-2 flex items-center gap-3 border-l border-border pl-3">
          <span className="flex items-center gap-1">
            <span className="inline-block h-2.5 w-2.5 rounded-sm bg-[#1a3a1a]" />
            Positive dependency
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2.5 w-2.5 rounded-sm bg-[#d1d1d1] border border-border" />
            No dependency
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2.5 w-2.5 rounded-sm bg-[#5e1a1a]" />
            Negative dependency
          </span>
        </div>
      </div>

      {/* Hint */}
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <Info className="h-3 w-3 flex-shrink-0" />
        Hover cells for details. Click any cell to open full drill-down panel.
      </div>

      {/* Heatmap: Consumer title sits above canvas; extra margin avoids overlap with rotated column ticks */}
      <div
        ref={measureRef}
        className={`${containerHeight} w-full min-w-0 overflow-auto rounded-lg border border-border bg-muted transition-all duration-300`}
      >
        <div className="mx-auto w-full min-w-0 px-1 pt-4">
          <div
            className="grid w-max max-w-full"
            style={{
              gridTemplateColumns: `${SUPPLIER_TITLE_STRIP_PX}px ${heatmapCanvasWidth}px`,
              gridTemplateRows: `auto ${chartHeight}px`,
            }}
          >
            <div
              className="relative z-10 col-start-1 row-start-2 flex items-center justify-center bg-muted/20"
              style={{
                width: SUPPLIER_TITLE_STRIP_PX,
                minHeight: chartHeight,
              }}
            >
              <span
                className="font-medium text-foreground"
                style={{
                  fontSize: IO_AXIS_TITLE_PX,
                  writingMode: "vertical-rl",
                  transform: "rotate(180deg)",
                }}
              >
                Supplier
              </span>
            </div>
            <div className="col-start-2 row-start-1 row-span-2 min-w-0">
              <p
                className="mb-5 text-center font-medium tracking-wide text-foreground"
                style={{
                  paddingLeft: heatmapMargins.left,
                  paddingRight: heatmapMargins.right,
                  fontSize: IO_AXIS_TITLE_PX,
                  lineHeight: 1.25,
                }}
              >
                Consumer
              </p>
              <HeatMapCanvas
                data={data}
                width={heatmapCanvasWidth}
                height={chartHeight}
                margin={{ ...heatmapMargins }}
              valueFormat=">-.4f"
              pixelRatio={
                typeof window !== "undefined"
                  ? Math.min(window.devicePixelRatio, 2)
                  : 1
              }
              colors={heatmapCellColor}
              emptyColor="#252525"
              borderWidth={1}
              borderColor={heatmapCellBorderColor}
              xInnerPadding={HEATMAP_INNER_PADDING}
              yInnerPadding={HEATMAP_INNER_PADDING}
              enableLabels={false}
              axisTop={{
                tickSize: 0,
                tickPadding: 18,
                tickRotation: -48,
                truncateTickAt: AXIS_TICK_NO_TRUNCATE,
                format: (value) => {
                  const s = String(value);
                  return colAxisTick.get(s) ?? getSectorName(s);
                },
              }}
              axisLeft={{
                tickSize: 0,
                tickPadding: 8,
                tickRotation: 0,
                truncateTickAt: AXIS_TICK_NO_TRUNCATE,
                format: (value) => {
                  const s = String(value);
                  return rowAxisTick.get(s) ?? getSectorName(s);
                },
              }}
              hoverTarget="cell"
              tooltip={({ cell }) => {
                const rowCode = String(cell.serieId);
                const colCode = String(cell.data.x);
                const value = (cell.value as number) ?? 0;
                const rowName = resolveIoAxisLabel(matrixData, rowCode, "row");
                const colName = resolveIoAxisLabel(matrixData, colCode, "col");
                const { level, color, description } =
                  classifyCoefficient(value);
                const isDiagonal = rowCode === colCode;

                return (
                  <TooltipPortal>
                    <div className="max-w-xs rounded-lg border border-border bg-card px-4 py-3 text-sm shadow-xl">
                      <div className="mb-2">
                        <div className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                          Supplier
                        </div>
                        <div className="font-semibold text-card-foreground">
                          {rowName}
                        </div>
                        {rowName !== rowCode && (
                          <div className="font-mono text-[11px] text-muted-foreground">
                            {rowCode}
                          </div>
                        )}
                      </div>

                      <div className="mb-3">
                        <div className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                          Consumer
                        </div>
                        <div className="font-semibold text-card-foreground">
                          {colName}
                        </div>
                        {colName !== colCode && (
                          <div className="font-mono text-[11px] text-muted-foreground">
                            {colCode}
                          </div>
                        )}
                      </div>

                      <div className="mb-2 rounded-md border border-border bg-muted/40 px-3 py-2">
                        <div className="flex items-center justify-between gap-4">
                          <span className="text-xs text-muted-foreground">
                            Coefficient
                          </span>
                          <span className="font-mono text-base font-bold tabular-nums text-card-foreground">
                            {value.toFixed(6)}
                          </span>
                        </div>
                        <div className={`mt-1 text-xs font-medium ${color}`}>
                          {level} &mdash; {description}
                        </div>
                      </div>

                      <div className="text-[11px] leading-relaxed text-muted-foreground">
                        {isDiagonal ? (
                          <>
                            Intra-industry recirculation: {rowName} uses its
                            own output as input at a rate of{" "}
                            <span className="font-mono font-medium">
                              {value.toFixed(4)}
                            </span>{" "}
                            per dollar of output.
                          </>
                        ) : (
                          <>
                            Per $1 of{" "}
                            <span className="font-medium">{colName}</span>{" "}
                            output,{" "}
                            <span className="font-mono font-medium">
                              ${value.toFixed(4)}
                            </span>{" "}
                            of direct input is required from{" "}
                            <span className="font-medium">{rowName}</span>.
                          </>
                        )}
                      </div>
                    </div>
                  </TooltipPortal>
                );
              }}
              onClick={handleCellClick}
              isInteractive={true}
              theme={{
                background: HEATMAP_CANVAS_BG,
                text: {
                  fill: "#a3a3a3",
                  fontSize: 11,
                },
                axis: {
                  ticks: {
                    text: {
                      fill: "#a3a3a3",
                      fontSize: 11,
                    },
                  },
                },
                tooltip: {
                  container: {
                    background: "transparent",
                    padding: 0,
                    borderRadius: 0,
                    boxShadow: "none",
                  },
                },
              }}
            />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
