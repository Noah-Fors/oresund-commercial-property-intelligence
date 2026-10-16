"""Steg 5a: känslighetsanalys.

Tvåvägsmatris: marknadsvärdet när exit yield och marknadshyra varieras
samtidigt. Discount rate följer alltid med yielden (yield + KPI).
"""

import pandas as pd

from .leases import PropertyCashFlowAssumptions, value_with_leases
from .yields import discount_rate

DEFAULT_YIELD_STEPS = (-0.005, -0.0025, 0.0, 0.0025, 0.005)
DEFAULT_RENT_STEPS = (-0.10, -0.05, 0.0, 0.05, 0.10)


def yield_rent_matrix(
    assumptions: PropertyCashFlowAssumptions,
    exit_yield: float,
    holding_period_years: int,
    yield_steps: tuple[float, ...] = DEFAULT_YIELD_STEPS,
    rent_steps: tuple[float, ...] = DEFAULT_RENT_STEPS,
) -> pd.DataFrame:
    """Rader = exit yield, kolumner = marknadshyra år 1 (kr/kvm), värden = marknadsvärde."""
    rents = [assumptions.market_rent_per_sqm * (1 + step) for step in rent_steps]
    yields = [exit_yield + step for step in yield_steps]
    matrix = {
        rent: [
            value_with_leases(
                assumptions.model_copy(update={"market_rent_per_sqm": rent}),
                holding_period_years,
                discount_rate(y, assumptions.indexation),
                y,
            ).market_value
            for y in yields
        ]
        for rent in rents
    }
    frame = pd.DataFrame(matrix, index=yields)
    frame.index.name = "exit_yield"
    frame.columns.name = "market_rent_per_sqm"
    return frame
