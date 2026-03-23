import { Skeleton } from "@/components/ui/skeleton";

/**
 * Loading state for individual indicator detail pages.
 * Shows large skeleton for chart area and smaller skeletons for controls.
 */
export default function Loading() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-5 w-16 rounded-full" />
          <Skeleton className="h-5 w-24 rounded-full" />
        </div>
      </div>

      {/* Chart skeleton */}
      <Skeleton className="h-[420px] w-full rounded-xl" />

      {/* Controls skeleton */}
      <div className="flex gap-4">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-6 w-36" />
        <Skeleton className="h-6 w-40" />
      </div>

      {/* Formula skeleton */}
      <Skeleton className="h-20 w-full rounded-xl" />
    </div>
  );
}
