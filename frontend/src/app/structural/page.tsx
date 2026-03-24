"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { YearSelector } from "@/components/structural/year-selector";
import { CoefficientHeatmap } from "@/components/structural/coefficient-heatmap";
import { HeatmapDrillDown } from "@/components/structural/heatmap-drill-down";
import { ReproductionSankey } from "@/components/structural/reproduction-sankey";
import { ProportionalityBadge } from "@/components/structural/proportionality-badge";
import { ShockSimulator } from "@/components/structural/shock-simulator";
import { ShockResults } from "@/components/structural/shock-results";
import {
  fetchYears,
  fetchMatrix,
  fetchReproduction,
  fetchCriticalSectors,
  simulateShock,
  type MatrixResponse,
  type ReproductionResponse,
  type CriticalSectorsResponse,
  type ShockResultResponse,
  type ShockRequest,
} from "@/lib/structural-api";
import { RefreshCw } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type TabType = "matrix" | "shock" | "reproduction";

interface DataState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

// Default BEA benchmark years
const DEFAULT_YEARS = [1997, 2002, 2007, 2012, 2017, 2022];

/**
 * Main structural analysis page with I-O matrix, shock simulation, and reproduction schema.
 *
 * Features:
 * - Year selector controls all tabs
 * - Three tabs: I-O Matrix, Shock Simulation, Reproduction Schema
 * - Auto-fetch data based on active tab and selected year
 * - Manual refresh button
 */
