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
    name: "Oil/Stagflation",
    startDate: "1973-11-01",
    endDate: "1975-03-01",
    color: "#f97316",
  },
  {
    name: "Volcker Recession",
    startDate: "1980-01-01",
    endDate: "1982-11-01",
    color: "#eab308",
  },
  {
    name: "Dot-com",
    startDate: "2001-03-01",
    endDate: "2001-11-01",
    color: "#a855f7",
  },
  {
    name: "Global Financial Crisis",
    startDate: "2007-12-01",
    endDate: "2009-06-01",
    color: "#ef4444",
  },
  {
    name: "COVID Recession",
    startDate: "2020-02-01",
    endDate: "2020-04-01",
    color: "#06b6d4",
  },
];
