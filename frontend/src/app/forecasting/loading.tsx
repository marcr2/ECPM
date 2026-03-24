import { Skeleton } from "@/components/ui/skeleton";

/**
 * Loading state for the forecasting page.
 * Server component - renders skeleton placeholders matching the page layout.
 */
export default function Loading() {
  return (
    <div className="space-y-6">
      {/* Hero: Crisis gauge skeleton */}
      <div className="rounded-lg border border-border bg-card p-4">
        <Skeleton className="mb-3 h-5 w-32" />
        <Skeleton className="mb-4 h-8 w-full" />
        <div className="grid grid-cols-3 gap-4">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
        </div>
        <Skeleton className="mt-4 h-24 w-full" />
      </div>

      {/* Main grid: Forecast chart + Regime detail */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        {/* Forecast chart (8 cols) */}
        <div className="rounded-lg border border-border bg-card p-4 lg:col-span-8">
          <Skeleton className="mb-3 h-5 w-40" />
          <Skeleton className="h-[350px] w-full" />
        </div>

        {/* Regime detail (4 cols) */}
        <div className="rounded-lg border border-border bg-card p-4 lg:col-span-4">
          <Skeleton className="mb-3 h-5 w-32" />
          <Skeleton className="mb-4 h-20 w-full" />
          <Skeleton className="mb-4 h-32 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      </div>

      {/* Tabs section */}
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="mb-4 flex gap-2">
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-8 w-24" />
        </div>
        <Skeleton className="h-[300px] w-full" />
      </div>
    </div>
  );
}
