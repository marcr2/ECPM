"use client";

import { useMemo } from "react";
import { ResponsiveSankey } from "@nivo/sankey";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type {
  ReproductionResponse,
  SankeyData,
  ConstantCapitalUnit,
  LaborSurplusUnit,
} from "@/lib/structural-api";

function formatC(value: number, unit: ConstantCapitalUnit) {
  return value.toLocaleString(undefined, {
    maximumFractionDigits: unit === "millions_of_dollars" ? 1 : 3,
  });
}

function formatVS(value: number, unit: LaborSurplusUnit) {
  return value.toLocaleString(undefined, {
    maximumFractionDigits: unit === "billions_of_dollars" ? 2 : 1,
  });
}

/** Sankey link/node magnitudes: millions USD when Use table is dollar flows; else coefficient sums. */
function sankeyFlowUnitPhrase(cUnit: ConstantCapitalUnit): {
  isDollars: boolean;
  shortLabel: string;
  sentenceFragment: string;
} {
  if (cUnit === "millions_of_dollars") {
    return {
      isDollars: true,
      shortLabel: "mn US$",
      sentenceFragment: "million US dollars (BEA Use table, same scale as intermediate flows)",
    };
  }
  return {
    isDollars: false,
    shortLabel: "I–O coeffs",
    sentenceFragment: "sum of technical coefficients",
  };
}

