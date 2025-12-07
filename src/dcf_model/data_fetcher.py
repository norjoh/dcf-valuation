# src/dcf_model/data_fetcher.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Literal

import pandas as pd
import yfinance as yf


FCFMode = Literal["free_cash_flow_line", "ocf_plus_capex"]


@dataclass
class FetchDiagnostics:
    ticker: str
    used_revenue_col: str
    used_ebit_col: str
    used_fcf_mode: FCFMode
    used_ocf_col: Optional[str]
    used_capex_col: Optional[str]


def _is_financial_institution(ticker: str, income: pd.DataFrame, info: dict) -> bool:
    """
    Heuristic check for banks/insurers/financials where EBIT-based FCFF DCF
    is not appropriate.

    Uses sector/industry metadata primarily, with income statement as a weak hint.
    """
    sector = str(info.get("sector", "")).lower()
    industry = str(info.get("industry", "")).lower()
    text = f"{sector} {industry}"

    financial_keywords = [
        "bank",
        "banks",
        "financial services",
        "insurance",
        "insurer",
        "capital markets",
        "diversified financial",
        "investment banking",
        "asset management",
        "thrifts & mortgage",
        "consumer finance",
    ]

    if any(k in text for k in financial_keywords):
        return True


def build_company_financials_from_yahoo(
    ticker: str,
    save_to_csv: bool = True,
) -> tuple[pd.DataFrame, FetchDiagnostics]:
    """
    Fetch basic financials from Yahoo Finance and reshape them into the format
    your assumption engine expects:

        Year, Revenue, EBIT, FCF

    Returns:
        (df, diagnostics)
        df: DataFrame with columns [Year, Revenue, EBIT, FCF]
        diagnostics: which line items / method were used

    Raises:
        ValueError / KeyError on missing or unusable data.
    """
    t = yf.Ticker(ticker)

    # Income statement and cash flow (annual)
    income = t.financials.T        # rows: dates, columns: line items
    cash = t.cashflow.T            # rows: dates, columns: line items

    # Basic existence checks
    if income.empty and cash.empty:
        raise ValueError(f"[{ticker}] No financials found (income and cash flow both empty).")

    if income.empty:
        raise ValueError(f"[{ticker}] Income statement is empty; cannot derive Revenue/EBIT.")

    if cash.empty:
        raise ValueError(f"[{ticker}] Cash flow statement is empty; cannot derive FCF.")

    # Try to get sector/industry info for classification
    try:
        info = t.info or {}
    except Exception:
        info = {}

    if _is_financial_institution(ticker, income, info):
        raise ValueError(
            f"[{ticker}] appears to be a financial institution (bank/insurer/financial). "
            "EBIT-based FCFF DCF is not appropriate. Use a financials-specific valuation model."
        )

    df = pd.DataFrame(index=income.index)
    df.index.name = "Date"

    # ---- Revenue ----
    revenue_candidates = ["Total Revenue", "Revenue"]
    revenue_col = next((c for c in revenue_candidates if c in income.columns), None)
    if revenue_col is None:
        raise KeyError(
            f"[{ticker}] Could not find any revenue column among {revenue_candidates}. "
            f"Available income statement columns: {list(income.columns)}"
        )
    df["Revenue"] = income[revenue_col]

    # ---- EBIT ----
    # Adjust these candidates if you want a different EBIT definition
    ebit_candidates = ["Ebit", "EBIT", "Operating Income"]
    ebit_col = next((c for c in ebit_candidates if c in income.columns), None)
    if ebit_col is None:
        raise KeyError(
            f"[{ticker}] Could not find any EBIT-like column among {ebit_candidates}. "
            f"Available income statement columns: {list(income.columns)}"
        )
    df["EBIT"] = income[ebit_col]

    # ---- FCF ----
    # Try to use Yahoo's own free cash flow line if available
    fcf_mode: FCFMode
    used_ocf_col: Optional[str] = None
    used_capex_col: Optional[str] = None

    if "Free Cash Flow" in cash.columns:
        df["FCF"] = cash["Free Cash Flow"]
        fcf_mode = "free_cash_flow_line"
    else:
        # Possible column name variants for operating cash flow
        ocf_candidates = [
            "Total Cash From Operating Activities",
            "Total Cash Flow From Operating Activities",
            "Operating Cash Flow",
            "Cash Flow From Operating Activities",
            "Cash Flow From Continuing Operating Activities",
        ]

        # Possible column name variants for capex
        capex_candidates = [
            "Capital Expenditures",
            "Capital Expenditure",
            "Net PPE Purchase And Sale",
            "Purchase Of PPE",
        ]

        ocf_col = next((c for c in ocf_candidates if c in cash.columns), None)
        capex_col = next((c for c in capex_candidates if c in cash.columns), None)

        if ocf_col is None or capex_col is None:
            raise KeyError(
                f"[{ticker}] Could not compute FCF: missing both a clear operating cash flow "
                f"and capex column. Tried OCF candidates {ocf_candidates} and "
                f"CapEx candidates {capex_candidates}. "
                f"Available cash flow columns: {list(cash.columns)}"
            )

        # CapEx is typically negative, so OCF + CapEx ≈ FCF
        df["FCF"] = cash[ocf_col] + cash[capex_col]
        fcf_mode = "ocf_plus_capex"
        used_ocf_col = ocf_col
        used_capex_col = capex_col

    # ---- Year conversion ----
    df = df.sort_index()
    df = df.reset_index()
    if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
        df["Date"] = pd.to_datetime(df["Date"])
    df["Year"] = df["Date"].dt.year
    df = df[["Year", "Revenue", "EBIT", "FCF"]]

    if save_to_csv:
        project_root = Path(__file__).resolve().parents[2]
        processed_dir = project_root / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)

        out_path = processed_dir / f"{ticker}_financials.csv"
        df.to_csv(out_path, index=False)
        print(f"Saved processed financials to: {out_path}")

    diagnostics = FetchDiagnostics(
        ticker=ticker,
        used_revenue_col=revenue_col,
        used_ebit_col=ebit_col,
        used_fcf_mode=fcf_mode,
        used_ocf_col=used_ocf_col,
        used_capex_col=used_capex_col,
    )

    return df, diagnostics
