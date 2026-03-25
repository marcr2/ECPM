/**
 * Diverging red (negative) → neutral → green (positive) palette used by the
 * BEA I/O coefficient heatmap. Reused for concentration–indicator correlations.
 */

// Ends: negative (reds) → near-zero (dim whites / soft neutrals) → positive (greens)
export const IO_HEATMAP_COLORS = [
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

export const IO_DIM_BLEND_BG = "#161616";

/** Neutral “no dependency” only in this band; outside uses full red/green ramps vs `bound`. */
export const IO_NEUTRAL_EPS = 0.00001;

/**
 * Map a numeric value in roughly [-bound, bound] to the I/O heatmap palette.
 */
export function coefficientToColor(
  value: number | null | undefined,
  bound: number,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "#252525";
  }
  if (Math.abs(value) <= IO_NEUTRAL_EPS) {
    return IO_HEATMAP_COLORS[6];
  }
  const b = Math.max(bound, IO_NEUTRAL_EPS * 1.0001);
  const span = b - IO_NEUTRAL_EPS;
  if (value < -IO_NEUTRAL_EPS) {
    const clamped = Math.max(-b, Math.min(-IO_NEUTRAL_EPS, value));
    const t = (clamped + b) / span;
    const idx = Math.min(5, Math.floor(t * 6));
    return IO_HEATMAP_COLORS[idx];
  }
  const clamped = Math.min(b, Math.max(IO_NEUTRAL_EPS, value));
  const t = (clamped - IO_NEUTRAL_EPS) / span;
  const idx = Math.min(11, 7 + Math.floor(t * 5));
  return IO_HEATMAP_COLORS[idx];
}

export function blendHex(fg: string, bg: string, bgWeight: number): string {
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

/** CSS linear-gradient matching the I/O palette from −bound to +bound (e.g. r = −1 … +1). */
export function ioHeatmapLegendGradientStops(): string {
  const c = IO_HEATMAP_COLORS;
  return `linear-gradient(to right, ${c[0]} 0%, ${c[3]} 22%, ${c[6]} 50%, ${c[9]} 78%, ${c[11]} 100%)`;
}
