"use client";

import type { FetchStatus } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CheckCircle, AlertCircle, Clock } from "lucide-react";

interface FetchStatusCardProps {
  status: FetchStatus | null;
  isLoading: boolean;
}

export function FetchStatusCard({
  status,
  isLoading,
}: FetchStatusCardProps) {
  return (
    <Card className="border-border bg-card">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">Pipeline Status</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading || !status ? (
          <div className="grid grid-cols-4 gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="h-14 animate-pulse rounded-md bg-muted/30"
              />
            ))}
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <StatBlock
                label="Total Series"
                value={status.total_series}
                icon={<Database className="h-3.5 w-3.5 text-muted-foreground" />}
              />
              <StatBlock
                label="OK"
                value={status.ok_count}
                icon={<CheckCircle className="h-3.5 w-3.5 text-emerald-400" />}
                valueClass="text-emerald-400"
              />
              <StatBlock
                label="Errors"
                value={status.error_count}
                icon={<AlertCircle className="h-3.5 w-3.5 text-red-400" />}
                valueClass={
                  status.error_count > 0 ? "text-red-400" : undefined
                }
              />
              <StatBlock
                label="Stale"
                value={status.stale_count}
                icon={<Clock className="h-3.5 w-3.5 text-amber-400" />}
                valueClass={
                  status.stale_count > 0 ? "text-amber-400" : undefined
                }
              />
            </div>

            <div className="mt-3 flex items-center gap-4 text-[11px] text-muted-foreground">
              <span>
                Last fetch: {formatDate(status.last_fetch_time) || "Never"}
              </span>
              {status.next_scheduled_run && (
                <span>
                  Next run: {formatDate(status.next_scheduled_run)}
                </span>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function Database({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M3 5V19A9 3 0 0 0 21 19V5" />
      <path d="M3 12A9 3 0 0 0 21 12" />
    </svg>
  );
}

function StatBlock({
  label,
  value,
  icon,
  valueClass,
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
  valueClass?: string;
}) {
  return (
    <div className="flex items-center gap-2 rounded-md border border-border bg-muted/20 px-3 py-2">
      {icon}
      <div>
        <p className={`text-lg font-semibold font-mono tabular-nums leading-tight ${valueClass ?? ""}`}>
          {value}
        </p>
        <p className="text-[10px] text-muted-foreground">{label}</p>
      </div>
    </div>
  );
}
