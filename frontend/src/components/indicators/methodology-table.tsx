"use client";

import {
  Table,
  TableHeader,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import { FormulaDisplay } from "./formula-display";
import type { IndicatorMethodologyDoc } from "@/lib/indicators";

interface MethodologyTableProps {
  indicator: string;
  shaikhTonak: IndicatorMethodologyDoc;
  kliman: IndicatorMethodologyDoc;
}

/**
 * Side-by-side diff table comparing Shaikh/Tonak and Kliman methodologies.
 *
 * Highlights cells where the two methodologies diverge with a different
 * background color to make differences immediately visible.
 */
export function MethodologyTable({
  indicator,
  shaikhTonak,
  kliman,
}: MethodologyTableProps) {
  // Check if formulas differ
  const formulasDiffer =
    shaikhTonak.formula_latex !== kliman.formula_latex;

  // Check if interpretations differ
  const interpretationsDiffer =
    shaikhTonak.interpretation !== kliman.interpretation;

  // Build mapping comparison rows
  const maxMappings = Math.max(
    shaikhTonak.mappings.length,
    kliman.mappings.length
  );

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold">{indicator}</h3>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-28">Aspect</TableHead>
            <TableHead>Shaikh/Tonak</TableHead>
            <TableHead>Kliman TSSI</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {/* Formula row */}
          <TableRow>
            <TableCell className="font-medium text-muted-foreground">
              Formula
            </TableCell>
            <TableCell
              className={
                formulasDiffer ? "bg-amber-500/10" : ""
              }
            >
              {shaikhTonak.formula_latex ? (
                <FormulaDisplay
                  latex={shaikhTonak.formula_latex}
                  displayMode={false}
                />
              ) : (
                <span className="text-muted-foreground">--</span>
              )}
            </TableCell>
            <TableCell
              className={
                formulasDiffer ? "bg-amber-500/10" : ""
              }
            >
              {kliman.formula_latex ? (
                <FormulaDisplay
                  latex={kliman.formula_latex}
                  displayMode={false}
                />
              ) : (
                <span className="text-muted-foreground">--</span>
              )}
            </TableCell>
          </TableRow>

          {/* NIPA mapping rows */}
          {Array.from({ length: maxMappings }).map((_, i) => {
            const st = shaikhTonak.mappings[i];
            const kl = kliman.mappings[i];
            const differ =
              st?.nipa_table !== kl?.nipa_table ||
              st?.nipa_line !== kl?.nipa_line ||
              st?.operation !== kl?.operation;

            return (
              <TableRow key={`mapping-${i}`}>
                <TableCell className="font-medium text-muted-foreground">
                  {st?.marx_category || kl?.marx_category || `Mapping ${i + 1}`}
                </TableCell>
                <TableCell
                  className={differ ? "bg-amber-500/10" : ""}
                >
                  {st ? (
                    <span className="text-xs">
                      Table {st.nipa_table} L{st.nipa_line}{" "}
                      <span className="text-muted-foreground">
                        ({st.operation})
                      </span>
                    </span>
                  ) : (
                    <span className="text-muted-foreground">--</span>
                  )}
                </TableCell>
                <TableCell
                  className={differ ? "bg-amber-500/10" : ""}
                >
                  {kl ? (
                    <span className="text-xs">
                      Table {kl.nipa_table} L{kl.nipa_line}{" "}
                      <span className="text-muted-foreground">
                        ({kl.operation})
                      </span>
                    </span>
                  ) : (
                    <span className="text-muted-foreground">--</span>
                  )}
                </TableCell>
              </TableRow>
            );
          })}

          {/* Interpretation row */}
          <TableRow>
            <TableCell className="font-medium text-muted-foreground">
              Interpretation
            </TableCell>
            <TableCell
              className={
                interpretationsDiffer ? "bg-amber-500/10" : ""
              }
            >
              <p className="text-xs">{shaikhTonak.interpretation || "--"}</p>
            </TableCell>
            <TableCell
              className={
                interpretationsDiffer ? "bg-amber-500/10" : ""
              }
            >
              <p className="text-xs">{kliman.interpretation || "--"}</p>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>
  );
}
