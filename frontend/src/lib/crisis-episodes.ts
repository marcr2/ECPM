export interface CrisisEpisode {
  name: string;
  startDate: string; // ISO date string (YYYY-MM-DD)
  endDate: string; // ISO date string
  color: string; // CSS color for shading
}

export const CRISIS_EPISODES: CrisisEpisode[] = [
  {
    name: "Great Depression",
    startDate: "1929-10-01",
    endDate: "1933-03-01",
    color: "#ef4444",
  },
  {
    name: "Post-War Transition",
    startDate: "1948-11-01",
    endDate: "1949-10-01",
    color: "#64748b",
  },
  {
    name: "Post-Korean War",
    startDate: "1953-07-01",
    endDate: "1954-05-01",
    color: "#8b5cf6",
  },
  {
    name: "Asian Flu Recession",
    startDate: "1957-08-01",
    endDate: "1958-04-01",
    color: "#14b8a6",
  },
  {
    name: "Monetary Tightening",
    startDate: "1960-04-01",
    endDate: "1961-02-01",
    color: "#0ea5e9",
  },
  {
    name: "Vietnam Era",
    startDate: "1969-12-01",
    endDate: "1970-11-01",
    color: "#84cc16",
  },
  {
    name: "Oil Shock",
    startDate: "1973-11-01",
    endDate: "1975-03-01",
    color: "#f97316",
  },
  {
    name: "First Volcker",
    startDate: "1980-01-01",
    endDate: "1980-07-01",
    color: "#eab308",
  },
  {
    name: "Double-Dip",
    startDate: "1981-07-01",
    endDate: "1982-11-01",
    color: "#f59e0b",
  },
  {
    name: "Gulf War",
    startDate: "1990-07-01",
    endDate: "1991-03-01",
    color: "#ec4899",
  },
  {
    name: "Dot-Com Crash",
    startDate: "2001-03-01",
    endDate: "2001-11-01",
    color: "#a855f7",
  },
  {
    name: "Great Recession",
    startDate: "2007-12-01",
    endDate: "2009-06-01",
    color: "#ef4444",
  },
  {
    name: "COVID-19",
    startDate: "2020-02-01",
    endDate: "2020-04-01",
    color: "#06b6d4",
  },
  {
    name: "Post-Pandemic Inflation",
    startDate: "2021-03-01",
    endDate: "2023-06-01",
    color: "#f43f5e",
  },
];
