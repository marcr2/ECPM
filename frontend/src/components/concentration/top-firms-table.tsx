"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { FirmInfo } from "@/lib/concentration-api";

interface TopFirmsTableProps {
  firms: FirmInfo[];
  year: number;
}

/**
 * Table showing top firms by market share.
 * Highlights top 4 firms (CR4 contributors) with different background.
 */
export function TopFirmsTable({ firms, year }: TopFirmsTableProps) {
  // Format revenue with appropriate suffix
  const formatRevenue = (revenue: number | null | undefined): string => {
    if (revenue === null || revenue === undefined) return "-";
    if (revenue >= 1e12) return `$${(revenue / 1e12).toFixed(1)}T`;
    if (revenue >= 1e9) return `$${(revenue / 1e9).toFixed(1)}B`;
    if (revenue >= 1e6) return `$${(revenue / 1e6).toFixed(1)}M`;
    return `$${revenue.toLocaleString()}`;
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">
          Top Firms by Market Share ({year})
        </h3>
        <span className="text-xs text-muted-foreground">
          {firms.length} firms shown
        </span>
      </div>

      <div className="rounded-md border border-border">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="w-12 text-center">#</TableHead>
              <TableHead>Firm Name</TableHead>
              <TableHead>Parent Company</TableHead>
              <TableHead className="text-right">Market Share</TableHead>
              <TableHead className="text-right">Revenue</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {firms.map((firm) => (
              <TableRow
                key={firm.rank}
                className={
                  firm.rank <= 4
                    ? "bg-blue-500/5 hover:bg-blue-500/10"
                    : "hover:bg-muted/50"
                }
              >
                <TableCell className="text-center font-medium">
                  {firm.rank <= 4 ? (
                    <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-blue-500 text-xs font-bold text-white">
                      {firm.rank}
                    </span>
                  ) : (
                    <span className="text-muted-foreground">{firm.rank}</span>
                  )}
                </TableCell>
                <TableCell className="font-medium">{firm.name}</TableCell>
                <TableCell className="text-muted-foreground">
                  {firm.parent || "-"}
                </TableCell>
                <TableCell className="text-right">
                  <span
                    className={
                      firm.rank <= 4
                        ? "font-semibold text-blue-500"
                        : "text-foreground"
                    }
                  >
                    {firm.market_share.toFixed(1)}%
                  </span>
                </TableCell>
                <TableCell className="text-right text-muted-foreground">
                  {formatRevenue(firm.revenue)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* CR4 summary */}
      {firms.length >= 4 && (
        <div className="flex items-center justify-end gap-2 text-sm">
          <span className="text-muted-foreground">CR4 Total:</span>
          <span className="font-semibold text-blue-500">
            {firms
              .slice(0, 4)
              .reduce((sum, f) => sum + f.market_share, 0)
              .toFixed(1)}
            %
          </span>
        </div>
      )}
    </div>
  );
}
