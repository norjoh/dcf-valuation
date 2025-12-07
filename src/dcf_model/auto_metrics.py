# src/dcf_model/auto_metrics.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, List

import numpy as np
import pandas as pd


@dataclass
class DataQualityReport:
    n_original_rows: int
    n_rows_after_cleaning: int
    dropped_years: list[Hashable]
    missing_columns: list[str]
    notes: list[str]


@dataclass
class HistoricalMetrics:
    revenue_cagr_5y: float | None
    avg_ebit_margin_5y: float | None
    avg_fcf_margin_5y: float | None


def _safe_cagr(series: pd.Series) -> float | None:
    """Compute CAGR over the given series, ignoring NaNs. Returns None if not meaningful."""
    series = series.dropna()
    if len(series) < 2:
        return None

    start = series.iloc[0]
    end = series.iloc[-1]
    n_years = len(series) - 1

    if start <= 0 or end <= 0:
        return None

    return (end / start) ** (1 / n_years) - 1


def compute_historical_metrics(
    financials: pd.DataFrame,
) -> tuple[HistoricalMetrics, DataQualityReport]:
    """
    Expects columns: 'Year', 'Revenue', 'EBIT', 'FCF' (Year can be index or column).

    Returns:
        (metrics, data_quality)
    """
    df = financials.copy()

    # If Year is a column but not the index, use it as a label for diagnostics
    if "Year" in df.columns and df.index.name != "Year":
        index_labels = df["Year"].tolist()
    else:
        index_labels = df.index.tolist()

    required_cols = ["Revenue", "EBIT", "FCF"]
    missing_cols = [c for c in required_cols if c not in df.columns]

    n_original = len(df)

    # Drop rows with missing core values *only* for metric calculation,
    # but report what was dropped.
    present_required = [c for c in required_cols if c in df.columns]
    df_clean = df.dropna(subset=present_required).copy()
    n_after = len(df_clean)

    dropped_years = []
    if n_original != n_after:
        kept_indices = set(df_clean.index.tolist())
        dropped_years = [label for idx, label in zip(df.index, index_labels) if idx not in kept_indices]

    notes: list[str] = []
    if missing_cols:
        notes.append(f"Missing columns for metrics: {missing_cols}")
    if dropped_years:
        notes.append(f"Dropped {len(dropped_years)} rows due to NaNs in {present_required}: {dropped_years}")

    # Default: no metrics
    metrics = HistoricalMetrics(
        revenue_cagr_5y=None,
        avg_ebit_margin_5y=None,
        avg_fcf_margin_5y=None,
    )

    if len(df_clean) >= 2 and not missing_cols:
        df_clean = df_clean.sort_values("Year" if "Year" in df_clean.columns else df_clean.index.name)
        last_5 = df_clean.tail(5)

        rev_cagr = _safe_cagr(last_5["Revenue"])

        ebit_margin = (last_5["EBIT"] / last_5["Revenue"]).replace(
            [np.inf, -np.inf], np.nan
        ).dropna()
        fcf_margin = (last_5["FCF"] / last_5["Revenue"]).replace(
            [np.inf, -np.inf], np.nan
        ).dropna()

        metrics = HistoricalMetrics(
            revenue_cagr_5y=rev_cagr,
            avg_ebit_margin_5y=float(ebit_margin.mean()) if len(ebit_margin) else None,
            avg_fcf_margin_5y=float(fcf_margin.mean()) if len(fcf_margin) else None,
        )
    else:
        notes.append(
            f"Insufficient clean data to compute metrics "
            f"(rows_after_cleaning={len(df_clean)}, missing_cols={missing_cols})."
        )

    quality = DataQualityReport(
        n_original_rows=n_original,
        n_rows_after_cleaning=n_after,
        dropped_years=dropped_years,
        missing_columns=missing_cols,
        notes=notes,
    )

    return metrics, quality
