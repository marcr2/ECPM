"use client";

import { useEffect } from "react";
import { unstable_retry as retry } from "next/navigation";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ConcentrationError({ error, reset }: ErrorProps) {
  useEffect(() => {
    // Log error to monitoring service
    console.error("Concentration page error:", error);
  }, [error]);

  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center p-6">
      <div className="text-center">
        <h2 className="text-xl font-semibold text-destructive">
          Failed to load concentration data
        </h2>
        <p className="mt-2 max-w-md text-sm text-muted-foreground">
          {error.message || "An unexpected error occurred while loading the concentration analysis."}
        </p>
        {error.digest && (
          <p className="mt-1 text-xs text-muted-foreground/60">
            Error ID: {error.digest}
          </p>
        )}
        <div className="mt-6 flex items-center justify-center gap-4">
          <button
            onClick={reset}
            className="rounded bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Try again
          </button>
          <a
            href="/data"
            className="rounded border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-muted"
          >
            Go to Data Overview
          </a>
        </div>
      </div>
    </div>
  );
}
