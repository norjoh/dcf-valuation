# src/dcf_model/auto_metrics.py

import pandas as pd
import numpy as np
from dataclasses import dataclass


@dataclass
class HistoricalMetrics:
    revenue_cagr_5y: float | None
    avg_ebit_margin_5y: float | None
    avg_fcf_margin_5y: float | None


def compute_cagr(series: pd.Series) -> float | None:
    """Compute CAGR for the period covered by the series, ignoring NaNs."""
    series = series.dropna()
    if len(series) < 2:
        return None

    start = series.iloc[0]
    end = series.iloc[-1]
    n_years = len(series) - 1

    if start <= 0 or end <= 0:
        return None

    return (end / start) ** (1 / n_years) - 1


def compute_historical_metrics(financials: pd.DataFrame) -> HistoricalMetrics:
    """
    Expects columns: 'Revenue', 'EBIT', 'FCF'.
    Index should be years or datelike.
    Drops rows with missing key values before computing metrics.
    """
    # Keep only rows where all three fields exist
    df = financials.copy()
    df = df.dropna(subset=["Revenue", "EBIT", "FCF"]).sort_index()

    # If we have fewer than 2 years, we can't compute anything sensible
    if len(df) < 2:
        return HistoricalMetrics(
            revenue_cagr_5y=None,
            avg_ebit_margin_5y=None,
            avg_fcf_margin_5y=None,
        )

    last_5 = df.tail(5)

    # CAGR of revenue
    revenue_cagr_5y = compute_cagr(last_5["Revenue"])

    # Average EBIT margin
    ebit_margin = last_5["EBIT"] / last_5["Revenue"]
    ebit_margin = ebit_margin.replace([np.inf, -np.inf], np.nan).dropna()
    avg_ebit_margin_5y = float(ebit_margin.mean()) if len(ebit_margin) else None

    # Average FCF margin
    fcf_margin = last_5["FCF"] / last_5["Revenue"]
    fcf_margin = fcf_margin.replace([np.inf, -np.inf], np.nan).dropna()
    avg_fcf_margin_5y = float(fcf_margin.mean()) if len(fcf_margin) else None

    return HistoricalMetrics(
        revenue_cagr_5y=revenue_cagr_5y,
        avg_ebit_margin_5y=avg_ebit_margin_5y,
        avg_fcf_margin_5y=avg_fcf_margin_5y,
    )
