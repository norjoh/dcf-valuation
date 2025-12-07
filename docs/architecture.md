# System Architecture

## High-Level Layers

1. Core Valuation Engine (Python)
   - Data fetching
   - Data cleaning & diagnostics
   - Assumption generation
   - Projections
   - Valuation
   - Sensitivity analysis

2. Analysis Orchestrator
   - Runs full valuation pipeline for one company
   - Aggregates outputs into a ValuationResult object

3. Output Layer
   - Excel generator
   - PowerPoint generator
   - Text/Markdown report generator

4. User Interface (Future)
   - CLI / Notebook (v1)
   - Web UI (FastAPI + Frontend)

## Core Objects

- ValuationInputs
- ValuationAssumptions
- ValuationResult
- FetchDiagnostics
- DataQualityReport
- SensitivityResult
- CompsResult (later)

## Data Flow

Yahoo Finance → Data Fetcher → Quality Checks → Metrics →  
Assumptions → Projections → Valuation → Sensitivity →  
Excel / PPTX / UI

## AI Integration Policy

- AI may explain, summarize, and verbalize results.
- AI must not generate financial inputs directly.
- All numbers must come from deterministic code paths.

---

## Version Control Principles

- All valuation logic is version-controlled.
- All documentation changes tracked.
- No hidden runtime parameter defaults.
