import type { ReactNode } from "react";
import Link from "next/link";

/**
 * Layout for the /structural section.
 *
 * Simple wrapper with breadcrumb navigation.
 */
export default function StructuralLayout({
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
        <span className="text-foreground">Structural Analysis</span>
      </nav>

      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold tracking-tight">
          Structural Analysis
        </h1>
        <p className="text-sm text-muted-foreground">
          Input-Output analysis, reproduction schemas, and shock propagation
        </p>
      </div>

      {children}
    </div>
  );
}
