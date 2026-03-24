import { Skeleton } from "@/components/ui/skeleton";

/**
 * Loading state for structural analysis page.
 */
export default function StructuralLoading() {
  return (
    <div className="space-y-6">
      {/* Year selector skeleton */}
      <div className="flex items-center justify-between">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-8 w-24" />
      </div>

      {/* Tab buttons skeleton */}
      <div className="flex gap-2">
        <Skeleton className="h-8 w-28" />
        <Skeleton className="h-8 w-36" />
        <Skeleton className="h-8 w-40" />
      </div>

      {/* Main content skeleton */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        {/* Heatmap area */}
        <div className="lg:col-span-8">
          <Skeleton className="h-[600px] w-full rounded-lg" />
        </div>

        {/* Sidebar controls */}
        <div className="lg:col-span-4 space-y-4">
          <Skeleton className="h-32 w-full rounded-lg" />
          <Skeleton className="h-48 w-full rounded-lg" />
        </div>
      </div>
    </div>
  );
}
