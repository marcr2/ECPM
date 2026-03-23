"use client";

import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";

const pageTitles: Record<string, string> = {
  "/data": "Data Overview",
  "/indicators": "Indicators",
  "/forecasting": "Forecasting",
  "/structural": "Structural Analysis",
  "/concentration": "Concentration",
};

export function Header() {
  const pathname = usePathname();
  const [backendStatus, setBackendStatus] = useState<
    "connected" | "disconnected" | "checking"
  >("checking");

  const title = pageTitles[pathname ?? ""] ?? "ECPM";

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/health`,
          { signal: AbortSignal.timeout(3000) }
        );
        setBackendStatus(res.ok ? "connected" : "disconnected");
      } catch {
        setBackendStatus("disconnected");
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30_000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-background/80 px-4 lg:px-6 backdrop-blur-sm">
      <h1 className="text-sm font-semibold tracking-tight">{title}</h1>
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <div
            className={`h-1.5 w-1.5 rounded-full ${
              backendStatus === "connected"
                ? "bg-emerald-500"
                : backendStatus === "disconnected"
                  ? "bg-red-500"
                  : "bg-yellow-500 animate-pulse"
            }`}
          />
          <span className="text-[11px] text-muted-foreground">
            {backendStatus === "connected"
              ? "API Connected"
              : backendStatus === "disconnected"
                ? "API Offline"
                : "Checking..."}
          </span>
        </div>
        <Badge variant="outline" className="text-[10px] font-mono">
          Phase 1
        </Badge>
      </div>
    </header>
  );
}
