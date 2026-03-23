"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";

/**
 * Error boundary for the indicators section.
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
    console.error("Indicator section error:", error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center gap-4 p-8">
      <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 text-center">
        <h2 className="mb-2 text-lg font-semibold text-foreground">
          Failed to load indicators
        </h2>
        <p className="mb-4 text-sm text-muted-foreground">
          {error.message || "An unexpected error occurred."}
        </p>
        {error.digest && (
          <p className="mb-4 font-mono text-xs text-muted-foreground">
            Error ID: {error.digest}
          </p>
        )}
        <Button variant="outline" onClick={() => unstable_retry()}>
          Try again
        </Button>
      </div>
    </div>
  );
}
