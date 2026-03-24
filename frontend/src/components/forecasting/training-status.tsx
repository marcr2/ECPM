"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  triggerTraining,
  subscribeToTrainingProgress,
  type TrainingStep,
} from "@/lib/forecast-api";
import { Play, CheckCircle, XCircle, Loader2 } from "lucide-react";

interface TrainingStatusProps {
  onTrainingComplete?: () => void;
}

interface LogLine {
  timestamp: string;
  message: string;
}

/**
 * Training status component with real-time progress via SSE.
 *
 * Features:
 * - "Train Now" button to trigger training
 * - Step badges showing pending/running/complete/error
 * - Scrollable log area with last 100 messages
 * - Elapsed time counter
 * - Auto-cleanup on unmount
 */
export function TrainingStatus({ onTrainingComplete }: TrainingStatusProps) {
  const [isTraining, setIsTraining] = useState(false);
  const [steps, setSteps] = useState<TrainingStep[]>([]);
  const [logLines, setLogLines] = useState<LogLine[]>([]);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);

  const eventSourceRef = useRef<EventSource | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const logContainerRef = useRef<HTMLDivElement>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  // Auto-scroll log to bottom
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logLines]);

  const handleTrainingComplete = useCallback(() => {
    setIsTraining(false);
    setShowSuccess(true);

    // Clear timer
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    // Close event source
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    // Call completion callback
    if (onTrainingComplete) {
      onTrainingComplete();
    }

    // Hide success after 3s
    setTimeout(() => {
      setShowSuccess(false);
    }, 3000);
  }, [onTrainingComplete]);

  const startTraining = async () => {
    setError(null);
    setSteps([]);
    setLogLines([]);
    setElapsedTime(0);
    setShowSuccess(false);

    try {
      // Trigger training
      const response = await triggerTraining();
      setIsTraining(true);

      // Add initial log
      addLogLine(`Training started. Task ID: ${response.task_id}`);

      // Start elapsed time counter
      const startTime = Date.now();
      timerRef.current = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
      }, 1000);

      // Subscribe to progress stream
      eventSourceRef.current = subscribeToTrainingProgress(
        (data) => {
          // Update steps
          setSteps((prev) => {
            const existingIdx = prev.findIndex((s) => s.name === data.name);
            if (existingIdx >= 0) {
              const updated = [...prev];
              updated[existingIdx] = data;
              return updated;
            }
            return [...prev, data];
          });

          // Add log line
          if (data.detail) {
            addLogLine(`[${data.name}] ${data.detail}`);
          } else {
            addLogLine(`[${data.name}] Status: ${data.status}`);
          }

          // Check if complete
          if (data.name === "pipeline" && data.status === "complete") {
            handleTrainingComplete();
          }

          // Check if error
          if (data.status === "error") {
            setError(`Training failed at step: ${data.name}`);
            handleTrainingComplete();
          }
        },
        (err) => {
          console.error("SSE error:", err);
          setError("Lost connection to training progress stream");
        }
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start training");
      setIsTraining(false);
    }
  };

  const addLogLine = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogLines((prev) => {
      const updated = [...prev, { timestamp, message }];
      // Keep only last 100 lines
      return updated.slice(-100);
    });
  };

  const formatElapsedTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

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

  const getStepVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
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

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle>Model Training</CardTitle>
        {isTraining && (
          <span className="text-sm tabular-nums text-muted-foreground">
            {formatElapsedTime(elapsedTime)}
          </span>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Train button */}
        <Button
          onClick={startTraining}
          disabled={isTraining}
          className="w-full"
        >
          {isTraining ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Training in progress...
            </>
          ) : (
            <>
              <Play className="mr-2 h-4 w-4" />
              Train Now
            </>
          )}
        </Button>

        {/* Error display */}
        {error && (
          <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {/* Success display */}
        {showSuccess && (
          <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-3 text-sm text-emerald-400">
            Training completed successfully!
          </div>
        )}

        {/* Step badges */}
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
                    ({(step.duration_ms / 1000).toFixed(1)}s)
                  </span>
                )}
              </Badge>
            ))}
          </div>
        )}

        {/* Log area */}
        {logLines.length > 0 && (
          <div
            ref={logContainerRef}
            className="max-h-48 overflow-y-auto rounded-lg bg-muted/50 p-3 font-mono text-xs"
          >
            {logLines.map((line, idx) => (
              <div key={idx} className="whitespace-pre-wrap">
                <span className="text-muted-foreground">[{line.timestamp}]</span>{" "}
                {line.message}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
