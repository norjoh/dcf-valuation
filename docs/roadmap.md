# Project Roadmap

## Phase 1 — Core DCF Engine (Current)
- Data fetching (Yahoo Finance)
- Data quality & diagnostics system
- Historical metrics (growth, margins)
- Assumption engine (growth, margins, WACC, terminal growth)
- Projection engine
- Discounted cash flow valuation
- Sensitivity analysis (WACC × terminal growth)
- Unit tests and synthetic test companies

## Phase 2 — Excel Model Export
- Input assumptions sheet
- Historical financials sheet
- Forecast financials sheet
- DCF calculation sheet
- Sensitivity matrix sheet
- Fully formula-driven Excel model

## Phase 3 — Comparable Companies (Comps)
- Manual peer group input
- Multiples: EV/EBIT, EV/EBITDA, P/E, growth
- Peer summary statistics
- Implied valuation from comps
- Excel export for comps

## Phase 4 — Qualitative Analysis
- PDF report parsing (annual & quarterly)
- Management outlook extraction
- Risk factor summaries
- Recent company news integration

## Phase 5 — User Interface
- CLI or notebook-based valuation wizard
- Web backend (FastAPI)
- Frontend UI (React or Streamlit)

## Phase 6 — AI & Advanced Risk Modeling
- AI-generated report drafts
- Macro scenario overlays
- Probabilistic valuation bands
- Model risk scoring

---

## Maintenance & Governance
- Continuous test coverage
- Design documentation updates
- Validation of assumptions framework
