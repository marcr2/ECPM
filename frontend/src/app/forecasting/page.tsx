"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CrisisGauge } from "@/components/forecasting/crisis-gauge";
import { ForecastChart } from "@/components/forecasting/forecast-chart";
import { BacktestTimeline } from "@/components/forecasting/backtest-timeline";
import { TrainingStatus } from "@/components/forecasting/training-status";
import { RegimeDetail } from "@/components/forecasting/regime-detail";
import {
  fetchCrisisIndex,
  fetchRegime,
  fetchForecasts,
  fetchBacktests,
  type CrisisIndex,
  type RegimeResult,
  type ForecastsResponse,
  type BacktestsResponse,
} from "@/lib/forecast-api";
import { RefreshCw } from "lucide-react";

type TabType = "forecasts" | "backtests" | "training";

interface DataState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/**
 * Main forecasting page with crisis index, forecasts, backtests, and training.
 *
 * Features:
 * - Hero section with crisis gauge
 * - Main grid with forecast chart and regime detail
 * - Tabbed section for forecasts, backtests, and training
 * - Auto-refresh every 60s
 * - Manual refresh button
 */
export default function ForecastingPage() {
  const [activeTab, setActiveTab] = useState<TabType>("forecasts");
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Data states
  const [crisisIndex, setCrisisIndex] = useState<DataState<CrisisIndex>>({
    data: null,
    loading: true,
    error: null,
  });
  const [regime, setRegime] = useState<DataState<RegimeResult>>({
    data: null,
    loading: true,
    error: null,
  });
  const [forecasts, setForecasts] = useState<DataState<ForecastsResponse>>({
    data: null,
    loading: true,
    error: null,
  });
  const [backtests, setBacktests] = useState<DataState<BacktestsResponse>>({
    data: null,
    loading: true,
    error: null,
  });

  // Fetch all data
  const fetchAllData = useCallback(async (showLoading = true) => {
    if (showLoading) {
      setCrisisIndex((prev) => ({ ...prev, loading: true }));
      setRegime((prev) => ({ ...prev, loading: true }));
      setForecasts((prev) => ({ ...prev, loading: true }));
      setBacktests((prev) => ({ ...prev, loading: true }));
    }

    // Fetch in parallel
    const results = await Promise.allSettled([
      fetchCrisisIndex(),
      fetchRegime(),
      fetchForecasts(),
      fetchBacktests(),
    ]);

    // Process results
    if (results[0].status === "fulfilled") {
      setCrisisIndex({ data: results[0].value, loading: false, error: null });
    } else {
      setCrisisIndex({ data: null, loading: false, error: results[0].reason?.message || "Failed to load crisis index" });
    }

    if (results[1].status === "fulfilled") {
      setRegime({ data: results[1].value, loading: false, error: null });
    } else {
      setRegime({ data: null, loading: false, error: results[1].reason?.message || "Failed to load regime" });
    }

    if (results[2].status === "fulfilled") {
      setForecasts({ data: results[2].value, loading: false, error: null });
    } else {
      setForecasts({ data: null, loading: false, error: results[2].reason?.message || "Failed to load forecasts" });
    }

    if (results[3].status === "fulfilled") {
      setBacktests({ data: results[3].value, loading: false, error: null });
    } else {
      setBacktests({ data: null, loading: false, error: results[3].reason?.message || "Failed to load backtests" });
    }
  }, []);

  // Initial fetch and auto-refresh
  useEffect(() => {
    fetchAllData();

    // Auto-refresh every 60s
    const interval = setInterval(() => {
      fetchAllData(false); // Silent refresh
    }, 60000);

    return () => clearInterval(interval);
  }, [fetchAllData]);

  // Manual refresh
  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchAllData(false);
    setIsRefreshing(false);
  };

  // After training completes, refresh all data
  const handleTrainingComplete = () => {
    fetchAllData(false);
  };

  // Get first forecast for main chart
  const firstForecast = forecasts.data?.forecasts
    ? Object.values(forecasts.data.forecasts)[0]
    : null;

  const tabs: { key: TabType; label: string }[] = [
    { key: "forecasts", label: "Forecasts" },
    { key: "backtests", label: "Backtests" },
    { key: "training", label: "Training" },
  ];

  return (
    <div className="space-y-6">
      {/* Refresh button */}
      <div className="flex justify-end">
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

      {/* Hero section: Crisis gauge */}
      <CrisisGauge
        data={crisisIndex.data}
        loading={crisisIndex.loading}
        regimeLabel={regime.data?.regime_label}
      />

      {/* Main grid: Forecast chart + Regime detail */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        {/* Forecast chart (8 cols) */}
        <div className="lg:col-span-8">
          {firstForecast ? (
            <ForecastChart data={firstForecast} />
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>VAR Forecasts</CardTitle>
              </CardHeader>
              <CardContent>
                {forecasts.loading ? (
                  <div className="flex h-[350px] items-center justify-center">
                    <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    {forecasts.error || "No forecast data available. Run training first."}
                  </p>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Regime detail (4 cols) */}
        <div className="lg:col-span-4">
          <RegimeDetail data={regime.data} loading={regime.loading} />
        </div>
      </div>

      {/* Tabs section */}
      <Card>
        <CardHeader className="pb-2">
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
        </CardHeader>
        <CardContent>
          {activeTab === "forecasts" && (
            <div className="space-y-4">
              {forecasts.data?.forecasts ? (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  {Object.values(forecasts.data.forecasts).map((forecast) => (
                    <ForecastChart
                      key={forecast.indicator}
                      data={forecast}
                      title={forecast.indicator}
                    />
                  ))}
                </div>
              ) : forecasts.loading ? (
                <div className="flex h-48 items-center justify-center">
                  <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  {forecasts.error || "No forecast data available. Run training first."}
                </p>
              )}
            </div>
          )}

          {activeTab === "backtests" && (
            <BacktestTimeline backtests={backtests.data?.backtests || []} />
          )}

          {activeTab === "training" && (
            <TrainingStatus onTrainingComplete={handleTrainingComplete} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
