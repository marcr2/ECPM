"use client";

import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  fetchTrainingLog,
  type TrainingStep,
} from "@/lib/forecast-api";
import { CheckCircle, XCircle, Loader2, ScrollText } from "lucide-react";

/**
 * Read-only training log viewer.
 *
 * Fetches the latest persisted training log from the API on mount
 * and displays step badges + scrollable log entries.
 * Training can only be triggered via authenticated API calls.
 */
export function TrainingStatus() {
  const [entries, setEntries] = useState<TrainingStep[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const log = await fetchTrainingLog();
        if (!cancelled) {
          setEntries(log.entries);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load training log"
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [entries]);

  const steps = deduplicateSteps(entries);
  const pipelineEntry = entries.find(
    (e) => e.name === "pipeline" && (e.status === "complete" || e.status === "error")
  );
  const totalDuration = pipelineEntry?.duration_ms;

  const getStepIcon = (status: string) => {
    switch (status) {
      case "complete":
        return <CheckCircle className="h-3 w-3 text-emerald-400" />;
      case "error":
        return <XCircle className="h-3 w-3 text-red-400" />;
      case "running":
        return <Loader2 className="h-3 w-3 animate-spin text-blue-400" />;
      default:
        return <div className="h-3 w-3 rounded-full bg-muted-foreground/30" />;
    }
  };

  const getStepVariant = (
    status: string
  ): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case "complete":
        return "default";
      case "error":
        return "destructive";
      case "running":
        return "secondary";
      default:
        return "outline";
    }
  };

  const formatDuration = (ms: number): string => {
    const secs = ms / 1000;
    if (secs < 60) return `${secs.toFixed(1)}s`;
    const mins = Math.floor(secs / 60);
    const remSecs = secs % 60;
    return `${mins}m ${remSecs.toFixed(0)}s`;
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="flex items-center gap-2">
          <ScrollText className="h-5 w-5" />
          Latest Training Log
        </CardTitle>
        {totalDuration !== undefined && (
          <span className="text-sm tabular-nums text-muted-foreground">
            Total: {formatDuration(totalDuration)}
          </span>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {loading && (
          <div className="flex h-24 items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {!loading && !error && entries.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No training log available. Training is triggered via the API.
          </p>
        )}

        {steps.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {steps.map((step) => (
              <Badge
                key={step.name}
                variant={getStepVariant(step.status)}
                className="flex items-center gap-1"
              >
                {getStepIcon(step.status)}
                {step.name}
                {step.duration_ms !== undefined && (
                  <span className="text-xs opacity-70">
                    ({formatDuration(step.duration_ms)})
                  </span>
                )}
              </Badge>
            ))}
          </div>
        )}

        {entries.length > 0 && (
          <div
            ref={logContainerRef}
            className="max-h-64 overflow-y-auto rounded-lg bg-muted/50 p-3 font-mono text-xs"
          >
            {entries.map((entry, idx) => {
              const ts = new Date(entry.timestamp).toLocaleTimeString();
              const msg =
                entry.error ??
                entry.detail ??
                `${entry.name}: ${entry.status}`;
              return (
                <div key={idx} className="whitespace-pre-wrap">
                  <span className="text-muted-foreground">[{ts}]</span>{" "}
                  <span
                    className={
                      entry.status === "error"
                        ? "text-red-400"
                        : entry.status === "complete"
                          ? "text-emerald-400"
                          : ""
                    }
                  >
                    [{entry.name}]
                  </span>{" "}
                  {msg}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function deduplicateSteps(entries: TrainingStep[]): TrainingStep[] {
  const map = new Map<string, TrainingStep>();
  for (const entry of entries) {
    if (entry.name === "pipeline") continue;
    map.set(entry.name, entry);
  }
  return Array.from(map.values());
}
