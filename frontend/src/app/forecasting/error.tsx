"use client";

import { useEffect } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

/**
 * Error boundary for the forecasting section.
 *
 * Uses Next.js 16 `unstable_retry` prop (NOT `reset`).
 * Must be a client component.
 */
export default function ErrorPage({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string };
  unstable_retry: () => void;
}) {
  useEffect(() => {
    console.error("Forecasting section error:", error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center gap-4 p-8">
      <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 text-center">
        <h2 className="mb-2 text-lg font-semibold text-foreground">
          Failed to load forecasting data
        </h2>
        <p className="mb-4 text-sm text-muted-foreground">
          {error.message || "An unexpected error occurred."}
        </p>
        {error.digest && (
          <p className="mb-4 font-mono text-xs text-muted-foreground">
            Error ID: {error.digest}
          </p>
        )}
        <div className="flex justify-center gap-3">
          <Button variant="outline" onClick={() => unstable_retry()}>
            Try again
          </Button>
          <Link
            href="/"
            className="inline-flex h-8 items-center justify-center rounded-lg px-2.5 text-sm font-medium hover:bg-muted hover:text-foreground"
          >
            Go home
          </Link>
        </div>
      </div>
    </div>
  );
}
