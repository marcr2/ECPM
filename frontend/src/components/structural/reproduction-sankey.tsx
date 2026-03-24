"use client";

import { useMemo } from "react";
import { ResponsiveSankey } from "@nivo/sankey";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ReproductionResponse, SankeyData } from "@/lib/structural-api";

interface ReproductionSankeyProps {
  reproductionData: ReproductionResponse;
}

/**
 * Sankey diagram for Marx's reproduction schema.
 * Shows flows between Department I (means of production) and Department II (means of consumption).
 *
 * Colors: Dept I = blue, Dept II = green
 */
export function ReproductionSankey({
  reproductionData,
}: ReproductionSankeyProps) {
  // Build sankey data from flows if not provided
  const sankeyData: SankeyData = useMemo(() => {
    if (reproductionData.sankey_data) {
      return reproductionData.sankey_data;
    }

    // Construct from flows matrix
    // flows[0][0] = I->I, flows[0][1] = I->II
    // flows[1][0] = II->I, flows[1][1] = II->II
    const flows = reproductionData.flows;

    return {
      nodes: [
        { id: "I_out", label: "Dept I Output" },
        { id: "II_out", label: "Dept II Output" },
        { id: "I_in", label: "Dept I Input" },
        { id: "II_in", label: "Dept II Input" },
      ],
      links: [
        { source: "I_out", target: "I_in", value: flows[0]?.[0] ?? 0 },
        { source: "I_out", target: "II_in", value: flows[0]?.[1] ?? 0 },
        { source: "II_out", target: "I_in", value: flows[1]?.[0] ?? 0 },
        { source: "II_out", target: "II_in", value: flows[1]?.[1] ?? 0 },
      ].filter((l) => l.value > 0),
    };
  }, [reproductionData]);

  // Calculate totals for display
  const totalFlow = sankeyData.links.reduce((sum, l) => sum + l.value, 0);

  // Department c/v/s values
  const deptI = reproductionData.dept_i;
  const deptII = reproductionData.dept_ii;

  return (
    <div className="space-y-4">
      {/* Sankey diagram */}
      <div className="h-[400px] w-full">
        <ResponsiveSankey
          data={sankeyData}
          margin={{ top: 40, right: 160, bottom: 40, left: 50 }}
          align="justify"
          colors={(node) => {
            const id = String(node.id);
            if (id.startsWith("I")) return "#3b82f6"; // blue
            return "#22c55e"; // green
          }}
          nodeOpacity={1}
          nodeHoverOpacity={1}
          nodeThickness={18}
          nodeSpacing={24}
          nodeBorderWidth={0}
          nodeBorderRadius={3}
          linkOpacity={0.5}
          linkHoverOpacity={0.8}
          linkContract={3}
          enableLinkGradient={true}
          labelPosition="outside"
          labelOrientation="horizontal"
          labelPadding={16}
          labelTextColor={{ from: "color", modifiers: [["brighter", 0.8]] }}
          nodeTooltip={({ node }) => (
            <div className="rounded-md border border-border bg-card px-3 py-2 text-sm shadow-lg">
              <div className="font-medium">{node.label || node.id}</div>
              <div className="text-muted-foreground">
                Total: {node.value?.toLocaleString(undefined, {
                  maximumFractionDigits: 0,
                })} ({((node.value ?? 0) / totalFlow * 100).toFixed(1)}%)
              </div>
            </div>
          )}
          linkTooltip={({ link }) => (
            <div className="rounded-md border border-border bg-card px-3 py-2 text-sm shadow-lg">
              <div className="font-medium">
                {String(link.source.id).replace("_out", "")} &rarr;{" "}
                {String(link.target.id).replace("_in", "")}
              </div>
              <div className="text-muted-foreground">
                Flow: {link.value.toLocaleString(undefined, {
                  maximumFractionDigits: 0,
                })} ({((link.value / totalFlow) * 100).toFixed(1)}%)
              </div>
            </div>
          )}
          theme={{
            text: {
              fill: "hsl(var(--muted-foreground))",
              fontSize: 12,
            },
          }}
        />
      </div>

      {/* Department c/v/s breakdown cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-blue-500" />
              Department I (Means of Production)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold tabular-nums">
                  {deptI.c.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
                <p className="text-xs text-muted-foreground">c (Constant)</p>
              </div>
              <div>
                <p className="text-2xl font-bold tabular-nums">
                  {deptI.v.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
                <p className="text-xs text-muted-foreground">v (Variable)</p>
              </div>
              <div>
                <p className="text-2xl font-bold tabular-nums">
                  {deptI.s.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
                <p className="text-xs text-muted-foreground">s (Surplus)</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-green-500" />
              Department II (Means of Consumption)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold tabular-nums">
                  {deptII.c.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
                <p className="text-xs text-muted-foreground">c (Constant)</p>
              </div>
              <div>
                <p className="text-2xl font-bold tabular-nums">
                  {deptII.v.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
                <p className="text-xs text-muted-foreground">v (Variable)</p>
              </div>
              <div>
                <p className="text-2xl font-bold tabular-nums">
                  {deptII.s.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
                <p className="text-xs text-muted-foreground">s (Surplus)</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
