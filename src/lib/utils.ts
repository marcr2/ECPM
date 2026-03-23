import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format an ISO date string to a compact readable form */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "--";
  try {
    return new Date(iso).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

/** Format a number with locale-aware separators */
export function formatNumber(n: number | null | undefined): string {
  if (n == null) return "--";
  return n.toLocaleString("en-US");
}

/** Human-readable frequency label */
export function frequencyLabel(freq: string | null | undefined): string {
  const labels: Record<string, string> = {
    D: "Daily",
    M: "Monthly",
    Q: "Quarterly",
    A: "Annual",
  };
  return labels[freq ?? ""] ?? freq ?? "--";
}

/** Tailwind color classes for fetch status badges */
export function statusColor(status: string | null | undefined): string {
  switch (status) {
    case "ok":
      return "bg-emerald-500/15 text-emerald-400 border-emerald-500/20";
    case "error":
      return "bg-red-500/15 text-red-400 border-red-500/20";
    case "stale":
      return "bg-amber-500/15 text-amber-400 border-amber-500/20";
    case "pending":
      return "bg-zinc-500/15 text-zinc-400 border-zinc-500/20";
    default:
      return "bg-zinc-500/15 text-zinc-400 border-zinc-500/20";
  }
}
