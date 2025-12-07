# src/dcf_model/data_fetcher.py

from __future__ import annotations

import pandas as pd
import yfinance as yf
from pathlib import Path


def build_company_financials_from_yahoo(
    ticker: str,
    save_to_csv: bool = True,
) -> pd.DataFrame:
    """
    Fetch basic financials from Yahoo Finance and reshape them into the format
    your assumption engine expects:

        Year, Revenue, EBIT, FCF

    Returns a DataFrame and (optionally) saves it under
    data/processed/<ticker>_financials.csv
    """

    t = yf.Ticker(ticker)

    # Income statement and cash flow (annual)
    income = t.financials.T        # rows: years, columns: line items
    cash = t.cashflow.T            # rows: years, columns: line items

    if income.empty or cash.empty:
        raise ValueError(f"No financials found for {ticker}")

    df = pd.DataFrame(index=income.index)
    df.index.name = "Date"

    # Revenue
    if "Total Revenue" in income.columns:
        df["Revenue"] = income["Total Revenue"]
    else:
        raise KeyError("Could not find 'Total Revenue' in income statement")

    # EBIT (name can vary slightly between sources; adjust if needed)
    if "Ebit" in income.columns:
        df["EBIT"] = income["Ebit"]
    elif "EBIT" in income.columns:
        df["EBIT"] = income["EBIT"]
    else:
        raise KeyError("Could not find 'Ebit' or 'EBIT' in income statement")
    
    # Possible column name variants
    ocf_candidates = [
        "Total Cash From Operating Activities",
        "Total Cash Flow From Operating Activities",
        "Operating Cash Flow",
        "Cash Flow From Operating Activities",
        "Cash Flow From Continuing Operating Activities",
    ]

    capex_candidates = [
        "Capital Expenditures",
        "Capital Expenditure",
        "Purchase of Property, Plant, and Equipment",
        "Additions to Property, Plant, and Equipment",
        "Net PPE Purchase And Sale",
        "Purchase Of PPE",
    ]

    # FCF = Operating Cash Flow + Capital Expenditures
    # (CapEx is usually negative, so + works out to OCF - |CapEx|)
    ocf_col = next((c for c in ocf_candidates if c in cash.columns), None)
    capex_col = next((c for c in capex_candidates if c in cash.columns), None)

    if "Free Cash Flow" in cash.columns:
        # Easiest: just use the Free Cash Flow line directly if it exists
        df["FCF"] = cash["Free Cash Flow"]
    elif ocf_col is not None and capex_col is not None:
        # Fallback: OCF + CapEx (CapEx is typically negative)
        df["FCF"] = cash[ocf_col] + cash[capex_col]
    else:
        raise KeyError(
            f"Could not compute FCF. Tried OCF candidates {ocf_candidates} and "
            f"CapEx candidates {capex_candidates}. Available columns: {list(cash.columns)}"
        )

    # Convert index from dates to plain years
    df = df.sort_index()
    df = df.reset_index()
    df["Year"] = df["Date"].dt.year
    df = df[["Year", "Revenue", "EBIT", "FCF"]]

    if save_to_csv:
        project_root = Path(__file__).resolve().parents[2]
        processed_dir = project_root / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)

        out_path = processed_dir / f"{ticker}_financials.csv"
        df.to_csv(out_path, index=False)
        print(f"Saved processed financials to: {out_path}")

    return df
