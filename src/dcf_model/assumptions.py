# src/dcf_model/assumptions.py

from dataclasses import dataclass
from typing import Dict, Literal


@dataclass
class GrowthAssumptions:
    """Per-year revenue growth for the explicit forecast period."""
    yearly_growth: Dict[int, float]


@dataclass
class MarginAssumptions:
    """Simple example: EBIT margin per year (as decimals, e.g. 0.18 = 18%)."""
    ebit_margin_by_year: Dict[int, float]


@dataclass
class WACCInputs:
    risk_free_rate: float
    beta: float
    equity_risk_premium: float
    cost_of_debt: float
    tax_rate: float
    equity_weight: float
    debt_weight: float


@dataclass
class DCFAssumptions:
    """Bundle all assumption types for convenient passing into the model."""
    growth: GrowthAssumptions
    margins: MarginAssumptions
    wacc_inputs: WACCInputs
    terminal_growth: float

    @property
    def wacc(self) -> float:
        ke = self.wacc_inputs.risk_free_rate + (
            self.wacc_inputs.beta * self.wacc_inputs.equity_risk_premium
        )
        kd_after_tax = self.wacc_inputs.cost_of_debt * (1 - self.wacc_inputs.tax_rate)
        return (
            self.wacc_inputs.equity_weight * ke
            + self.wacc_inputs.debt_weight * kd_after_tax
        )


def choose_scenario(
    suggestions: Dict[str, "DCFAssumptions"],
    scenario: Literal["bear", "base", "bull"] = "base",
) -> DCFAssumptions:
    """Convenience helper: pick one of several pre-built assumption sets."""
    return suggestions[scenario]
