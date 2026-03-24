import type { ReactNode } from "react";
import Link from "next/link";

/**
 * Layout for the /forecasting section.
 *
 * Simple wrapper with header and breadcrumb navigation.
 * No context provider needed (simpler than indicators layout).
 */
export default function ForecastingLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div className="space-y-4">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/" className="hover:text-foreground">
          Home
        </Link>
        <span>/</span>
        <span className="text-foreground">Forecasting</span>
      </nav>

      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold tracking-tight">
          Economic Forecasting
        </h1>
        <p className="text-sm text-muted-foreground">
          Crisis index, VAR forecasts, regime detection, and backtesting
        </p>
      </div>

      {children}
    </div>
  );
}
