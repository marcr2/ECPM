"use client";

import { useState, useMemo } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
  type ColumnFiltersState,
} from "@tanstack/react-table";
import type { SeriesMetadata } from "@/lib/api";
import {
  formatDate,
  formatNumber,
  frequencyLabel,
  statusColor,
} from "@/lib/utils";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowUpDown, Search } from "lucide-react";

// ---------- Columns ----------

const columns: ColumnDef<SeriesMetadata>[] = [
  {
    accessorKey: "series_id",
    header: ({ column }) => (
      <button
        className="flex items-center gap-1 hover:text-foreground transition-colors"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        Series ID
        <ArrowUpDown className="h-3 w-3" />
      </button>
    ),
    cell: ({ row }) => (
      <span className="font-mono text-xs text-primary">
        {row.getValue("series_id")}
      </span>
    ),
  },
  {
    accessorKey: "name",
    header: ({ column }) => (
      <button
        className="flex items-center gap-1 hover:text-foreground transition-colors"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        Name
        <ArrowUpDown className="h-3 w-3" />
      </button>
    ),
    cell: ({ row }) => (
      <span className="max-w-[280px] truncate block text-xs">
        {row.getValue("name")}
      </span>
    ),
  },
  {
    accessorKey: "source",
    header: "Source",
    cell: ({ row }) => {
      const source = row.getValue("source") as string;
      return (
        <Badge variant="outline" className="text-[10px] font-mono">
          {source}
        </Badge>
      );
    },
    filterFn: "equals",
  },
  {
    accessorKey: "frequency",
    header: "Freq",
    cell: ({ row }) => (
      <span className="text-xs text-muted-foreground">
        {frequencyLabel(row.getValue("frequency"))}
      </span>
    ),
  },
  {
    accessorKey: "last_updated",
    header: ({ column }) => (
      <button
        className="flex items-center gap-1 hover:text-foreground transition-colors"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        Last Updated
        <ArrowUpDown className="h-3 w-3" />
      </button>
    ),
    cell: ({ row }) => (
      <span className="text-xs text-muted-foreground font-mono">
        {formatDate(row.getValue("last_updated"))}
      </span>
    ),
  },
  {
    accessorKey: "observation_count",
    header: ({ column }) => (
      <button
        className="flex items-center gap-1 hover:text-foreground transition-colors"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        Obs
        <ArrowUpDown className="h-3 w-3" />
      </button>
    ),
    cell: ({ row }) => (
      <span className="text-xs font-mono tabular-nums">
        {formatNumber(row.getValue("observation_count"))}
      </span>
    ),
  },
  {
    accessorKey: "fetch_status",
    header: "Status",
    cell: ({ row }) => {
      const status = row.getValue("fetch_status") as string;
      return (
        <span
          className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium ${statusColor(status)}`}
        >
          {status}
        </span>
      );
    },
    filterFn: "equals",
  },
];

// ---------- Loading skeleton ----------

function TableSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="flex gap-4 px-2">
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-5 w-48" />
          <Skeleton className="h-5 w-12" />
          <Skeleton className="h-5 w-16" />
          <Skeleton className="h-5 w-20" />
          <Skeleton className="h-5 w-12" />
          <Skeleton className="h-5 w-14" />
        </div>
      ))}
    </div>
  );
}

// ---------- Component ----------

interface SeriesTableProps {
  data: SeriesMetadata[];
  isLoading: boolean;
  error: string | null;
}

export function SeriesTable({ data, isLoading, error }: SeriesTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = useState("");

  // Source filter
  const sourceFilter = useMemo(
    () =>
      (columnFilters.find((f) => f.id === "source")?.value as string) ?? "all",
    [columnFilters]
  );

  // Status filter
  const statusFilter = useMemo(
    () =>
      (columnFilters.find((f) => f.id === "fetch_status")?.value as string) ??
      "all",
    [columnFilters]
  );

  const table = useReactTable({
    data,
    columns,
    state: { sorting, columnFilters, globalFilter },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  const setSourceFilter = (value: string) => {
    setColumnFilters((prev) => {
      const next = prev.filter((f) => f.id !== "source");
      if (value !== "all") next.push({ id: "source", value });
      return next;
    });
  };

  const setStatusFilter = (value: string) => {
    setColumnFilters((prev) => {
      const next = prev.filter((f) => f.id !== "fetch_status");
      if (value !== "all") next.push({ id: "fetch_status", value });
      return next;
    });
  };

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <p className="text-sm text-destructive">Failed to load series data</p>
        <p className="mt-1 text-xs text-muted-foreground">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search series..."
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            className="h-8 pl-8 text-xs bg-muted/30"
          />
        </div>
        <select
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value)}
          className="h-8 rounded-md border border-border bg-muted/30 px-2.5 text-xs text-foreground outline-none"
        >
          <option value="all">All Sources</option>
          <option value="FRED">FRED</option>
          <option value="BEA">BEA</option>
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="h-8 rounded-md border border-border bg-muted/30 px-2.5 text-xs text-foreground outline-none"
        >
          <option value="all">All Statuses</option>
          <option value="ok">OK</option>
          <option value="error">Error</option>
          <option value="stale">Stale</option>
          <option value="pending">Pending</option>
        </select>
        <span className="text-[11px] text-muted-foreground ml-auto tabular-nums">
          {table.getFilteredRowModel().rows.length} of {data.length} series
        </span>
      </div>

      {/* Table */}
      {isLoading ? (
        <TableSkeleton />
      ) : data.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <p className="text-sm text-muted-foreground">No series data yet</p>
          <p className="mt-1 text-xs text-muted-foreground/60">
            Trigger a data fetch to populate the table
          </p>
        </div>
      ) : (
        <div className="rounded-md border border-border">
          <Table>
            <TableHeader>
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow
                  key={headerGroup.id}
                  className="border-border hover:bg-transparent"
                >
                  {headerGroup.headers.map((header) => (
                    <TableHead
                      key={header.id}
                      className="h-9 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground"
                    >
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {table.getRowModel().rows.map((row, i) => (
                <TableRow
                  key={row.id}
                  className={`border-border h-9 ${
                    i % 2 === 0 ? "bg-transparent" : "bg-muted/20"
                  }`}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id} className="py-1.5">
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
