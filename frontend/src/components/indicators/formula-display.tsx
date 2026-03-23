"use client";

import katex from "katex";
import "katex/dist/katex.min.css";

interface FormulaDisplayProps {
  latex: string;
  displayMode?: boolean;
}

/**
 * Renders LaTeX formulas using KaTeX renderToString.
 *
 * Uses dangerouslySetInnerHTML which is XSS-safe per KaTeX documentation
 * (KaTeX only generates math markup, never arbitrary HTML).
 */
export function FormulaDisplay({
  latex,
  displayMode = true,
}: FormulaDisplayProps) {
  const html = katex.renderToString(latex, {
    displayMode,
    throwOnError: false,
  });

  return <span dangerouslySetInnerHTML={{ __html: html }} />;
}
