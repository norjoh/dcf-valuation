# src/dcf_model/heuristics.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .auto_metrics import HistoricalMetrics, DataQualityReport
from .assumptions import (
    DCFAssumptions,
    GrowthAssumptions,
    MarginAssumptions,
    WACCInputs,
)


@dataclass
class AssumptionWarnings:
    messages: list[str]


@dataclass
class AssumptionSuggestions:
    """Store three scenario suggestion sets."""
    bear: DCFAssumptions
    base: DCFAssumptions
    bull: DCFAssumptions
    warnings: AssumptionWarnings


def suggest_growth_from_metrics(
    metrics: HistoricalMetrics,
    quality: DataQualityReport,
    years: int,
    *,
    fallback_growth: float | None = None,
) -> tuple[Dict[str, GrowthAssumptions], AssumptionWarnings]:
    """
    Construct bear/base/bull growth assumptions.

    - If metrics.revenue_cagr_5y is available: use it directly as base (or transform if you want).
    - If not, only use fallback_growth if explicitly provided.
    - Otherwise, return an empty suggestion dict with warnings.
    """
    warnings: list[str] = []

    if metrics.revenue_cagr_5y is not None:
        base_growth = metrics.revenue_cagr_5y
        warnings.append(
            f"Base revenue growth derived from 5Y CAGR={metrics.revenue_cagr_5y:.2%}. "
            f"Data quality notes: {quality.notes}"
        )
    elif fallback_growth is not None:
        base_growth = fallback_growth
        warnings.append(
            f"No valid 5Y revenue CAGR computed; using explicit fallback_growth={fallback_growth:.2%}. "
            f"Data quality notes: {quality.notes}"
        )
    else:
        warnings.append(
            "No valid 5Y revenue CAGR and no fallback_growth provided. "
            "Growth assumptions not generated."
        )
        return {}, AssumptionWarnings(warnings)

    # Here, bear/base/bull are still a modelling choice around base_growth.
    bear_growth = max(base_growth - 0.03, 0.0)
    bull_growth = base_growth + 0.03

    yearly_base = {i: base_growth for i in range(1, years + 1)}
    yearly_bear = {i: bear_growth for i in range(1, years + 1)}
    yearly_bull = {i: bull_growth for i in range(1, years + 1)}

    suggestions: Dict[str, GrowthAssumptions] = {
        "bear": GrowthAssumptions(yearly_growth=yearly_bear),
        "base": GrowthAssumptions(yearly_growth=yearly_base),
        "bull": GrowthAssumptions(yearly_growth=yearly_bull),
    }

    return suggestions, AssumptionWarnings(warnings)


def suggest_margins_from_metrics(
    metrics: HistoricalMetrics,
    quality: DataQualityReport,
    years: int,
    *,
    fallback_margin: float | None = None,
) -> tuple[Dict[str, MarginAssumptions], AssumptionWarnings]:
    """
    Construct bear/base/bull EBIT margin assumptions.

    Same philosophy as growth: no internal hardcoded fallback; caller supplies fallback if desired.
    """
    warnings: list[str] = []

    if metrics.avg_ebit_margin_5y is not None:
        base_margin = metrics.avg_ebit_margin_5y
        warnings.append(
            f"Base EBIT margin derived from 5Y average={metrics.avg_ebit_margin_5y:.2%}. "
            f"Data quality notes: {quality.notes}"
        )
    elif fallback_margin is not None:
        base_margin = fallback_margin
        warnings.append(
            f"No valid 5Y EBIT margin; using explicit fallback_margin={fallback_margin:.2%}. "
            f"Data quality notes: {quality.notes}"
        )
    else:
        warnings.append(
            "No valid 5Y EBIT margin and no fallback_margin provided. "
            "Margin assumptions not generated."
        )
        return {}, AssumptionWarnings(warnings)

    bear_margin = max(base_margin - 0.03, 0.0)
    bull_margin = base_margin + 0.03

    yearly_base = {i: base_margin for i in range(1, years + 1)}
    yearly_bear = {i: bear_margin for i in range(1, years + 1)}
    yearly_bull = {i: bull_margin for i in range(1, years + 1)}

    suggestions: Dict[str, MarginAssumptions] = {
        "bear": MarginAssumptions(ebit_margin_by_year=yearly_bear),
        "base": MarginAssumptions(ebit_margin_by_year=yearly_base),
        "bull": MarginAssumptions(ebit_margin_by_year=yearly_bull),
    }

    return suggestions, AssumptionWarnings(warnings)


def build_assumption_suggestions(
    metrics: HistoricalMetrics,
    quality: DataQualityReport,
    years: int,
    *,
    wacc_inputs_bear: WACCInputs,
    wacc_inputs_base: WACCInputs,
    wacc_inputs_bull: WACCInputs,
    terminal_growth_bear: float,
    terminal_growth_base: float,
    terminal_growth_bull: float,
    fallback_growth: float | None = None,
    fallback_margin: float | None = None,
) -> AssumptionSuggestions:
    """
    High-level helper to combine growth, margin, and WACC/terminal g into DCFAssumptions
    for bear/base/bull, with explicit inputs for all WACC/terminal choices.

    There are no hardcoded numeric defaults here; all WACC/terminal parameters
    must be passed in explicitly by the caller.
    """
    growth_suggestions, growth_warn = suggest_growth_from_metrics(
        metrics, quality, years, fallback_growth=fallback_growth
    )
    margin_suggestions, margin_warn = suggest_margins_from_metrics(
        metrics, quality, years, fallback_margin=fallback_margin
    )

    warnings = AssumptionWarnings(messages=[*growth_warn.messages, *margin_warn.messages])

    if not growth_suggestions or not margin_suggestions:
        # Let the caller decide how to handle "no suggestions".
        raise ValueError(
            "Could not generate growth/margin suggestions; see warnings for details: "
            f"{warnings.messages}"
        )

    bear = DCFAssumptions(
        growth=growth_suggestions["bear"],
        margins=margin_suggestions["bear"],
        wacc_inputs=wacc_inputs_bear,
        terminal_growth=terminal_growth_bear,
    )
    base = DCFAssumptions(
        growth=growth_suggestions["base"],
        margins=margin_suggestions["base"],
        wacc_inputs=wacc_inputs_base,
        terminal_growth=terminal_growth_base,
    )
    bull = DCFAssumptions(
        growth=growth_suggestions["bull"],
        margins=margin_suggestions["bull"],
        wacc_inputs=wacc_inputs_bull,
        terminal_growth=terminal_growth_bull,
    )

    return AssumptionSuggestions(bear=bear, base=base, bull=bull, warnings=warnings)