export default function StructuralPage() {
  const [activeTab, setActiveTab] = useState<TabType>("matrix");
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Year state
  const [years, setYears] = useState<number[]>(DEFAULT_YEARS);
  const [selectedYear, setSelectedYear] = useState<number>(
    DEFAULT_YEARS[DEFAULT_YEARS.length - 1]
  );

  // Data states
  const [matrix, setMatrix] = useState<DataState<MatrixResponse>>({
    data: null,
    loading: false,
    error: null,
  });
  const [reproduction, setReproduction] = useState<
    DataState<ReproductionResponse>
  >({
    data: null,
    loading: false,
    error: null,
  });
  const [criticalSectors, setCriticalSectors] = useState<
    DataState<CriticalSectorsResponse>
  >({
    data: null,
    loading: false,
    error: null,
  });
  const [shockResult, setShockResult] =
    useState<DataState<ShockResultResponse>>({
      data: null,
      loading: false,
      error: null,
    });

  // Heatmap drill-down state
  const [drillDown, setDrillDown] = useState<{
    open: boolean;
    row: string;
    col: string;
    value: number;
  }>({
    open: false,
    row: "",
    col: "",
    value: 0,
  });

  // Fetch available years on mount
  useEffect(() => {
    const loadYears = async () => {
      try {
        const response = await fetchYears();
        if (response.years.length > 0) {
          setYears(response.years);
          setSelectedYear(response.years[response.years.length - 1]);
        }
      } catch (err) {
        console.error("Failed to fetch years:", err);
        // Keep default years on error
      }
    };
    loadYears();
  }, []);

  // Fetch data based on active tab
  const fetchTabData = useCallback(
    async (showLoading = true) => {
      if (activeTab === "matrix") {
        if (showLoading) setMatrix((prev) => ({ ...prev, loading: true }));
        try {
          const data = await fetchMatrix(selectedYear, "coefficients");
          setMatrix({ data, loading: false, error: null });
        } catch (err) {
          setMatrix({
            data: null,
            loading: false,
            error: err instanceof Error ? err.message : "Failed to load matrix",
          });
        }
      } else if (activeTab === "shock") {
        // Fetch matrix for industries list and critical sectors
        if (showLoading) {
          setMatrix((prev) => ({ ...prev, loading: true }));
          setCriticalSectors((prev) => ({ ...prev, loading: true }));
        }
        try {
          const [matrixData, sectorsData] = await Promise.all([
            fetchMatrix(selectedYear, "coefficients"),
            fetchCriticalSectors(selectedYear),
          ]);
          setMatrix({ data: matrixData, loading: false, error: null });
          setCriticalSectors({ data: sectorsData, loading: false, error: null });
        } catch (err) {
          const msg =
            err instanceof Error ? err.message : "Failed to load data";
          setMatrix((prev) => ({ ...prev, loading: false, error: msg }));
          setCriticalSectors((prev) => ({ ...prev, loading: false, error: msg }));
        }
      } else if (activeTab === "reproduction") {
        if (showLoading)
          setReproduction((prev) => ({ ...prev, loading: true }));
        try {
          const data = await fetchReproduction(selectedYear);
          setReproduction({ data, loading: false, error: null });
        } catch (err) {
          setReproduction({
            data: null,
            loading: false,
            error:
              err instanceof Error
                ? err.message
                : "Failed to load reproduction data",
          });
        }
      }
    },
    [activeTab, selectedYear]
  );

  // Fetch data when tab or year changes
  useEffect(() => {
    fetchTabData();
  }, [fetchTabData]);

  // Manual refresh
  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchTabData(false);
    setIsRefreshing(false);
  };

  // Shock simulation handler
  const handleSimulateShock = async (req: ShockRequest) => {
    setShockResult({ data: null, loading: true, error: null });
    try {
      const result = await simulateShock(req);
      setShockResult({ data: result, loading: false, error: null });
    } catch (err) {
      setShockResult({
        data: null,
        loading: false,
        error:
          err instanceof Error ? err.message : "Failed to simulate shock",
      });
    }
  };

  // Build industries list from matrix labels
  const industries =
    matrix.data?.col_labels.map((code) => ({
      code,
      name: code, // API may provide names in the future
    })) ?? [];

  // Tab configuration
  const tabs: { key: TabType; label: string }[] = [
    { key: "matrix", label: "I-O Matrix" },
    { key: "shock", label: "Shock Simulation" },
    { key: "reproduction", label: "Reproduction Schema" },
  ];

  return (
    <div className="space-y-6">
      {/* Controls row */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <YearSelector
          years={years}
          selected={selectedYear}
          onChange={setSelectedYear}
        />
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={isRefreshing}
        >
          <RefreshCw
            className={`mr-2 h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`}
          />
          Refresh
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        {tabs.map((tab) => (
          <Button
            key={tab.key}
            variant={activeTab === tab.key ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </Button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "matrix" && (
        <Card>
          <CardHeader>
            <CardTitle>Input-Output Coefficient Matrix ({selectedYear})</CardTitle>
          </CardHeader>
          <CardContent>
            {matrix.loading ? (
              <div className="flex h-[600px] items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
              </div>
            ) : matrix.error ? (
              <div className="flex h-[600px] items-center justify-center">
                <p className="text-sm text-destructive">{matrix.error}</p>
              </div>
            ) : matrix.data ? (
              <>
                <CoefficientHeatmap
                  matrixData={matrix.data}
                  onCellClick={(row, col, value) =>
                    setDrillDown({ open: true, row, col, value })
                  }
                />
                <HeatmapDrillDown
                  open={drillDown.open}
                  onClose={() => setDrillDown((prev) => ({ ...prev, open: false }))}
                  rowCode={drillDown.row}
                  colCode={drillDown.col}
                  value={drillDown.value}
                />
              </>
            ) : (
              <div className="flex h-[600px] items-center justify-center">
                <p className="text-sm text-muted-foreground">
                  No matrix data available.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === "shock" && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
          {/* Shock simulator form */}
          <div className="lg:col-span-4">
            <Card>
              <CardHeader>
                <CardTitle>Configure Shock</CardTitle>
              </CardHeader>
              <CardContent>
                {matrix.loading ? (
                  <div className="flex h-48 items-center justify-center">
                    <div className="h-6 w-6 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                  </div>
                ) : matrix.error ? (
                  <p className="text-sm text-destructive">{matrix.error}</p>
                ) : industries.length > 0 ? (
                  <ShockSimulator
                    industries={industries}
                    year={selectedYear}
                    onSimulate={handleSimulateShock}
                    loading={shockResult.loading}
                  />
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No industries available.
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Shock results */}
          <div className="lg:col-span-8">
            <ShockResults
              results={shockResult.data}
              loading={shockResult.loading}
            />
          </div>

          {/* Critical sectors table */}
          <div className="lg:col-span-12">
            <Card>
              <CardHeader>
                <CardTitle>Critical Sectors (High Linkage)</CardTitle>
              </CardHeader>
              <CardContent>
                {criticalSectors.loading ? (
                  <div className="flex h-32 items-center justify-center">
                    <div className="h-6 w-6 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                  </div>
                ) : criticalSectors.error ? (
                  <p className="text-sm text-destructive">
                    {criticalSectors.error}
                  </p>
                ) : criticalSectors.data ? (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Code</TableHead>
                          <TableHead>Name</TableHead>
                          <TableHead className="text-right">
                            Backward Linkage
                          </TableHead>
                          <TableHead className="text-right">
                            Forward Linkage
                          </TableHead>
                          <TableHead className="text-right">
                            Multiplier
                          </TableHead>
                          <TableHead className="text-center">Critical</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {criticalSectors.data.sectors
                          .filter((s) => s.critical)
                          .slice(0, 15)
                          .map((sector) => (
                            <TableRow key={sector.code}>
                              <TableCell className="font-mono text-sm">
                                {sector.code}
                              </TableCell>
                              <TableCell>{sector.name || "-"}</TableCell>
                              <TableCell className="text-right tabular-nums">
                                {sector.backward_linkage.toFixed(3)}
                              </TableCell>
                              <TableCell className="text-right tabular-nums">
                                {sector.forward_linkage.toFixed(3)}
                              </TableCell>
                              <TableCell className="text-right tabular-nums">
                                {sector.multiplier?.toFixed(3) || "-"}
                              </TableCell>
                              <TableCell className="text-center">
                                <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
                              </TableCell>
                            </TableRow>
                          ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No critical sector data available.
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {activeTab === "reproduction" && (
        <Card>
          <CardHeader>
            <CardTitle>
              Marx&apos;s Reproduction Schema ({selectedYear})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {reproduction.loading ? (
              <div className="flex h-[500px] items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
              </div>
            ) : reproduction.error ? (
              <div className="flex h-[500px] items-center justify-center">
                <p className="text-sm text-destructive">{reproduction.error}</p>
              </div>
            ) : reproduction.data ? (
              <div className="space-y-6">
                <ReproductionSankey reproductionData={reproduction.data} />
                <ProportionalityBadge
                  proportionality={reproduction.data.proportionality}
                />
              </div>
            ) : (
              <div className="flex h-[500px] items-center justify-center">
                <p className="text-sm text-muted-foreground">
                  No reproduction data available.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
