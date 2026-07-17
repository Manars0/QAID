# QAID

AI-powered Financial Risk, Fraud Detection & IFRS Compliance platform for ERP accounting systems.

## Run & Operate

- `artifacts/qaid: web` — React frontend (auto-started via workflow)
- `artifacts/api-server: API Server` — Python FastAPI backend (auto-started via workflow)
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec

## Stack

### Frontend (`artifacts/qaid/`)
- React + TypeScript + Vite
- TailwindCSS + shadcn/ui
- Recharts (charts), Framer Motion (animations), Lucide Icons
- next-themes (dark/light mode), wouter (routing)
- @tanstack/react-query for data fetching

### Backend (`artifacts/api-server/`)
- Python FastAPI + Uvicorn
- Pandas + NumPy (data processing)
- Scikit-Learn Isolation Forest (ML fraud detection)
- OpenPyXL + XlsxWriter (Excel reports)
- ReportLab (PDF reports)
- In-memory session storage (per restart)

### Shared
- `lib/api-spec/openapi.yaml` — OpenAPI spec (source of truth)
- `lib/api-client-react/` — Generated React Query hooks
- `lib/api-zod/` — Generated Zod validation schemas

## Where things live

- Landing page: `artifacts/qaid/src/pages/` (or `src/`)
- Dashboard: `artifacts/qaid/src/`
- API routes: `artifacts/api-server/routers/`
- ML analysis: `artifacts/api-server/services/analyzer.py`
- Rule engine: `artifacts/api-server/services/rule_engine.py`
- ML model: `artifacts/api-server/services/ml_analyzer.py`
- Demo data: `artifacts/api-server/services/demo_data.py`
- Report generation: `artifacts/api-server/services/report_generator.py`

## Architecture decisions

- **API-first**: All analysis happens server-side; frontend is pure visualization
- **In-memory sessions**: Sessions stored in Python dict keyed by UUID; cleared on restart (MVP)
- **Scoring formula**: Final Risk Score = 60% Rule Engine + 40% Isolation Forest ML
- **Rule weights**: 11 configurable financial rules, each weighted 30-100 points
- **No database**: Analysis results are ephemeral per session (by design for privacy)

## Product

- Upload ERP files (Excel, CSV, ZIP) or load built-in demo dataset
- Real ML analysis: Isolation Forest anomaly detection + financial rule engine
- Dashboard with KPIs, risk gauge, distribution charts, trend analysis
- IFRS compliance checks (IAS 1, IFRS 9, IAS 8, IAS 24, IFRS 15)
- Clickable entry detail with full rule breakdown
- Downloadable Excel and PDF reports
- English + Arabic (RTL) support, dark/light mode

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

- The Python backend uses in-memory session storage — sessions are lost on server restart
- After OpenAPI spec changes, run `pnpm --filter @workspace/api-spec run codegen` before touching frontend
- Python packages are managed via Replit's package manager, not requirements.txt pip install
- The `api-zod` tsconfig includes `"dom"` lib to support Blob/File types in generated code
- Report download uses direct `<a href>` links, not React Query (binary response)

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
