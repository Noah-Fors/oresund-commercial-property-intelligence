"""Steg 5b: Monte Carlo-simulering av marknadsvärdet.

Varje simulering slumpar fram ett möjligt utfall för de osäkra antagandena
och räknar marknadsvärdet med samma DCF som annars. Efter tusentals
simuleringar får man en fördelning av möjliga värden istället för en siffra.

Antagandena slumpas oberoende av varandra. I verkligheten hänger de ihop
(i en lågkonjunktur stiger ofta yields samtidigt som hyrorna faller), så
spridningen här är snarare för liten än för stor.
"""

import numpy as np
from pydantic import BaseModel, Field

from .leases import PropertyCashFlowAssumptions, value_with_leases
from .yields import discount_rate


class Uncertainty(BaseModel):
    """Hur osäkert varje antagande är. Standardavvikelser i decimalform."""

    exit_yield_sd: float = Field(0.005, ge=0, description="±0,50 procentenheter.")
    market_rent_sd: float = Field(0.075, ge=0, description="±7,5 % av marknadshyran.")
    indexation_sd: float = Field(0.0075, ge=0, description="±0,75 procentenheter.")
    # Tomställning för hyresgäster som flyttar: (antal år, sannolikhet).
    void_years_distribution: tuple[tuple[int, float], ...] = ((0, 0.25), (1, 0.50), (2, 0.25))
    renewal_probability: float = Field(0.70, ge=0, le=1, description="Att en hyresgäst som väntas stanna gör det.")
    void_years_if_not_renewed: int = Field(1, ge=0)


class MonteCarloResult(BaseModel):
    values: list[float]

    def percentile(self, p: float) -> float:
        return float(np.percentile(self.values, p))

    @property
    def mean(self) -> float:
        return float(np.mean(self.values))

    def probability_below(self, threshold: float) -> float:
        return float(np.mean(np.array(self.values) < threshold))


def simulate(
    base: PropertyCashFlowAssumptions,
    exit_yield: float,
    holding_period_years: int,
    uncertainty: Uncertainty = Uncertainty(),
    n_simulations: int = 10_000,
    seed: int = 42,
) -> MonteCarloResult:
    """Marknadsvärdet i `n_simulations` slumpade scenarier.

    `seed` gör att samma slumptal kommer varje gång, så resultatet går att återskapa.
    """
    rng = np.random.default_rng(seed)
    void_options, void_probabilities = zip(*uncertainty.void_years_distribution)

    values = []
    for _ in range(n_simulations):
        sim_yield = max(rng.normal(exit_yield, uncertainty.exit_yield_sd), 0.01)
        sim_rent = base.market_rent_per_sqm * max(1 + rng.normal(0, uncertainty.market_rent_sd), 0.1)
        sim_kpi = rng.normal(base.indexation, uncertainty.indexation_sd)

        leases = []
        for lease in base.leases:
            if lease.void_years_after_expiry > 0:
                void = int(rng.choice(void_options, p=void_probabilities))
            elif rng.random() < uncertainty.renewal_probability:
                void = 0
            else:
                void = uncertainty.void_years_if_not_renewed
            leases.append(lease.model_copy(update={"void_years_after_expiry": void}))

        scenario = base.model_copy(
            update={"leases": leases, "market_rent_per_sqm": sim_rent, "indexation": sim_kpi}
        )
        result = value_with_leases(
            scenario, holding_period_years, discount_rate(sim_yield, sim_kpi), sim_yield
        )
        values.append(result.market_value)

    return MonteCarloResult(values=values)