const SANKEY_TOOLTIP_PANEL_CLASS =
  "rounded-md border border-border bg-card px-4 py-3 text-sm shadow-lg leading-relaxed min-w-[min(22rem,calc(100vw-2rem))] max-w-xl";

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
  // Build an acyclic 4-node graph from the 2x2 inter-department flows matrix.
  // Left side = what each department produces; right side = who buys it.
  const sankeyData: SankeyData = useMemo(() => {
    const flows = reproductionData.flows;

    return {
      nodes: [
        { id: "I_prod", label: "Machinery & Materials produced" },
        { id: "II_prod", label: "Consumer Goods produced" },
        { id: "I_buy", label: "Bought by Dept I" },
        { id: "II_buy", label: "Bought by Dept II" },
      ],
      links: [
        { source: "I_prod", target: "I_buy", value: flows[0]?.[0] ?? 0 },
        { source: "I_prod", target: "II_buy", value: flows[0]?.[1] ?? 0 },
        { source: "II_prod", target: "I_buy", value: flows[1]?.[0] ?? 0 },
        { source: "II_prod", target: "II_buy", value: flows[1]?.[1] ?? 0 },
      ].filter((l) => l.value > 0),
    };
  }, [reproductionData]);

  // Calculate totals for display
  const totalFlow = sankeyData.links.reduce((sum, l) => sum + l.value, 0);

  // Department c/v/s values
  const deptI = reproductionData.dept_i;
  const deptII = reproductionData.dept_ii;

  const cUnit = reproductionData.constant_capital_unit;
  const vsUnit = reproductionData.labor_and_surplus_unit;
  const flowUnit = sankeyFlowUnitPhrase(cUnit);

  const intermediateSublabel =
    cUnit === "coefficient_column_sum"
      ? "Intermediate inputs (sum of technical coefficients)"
      : "Intermediate inputs (mn $)";
  const wagesSublabel =
    vsUnit === "billions_of_dollars"
      ? "Wages & compensation (bn $)"
      : "Wages & compensation (mn $)";
  const surplusSublabel =
    vsUnit === "billions_of_dollars"
      ? "Gross operating surplus (bn $)"
      : "Gross operating surplus (mn $)";

  return (
    <div className="space-y-4">
      {/* Sankey diagram */}
      <div className="h-[400px] w-full">
        <ResponsiveSankey
          data={sankeyData}
          margin={{ top: 40, right: 160, bottom: 40, left: 230 }}
          label={(node) => (node as { label?: string }).label ?? String(node.id)}
          align="justify"
          colors={(node) => {
            const id = String(node.id);
            if (id.startsWith("I_")) return "#3b82f6"; // blue = Dept I
            // Slightly brighter green so thin Dept II ribbons stay visible on dark UI
            return "#4ade80";
          }}
          nodeOpacity={1}
          nodeHoverOpacity={1}
          nodeThickness={22}
          nodeSpacing={24}
          nodeBorderWidth={0}
          nodeBorderRadius={3}
          // Default Nivo linkBlendMode is "multiply", which crushes luminance on dark
          // backgrounds—especially when Dept II flows are thin after dollar scaling.
          linkBlendMode="normal"
          linkOpacity={0.78}
          linkHoverOpacity={0.95}
          linkContract={3}
          enableLinkGradient={false}
          labelPosition="outside"
          labelOrientation="horizontal"
          labelPadding={16}
          labelTextColor={{ from: "color", modifiers: [["brighter", 0.8]] }}
          nodeTooltip={({ node }) => (
            <div className={SANKEY_TOOLTIP_PANEL_CLASS}>
              <div className="font-medium">{node.label || node.id}</div>
              <div className="text-muted-foreground">
                {flowUnit.isDollars ? (
                  <>
                    Flow total:{" "}
                    <span className="font-medium text-foreground">
                      {node.value?.toLocaleString(undefined, {
                        maximumFractionDigits: 2,
                      })}{" "}
                      {flowUnit.shortLabel}
                    </span>
                    <span className="block text-xs mt-1 opacity-90">
                      ({flowUnit.sentenceFragment})
                    </span>
                  </>
                ) : (
                  <>
                    Aggregate:{" "}
                    <span className="font-medium text-foreground">
                      {node.value?.toLocaleString(undefined, {
                        maximumFractionDigits: 2,
                      })}
                    </span>
                    <span className="block text-xs mt-1 opacity-90">
                      {flowUnit.sentenceFragment}
                    </span>
                  </>
                )}
                <span className="block mt-1">
                  {((node.value ?? 0) / totalFlow * 100).toFixed(1)}% of chart total
                </span>
              </div>
            </div>
          )}
          linkTooltip={({ link }) => {
            const srcId = String(link.source.id);
            const tgtId = String(link.target.id);
            const seller = srcId.startsWith("I_") ? "Dept I" : "Dept II";
            const goods = srcId.startsWith("I_") ? "machinery & materials" : "consumer goods";
            const buyer = tgtId === "I_buy" ? "Dept I" : "Dept II";
            return (
              <div className={SANKEY_TOOLTIP_PANEL_CLASS}>
                <div className="font-medium">
                  {seller} sells {goods} to {buyer}
                </div>
                <div className="text-muted-foreground">
                  {flowUnit.isDollars ? (
                    <>
                      <span className="font-medium text-foreground">
                        {link.value.toLocaleString(undefined, {
                          maximumFractionDigits: 2,
                        })}{" "}
                        {flowUnit.shortLabel}
                      </span>
                      <span className="block text-xs mt-1 opacity-90">
                        ({flowUnit.sentenceFragment})
                      </span>
                    </>
                  ) : (
                    <>
                      <span className="font-medium text-foreground">
                        {link.value.toLocaleString(undefined, {
                          maximumFractionDigits: 2,
                        })}
                      </span>
                      <span className="block text-xs mt-1 opacity-90">
                        {flowUnit.sentenceFragment}
                      </span>
                    </>
                  )}
                  <span className="block mt-1">
                    {((link.value / totalFlow) * 100).toFixed(1)}% of chart total
                  </span>
                </div>
              </div>
            );
          }}
          theme={{
            text: {
              fill: "var(--muted-foreground)",
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
                  {formatC(deptI.c, cUnit)}
                </p>
                <p className="text-xs text-muted-foreground">c (Constant Capital)</p>
                <p className="text-[10px] text-muted-foreground/60">
                  {intermediateSublabel}
                </p>
              </div>
              <div>
                <p className="text-2xl font-bold tabular-nums">
                  {formatVS(deptI.v, vsUnit)}
                </p>
                <p className="text-xs text-muted-foreground">v (Variable Capital)</p>
                <p className="text-[10px] text-muted-foreground/60">{wagesSublabel}</p>
              </div>
              <div>
                <p className="text-2xl font-bold tabular-nums">
                  {formatVS(deptI.s, vsUnit)}
                </p>
                <p className="text-xs text-muted-foreground">s (Surplus Value)</p>
                <p className="text-[10px] text-muted-foreground/60">{surplusSublabel}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-green-400" />
              Department II (Means of Consumption)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold tabular-nums">
                  {formatC(deptII.c, cUnit)}
                </p>
                <p className="text-xs text-muted-foreground">c (Constant Capital)</p>
                <p className="text-[10px] text-muted-foreground/60">
                  {intermediateSublabel}
                </p>
              </div>
              <div>
                <p className="text-2xl font-bold tabular-nums">
                  {formatVS(deptII.v, vsUnit)}
                </p>
                <p className="text-xs text-muted-foreground">v (Variable Capital)</p>
                <p className="text-[10px] text-muted-foreground/60">{wagesSublabel}</p>
              </div>
              <div>
                <p className="text-2xl font-bold tabular-nums">
                  {formatVS(deptII.s, vsUnit)}
                </p>
                <p className="text-xs text-muted-foreground">s (Surplus Value)</p>
                <p className="text-[10px] text-muted-foreground/60">{surplusSublabel}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
