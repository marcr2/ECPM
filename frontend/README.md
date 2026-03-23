# ECPM Frontend

Frontend dashboard for the **Economic Crisis Prediction Model** — a Marxist political economy tool for tracking economic indicators, forecasting, and structural analysis.

## Tech Stack

- **Next.js 16** with App Router
- **React 19**
- **Tailwind CSS 4** + **shadcn/ui**
- **TanStack Table** for data grids
- **next-themes** (dark mode by default)

## Modules

| # | Module              | Status  | Description                                  |
|---|---------------------|---------|----------------------------------------------|
| 1 | Data Overview       | Active  | Browse economic series from FRED & BEA       |
| 2 | Indicators          | Planned | Derived Marxist political economy indicators |
| 3 | Forecasting         | Planned | Crisis probability forecasting               |
| 4 | Structural Analysis | Planned | Structural economic analysis                 |
| 5 | Concentration       | Planned | Capital concentration metrics                |

## Getting Started

### Prerequisites

- Node.js 20+
- The ECPM backend running (defaults to `http://localhost:8000`)

### Install & Run

```bash
npm install
npm run dev
```

The app starts at [http://localhost:3000](http://localhost:3000).

### Environment Variables

| Variable              | Default                  | Description       |
|-----------------------|--------------------------|-------------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000`  | Backend API URL   |

## Project Structure

```
src/
├── app/                  # Next.js App Router pages
│   ├── data/             # Data Overview page
│   ├── layout.tsx        # Root layout (sidebar + header)
│   └── page.tsx          # Redirects to /data
├── components/
│   ├── data/             # Data module components
│   ├── layout/           # Sidebar, Header
│   └── ui/               # shadcn/ui primitives
└── lib/
    ├── api.ts            # Backend API client
    └── utils.ts          # Utility functions
```
