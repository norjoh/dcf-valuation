# Valuation Engine Specification

## Model Type
- Equity valuation via FCFF Discounted Cash Flow (DCF)

## Core Financial Definitions

- Revenue: Top-line sales
- EBIT: Operating profit before interest and taxes
- FCF: Free Cash Flow to Firm
- WACC: Weighted Average Cost of Capital
- Terminal Growth: Long-term perpetual growth rate

## Projection Structure

Forecast horizon: 5–10 years

For each year:
- Revenue
- EBITDA (optional later)
- EBIT
- Taxes
- NOPAT
- Reinvestment
- FCFF

## Discounting

- FCFF discounted by WACC
- Terminal Value:
  - Gordon Growth Model
  - Must satisfy: terminal growth < WACC

## Sensitivity Analysis

- 2D Grid:
  - Rows: WACC
  - Columns: Terminal growth
- Output: Implied equity value per share

## Error Handling & Warnings

- Missing Revenue → Hard stop
- Missing EBIT → Hard stop
- Missing FCF → Hard stop
- Excessive history gaps → Warning
- Negative terminal spread → Hard stop

## Output Values

- Enterprise value
- Net debt
- Equity value
- Equity value per share
