"use client";

import { useEffect, useState } from "react";
import {
  fetchMethodologyDocs,
  type MethodologyDocResponse,
  type NIPAMappingDoc,
} from "@/lib/indicators";
import { FormulaDisplay } from "@/components/indicators/formula-display";
import { MethodologyTable } from "@/components/indicators/methodology-table";
import {
  Table,
  TableHeader,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

/**
 * Methodology documentation page (DASH-05).
 *
 * Displays LaTeX formulas, NIPA component mapping tables, interpretation
 * notes, and citations for each methodology. Includes side-by-side diff
 * tables showing where Shaikh/Tonak and Kliman diverge.
 */
export default function MethodologyPage() {
  const [stDocs, setStDocs] = useState<MethodologyDocResponse | null>(null);
  const [klDocs, setKlDocs] = useState<MethodologyDocResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [st, kl] = await Promise.all([
          fetchMethodologyDocs("shaikh-tonak"),
          fetchMethodologyDocs("kliman"),
        ]);
        setStDocs(st);
        setKlDocs(kl);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load methodology docs"
        );
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <MethodologySkeleton />;
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 text-center">
        <h2 className="mb-2 text-lg font-semibold">
          Failed to load methodology documentation
        </h2>
        <p className="mb-4 text-sm text-muted-foreground">{error}</p>
        <Button variant="outline" onClick={() => window.location.reload()}>
          Retry
        </Button>
      </div>
    );
  }

  // Combine indicator slugs from both methodologies
  const allSlugs = new Set([
    ...(stDocs?.indicators?.map((d) => d.indicator_slug) ?? []),
    ...(klDocs?.indicators?.map((d) => d.indicator_slug) ?? []),
  ]);

  const stMap = new Map(
    stDocs?.indicators?.map((d) => [d.indicator_slug, d]) ?? []
  );
  const klMap = new Map(
    klDocs?.indicators?.map((d) => [d.indicator_slug, d]) ?? []
  );

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-lg font-semibold">Methodology Documentation</h2>
        <p className="text-sm text-muted-foreground">
          NIPA-to-Marx variable mappings, formulas, and interpretation for each
          methodology
        </p>
      </div>

      {/* Table of Contents */}
      <nav className="rounded-xl border border-border bg-card p-4">
        <h3 className="mb-2 text-sm font-medium">Contents</h3>
        <ul className="columns-2 gap-4 text-xs text-muted-foreground">
          {[...allSlugs].map((slug) => {
            const doc = stMap.get(slug) ?? klMap.get(slug);
            return (
              <li key={slug} className="mb-1">
                <a
                  href={`#${slug}`}
                  className="hover:text-foreground hover:underline"
                >
                  {doc?.indicator_name ?? slug}
                </a>
              </li>
            );
          })}
          <li className="mb-1">
            <a
              href="#comparison"
              className="hover:text-foreground hover:underline"
            >
              Side-by-side Comparison
            </a>
          </li>
        </ul>
      </nav>

      {/* Per-methodology, per-indicator documentation */}
      {[
        { key: "shaikh-tonak", name: "Shaikh/Tonak", docs: stDocs },
        { key: "kliman", name: "Kliman TSSI", docs: klDocs },
      ].map(({ key, name, docs }) => (
        <section key={key} className="space-y-6">
          <h2 className="border-b border-border pb-2 text-base font-semibold">
            {name}
          </h2>
          {docs?.indicators?.map((doc) => (
            <div
              key={doc.indicator_slug}
              id={key === "shaikh-tonak" ? doc.indicator_slug : undefined}
              className="space-y-3 rounded-xl border border-border bg-card p-4"
            >
              <h3 className="text-sm font-semibold">{doc.indicator_name}</h3>

              {/* Formula */}
              {doc.formula_latex && (
                <div className="rounded-lg bg-muted/50 p-3">
                  <FormulaDisplay latex={doc.formula_latex} />
                </div>
              )}

              {/* NIPA Mappings Table */}
              {doc.mappings.length > 0 && (
                <div>
                  <h4 className="mb-1 text-xs font-medium text-muted-foreground">
                    NIPA Component Mappings
                  </h4>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Marx Category</TableHead>
                        <TableHead>NIPA Table</TableHead>
                        <TableHead>Line</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead>Operation</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {doc.mappings.map((m: NIPAMappingDoc, i: number) => (
                        <TableRow key={i}>
                          <TableCell className="font-medium">
                            {m.marx_category}
                          </TableCell>
                          <TableCell>{m.nipa_table}</TableCell>
                          <TableCell>{m.nipa_line}</TableCell>
                          <TableCell className="text-muted-foreground">
                            {m.nipa_description}
                          </TableCell>
                          <TableCell>
                            <code className="text-xs">{m.operation}</code>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}

              {/* Interpretation */}
              {doc.interpretation && (
                <div>
                  <h4 className="mb-1 text-xs font-medium text-muted-foreground">
                    Interpretation
                  </h4>
                  <p className="text-sm text-foreground/80">
                    {doc.interpretation}
                  </p>
                </div>
              )}

              {/* Citations */}
              {doc.citations.length > 0 && (
                <div>
                  <h4 className="mb-1 text-xs font-medium text-muted-foreground">
                    References
                  </h4>
                  <ul className="list-disc pl-4 text-xs text-muted-foreground">
                    {doc.citations.map((c: string, i: number) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </section>
      ))}

      {/* Side-by-side comparison section */}
      <section id="comparison" className="space-y-4">
        <h2 className="border-b border-border pb-2 text-base font-semibold">
          Side-by-side Comparison
        </h2>
        <p className="text-sm text-muted-foreground">
          Cells highlighted in amber indicate where the two methodologies
          diverge.
        </p>
        {[...allSlugs].map((slug) => {
          const stDoc = stMap.get(slug);
          const klDoc = klMap.get(slug);
          if (!stDoc || !klDoc) return null;
          return (
            <MethodologyTable
              key={slug}
              indicator={stDoc.indicator_name}
              shaikhTonak={stDoc}
              kliman={klDoc}
            />
          );
        })}
      </section>
    </div>
  );
}

function MethodologySkeleton() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Skeleton className="h-6 w-64" />
        <Skeleton className="h-4 w-96" />
      </div>
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className="space-y-3 rounded-xl border border-border bg-card p-4"
        >
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      ))}
    </div>
  );
}
