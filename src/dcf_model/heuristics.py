# src/dcf_model/heuristics.py

from dataclasses import dataclass
from typing import Dict

from .auto_metrics import HistoricalMetrics
from .assumptions import (
    DCFAssumptions,
    GrowthAssumptions,
    MarginAssumptions,
    WACCInputs,
)


@dataclass
class AssumptionSuggestions:
    """Store three scenario suggestion sets."""
    bear: DCFAssumptions
    base: DCFAssumptions
    bull: DCFAssumptions


def suggest_growth_from_metrics(
    metrics: HistoricalMetrics, years: int = 5
) -> Dict[str, GrowthAssumptions]:
    """
    Very simple heuristic:
    - base: a bit below historical 5Y CAGR (if available)
    - bear: base - 3pp (floored at 0)
    - bull: base + 3pp
    """
    if metrics.revenue_cagr_5y is None:
        # fallback: generic assumptions
        base_growth = 0.05
    else:
        # e.g. clamp between 2% and 15%
        base_growth = max(min(metrics.revenue_cagr_5y * 0.8, 0.15), 0.02)

    bear_growth = max(base_growth - 0.03, 0.0)
    bull_growth = min(base_growth + 0.03, 0.20)

    yearly = {i: base_growth for i in range(1, years + 1)}
    yearly_bear = {i: bear_growth for i in range(1, years + 1)}
    yearly_bull = {i: bull_growth for i in range(1, years + 1)}

    return {
        "bear": GrowthAssumptions(yearly_growth=yearly_bear),
        "base": GrowthAssumptions(yearly_growth=yearly),
        "bull": GrowthAssumptions(yearly_growth=yearly_bull),
    }


def suggest_margins_from_metrics(
    metrics: HistoricalMetrics, years: int = 5
) -> Dict[str, MarginAssumptions]:
    """
    Simple margin heuristic:
    - base: around historical avg EBIT margin
    - bear: a bit lower
    - bull: a bit higher
    """
    if metrics.avg_ebit_margin_5y is None:
        base_margin = 0.15
    else:
        base_margin = metrics.avg_ebit_margin_5y

    bear_margin = max(base_margin - 0.03, 0.05)
    bull_margin = min(base_margin + 0.03, 0.40)

    yearly_base = {i: base_margin for i in range(1, years + 1)}
    yearly_bear = {i: bear_margin for i in range(1, years + 1)}
    yearly_bull = {i: bull_margin for i in range(1, years + 1)}

    return {
        "bear": MarginAssumptions(ebit_margin_by_year=yearly_bear),
        "base": MarginAssumptions(ebit_margin_by_year=yearly_base),
        "bull": MarginAssumptions(ebit_margin_by_year=yearly_bull),
    }


def suggest_wacc_and_terminal_growth(
    country: str = "developed", sector: str = "generic"
) -> Dict[str, Dict]:
    """
    Very rough placeholders – you can refine based on real data later.
    Returns dictionaries that can be passed into WACCInputs + g.
    """
    # Defaults you can calibrate later
    rf = 0.03
    erp = 0.05

    if sector.lower() in {"tech", "growth"}:
        beta = 1.2
    else:
        beta = 1.0

    cost_of_debt = rf + 0.02  # simple spread
    tax_rate = 0.22
    equity_weight = 0.7
    debt_weight = 0.3

    # Terminal growth ranges
    if country.lower() in {"norway", "europe", "developed"}:
        g_base = 0.02
    else:
        g_base = 0.03

    suggestions = {
        "bear": {
            "wacc_inputs": WACCInputs(
                risk_free_rate=rf,
                beta=beta,
                equity_risk_premium=erp,
                cost_of_debt=cost_of_debt,
                tax_rate=tax_rate,
                equity_weight=0.6,
                debt_weight=0.4,
            ),
            "terminal_growth": max(g_base - 0.01, 0.0),
        },
        "base": {
            "wacc_inputs": WACCInputs(
                risk_free_rate=rf,
                beta=beta,
                equity_risk_premium=erp,
                cost_of_debt=cost_of_debt,
                tax_rate=tax_rate,
                equity_weight=0.7,
                debt_weight=0.3,
            ),
            "terminal_growth": g_base,
        },
        "bull": {
            "wacc_inputs": WACCInputs(
                risk_free_rate=rf,
                beta=beta,
                equity_risk_premium=erp,
                cost_of_debt=cost_of_debt,
                tax_rate=tax_rate,
                equity_weight=0.8,
                debt_weight=0.2,
            ),
            "terminal_growth": g_base + 0.005,
        },
    }

    return suggestions


def build_assumption_suggestions(
    metrics: HistoricalMetrics,
    years: int = 5,
    country: str = "developed",
    sector: str = "generic",
) -> AssumptionSuggestions:
    growth = suggest_growth_from_metrics(metrics, years=years)
    margins = suggest_margins_from_metrics(metrics, years=years)
    wacc_and_g = suggest_wacc_and_terminal_growth(country=country, sector=sector)

    def make_scenario(name: str) -> DCFAssumptions:
        wg = wacc_and_g[name]
        return DCFAssumptions(
            growth=growth[name],
            margins=margins[name],
            wacc_inputs=wg["wacc_inputs"],
            terminal_growth=wg["terminal_growth"],
        )

    return AssumptionSuggestions(
        bear=make_scenario("bear"),
        base=make_scenario("base"),
        bull=make_scenario("bull"),
    )
