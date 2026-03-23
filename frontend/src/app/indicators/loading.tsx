import { Skeleton } from "@/components/ui/skeleton";

/**
 * Loading state for the indicators overview page.
 * Server component -- renders skeleton placeholders matching the
 * dashboard grid layout: 3 hero cards + 5 secondary cards.
 */
export default function Loading() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96" />
      </div>

      {/* Hero row: 3 large cards for TRPF trio */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={`hero-${i}`}
            className="rounded-lg border border-border bg-card p-4"
          >
            <Skeleton className="mb-3 h-5 w-40" />
            <Skeleton className="mb-2 h-8 w-24" />
            <Skeleton className="h-10 w-full" />
          </div>
        ))}
      </div>

      {/* Secondary section: 5 smaller cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={`secondary-${i}`}
            className="rounded-lg border border-border bg-card p-4"
          >
            <Skeleton className="mb-2 h-4 w-32" />
            <Skeleton className="mb-2 h-6 w-20" />
            <Skeleton className="h-8 w-full" />
          </div>
        ))}
      </div>
    </div>
  );
}
