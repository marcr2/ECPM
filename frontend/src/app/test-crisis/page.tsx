"use client";

import { IndicatorChart } from "@/components/indicators/indicator-chart";
import { ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea } from "recharts";

export default function TestCrisisPage() {
  // Hardcoded test data spanning crisis periods
  const testData = [
    { date: "2005-01-01", value: 15 },
    { date: "2006-01-01", value: 16 },
    { date: "2007-01-01", value: 17 },
    { date: "2007-12-01", value: 16 }, // GFC start - EXACT MATCH
    { date: "2008-01-01", value: 14 },
    { date: "2008-06-01", value: 12 },
    { date: "2009-01-01", value: 11 },
    { date: "2009-06-01", value: 13 }, // GFC end - EXACT MATCH
    { date: "2010-01-01", value: 14 },
    { date: "2015-01-01", value: 18 },
    { date: "2019-01-01", value: 20 },
    { date: "2020-02-01", value: 19 }, // COVID start - EXACT MATCH
    { date: "2020-04-01", value: 15 }, // COVID end - EXACT MATCH
    { date: "2021-01-01", value: 18 },
    { date: "2022-01-01", value: 19 },
  ];

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Crisis Annotation Test</h1>
        <p className="text-muted-foreground">
          This chart has hardcoded data spanning 2005-2022 to test crisis annotations.
          Should show GFC (2007-2009) and COVID (2020) highlights.
        </p>
      </div>

      <div className="rounded-xl border border-border bg-card p-4">
        <h3 className="text-sm font-semibold mb-2">Using IndicatorChart Component</h3>
        <IndicatorChart
          data={testData}
          primaryKey="value"
          primaryLabel="Test Value"
          crisisMode="shaded"
          height={420}
        />
      </div>

      <div className="rounded-xl border border-border bg-card p-4">
        <h3 className="text-sm font-semibold mb-2">Direct Recharts Test (Manual ReferenceArea)</h3>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={testData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="value" stroke="#8884d8" />
            {/* Manual ReferenceArea for GFC */}
            <ReferenceArea
              x1="2007-12-01"
              x2="2009-06-01"
              fill="#ef4444"
              fillOpacity={0.3}
              label="GFC"
            />
            {/* Manual ReferenceArea for COVID */}
            <ReferenceArea
              x1="2020-02-01"
              x2="2020-04-01"
              fill="#06b6d4"
              fillOpacity={0.3}
              label="COVID"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-2">Debug Info</h2>
        <pre className="text-xs bg-muted p-4 rounded overflow-auto">
          {JSON.stringify({
            dataPoints: testData.length,
            dateRange: [testData[0].date, testData[testData.length-1].date],
            crisisDates: {
              gfc: { start: "2007-12-01", end: "2009-06-01" },
              covid: { start: "2020-02-01", end: "2020-04-01" }
            },
            exactMatches: {
              "2007-12-01": testData.some(d => d.date === "2007-12-01"),
              "2009-06-01": testData.some(d => d.date === "2009-06-01"),
              "2020-02-01": testData.some(d => d.date === "2020-02-01"),
              "2020-04-01": testData.some(d => d.date === "2020-04-01"),
            }
          }, null, 2)}
        </pre>
      </div>
    </div>
  );
}
