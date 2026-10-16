import pytest

from src.phase2_valuation.leases import value_with_leases
from src.phase2_valuation.monte_carlo import Uncertainty, simulate
from src.phase2_valuation.yields import discount_rate
from tests.test_leases import KRONBORGSVAGEN_20

EXIT_YIELD = 0.059797

NO_UNCERTAINTY = Uncertainty(
    exit_yield_sd=0,
    market_rent_sd=0,
    indexation_sd=0,
    void_years_distribution=((1, 1.0),),
    renewal_probability=1.0,
)


def test_without_uncertainty_every_simulation_equals_the_base_case():
    base = value_with_leases(KRONBORGSVAGEN_20, 5, discount_rate(EXIT_YIELD, 0.02), EXIT_YIELD).market_value
    result = simulate(KRONBORGSVAGEN_20, EXIT_YIELD, 5, NO_UNCERTAINTY, n_simulations=20)
    assert result.values == pytest.approx([base] * 20)


def test_same_seed_gives_same_result():
    first = simulate(KRONBORGSVAGEN_20, EXIT_YIELD, 5, n_simulations=200, seed=1)
    second = simulate(KRONBORGSVAGEN_20, EXIT_YIELD, 5, n_simulations=200, seed=1)
    assert first.values == second.values


def test_distribution_is_spread_around_the_base_case():
    result = simulate(KRONBORGSVAGEN_20, EXIT_YIELD, 5, n_simulations=2_000)
    assert result.percentile(10) < 41_142_351 < result.percentile(90)
    assert result.percentile(10) < result.percentile(50) < result.percentile(90)
    assert 0 < result.probability_below(38_000_000) < 0.5
