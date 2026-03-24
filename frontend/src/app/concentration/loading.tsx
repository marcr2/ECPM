import { Skeleton } from "@/components/ui/skeleton";

export default function ConcentrationLoading() {
  return (
    <div className="space-y-6 p-6">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-72" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-8 w-12" />
          <Skeleton className="h-8 w-12" />
          <Skeleton className="h-8 w-12" />
        </div>
      </div>

      {/* Hero section skeleton */}
      <Skeleton className="h-80 w-full rounded-lg" />

      {/* Two-column layout skeleton */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Skeleton className="h-[550px] rounded-lg" />
        <Skeleton className="h-[550px] rounded-lg" />
      </div>

      {/* Cards grid skeleton */}
      <div className="space-y-3">
        <Skeleton className="h-6 w-48" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-40 rounded-lg" />
          ))}
        </div>
      </div>
    </div>
  );
}
