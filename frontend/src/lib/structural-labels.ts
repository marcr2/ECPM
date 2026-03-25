import { getSectorName } from "@/lib/bea-sector-names";
import type { MatrixResponse } from "@/lib/structural-api";

/**
 * Human-readable label for an I-O axis code: prefer BEA descriptions from the
 * API, then the static summary-level name map, then the code.
 */
export function resolveIoAxisLabel(
  data: MatrixResponse,
  code: string,
  axis: "row" | "col",
): string {
  const labels = axis === "row" ? data.row_labels : data.col_labels;
  const extras =
    axis === "row" ? data.row_display_labels : data.col_display_labels;
  const i = labels.indexOf(code);
  if (i < 0) return getSectorName(code);
  const raw = extras?.[i]?.trim();
  if (raw && raw !== code) return raw;
  return getSectorName(code);
}
