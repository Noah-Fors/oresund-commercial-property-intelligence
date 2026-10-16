"""Mini-DCF för Kronborgsvägen 20, löst i Excel innan koden skrevs."""

import pytest

from src.phase2_valuation.dcf import discount_factor, discounted_cash_flow, growing_noi
from src.phase2_valuation.direct_capitalisation import direct_capitalisation_value

NOI_YEAR_1 = 2_272_000
KPI = 0.02
DISCOUNT_RATE = 0.0725
EXIT_YIELD = 0.0525


@pytest.fixture
def three_year_dcf():
    noi = growing_noi(NOI_YEAR_1, KPI, years=4)
    return discounted_cash_flow(noi[:3], exit_noi=noi[3], discount_rate=DISCOUNT_RATE, exit_yield=EXIT_YIELD)


def test_noi_grows_with_kpi():
    assert growing_noi(NOI_YEAR_1, KPI, years=4) == pytest.approx(
        [2_272_000, 2_317_440, 2_363_788.8, 2_411_064.58], abs=0.01
    )


def test_discount_factor_year_1_is_less_than_one():
    assert discount_factor(DISCOUNT_RATE, 0) == 1
    assert discount_factor(DISCOUNT_RATE, 1) == pytest.approx(0.9324, abs=0.0001)


def test_present_value_per_year(three_year_dcf):
    assert [y.present_value for y in three_year_dcf.years] == pytest.approx(
        [2_118_415, 2_014_716, 1_916_094], abs=1
    )


def test_exit_value_and_its_present_value(three_year_dcf):
    assert three_year_dcf.exit_value == pytest.approx(45_925_040, abs=1)
    assert three_year_dcf.pv_exit_value == pytest.approx(37_226_965, abs=1)


def test_market_value_does_not_double_count_year_4(three_year_dcf):
    assert three_year_dcf.market_value == pytest.approx(43_276_190, abs=1)


def test_dcf_equals_direct_capitalisation_when_growth_is_constant(three_year_dcf):
    # Gordon growth: discount rate = yield + tillväxt och exit yield = dagens yield.
    assert three_year_dcf.market_value == pytest.approx(
        direct_capitalisation_value(NOI_YEAR_1, EXIT_YIELD), rel=1e-9
    )


def test_most_of_the_value_comes_from_exit(three_year_dcf):
    assert three_year_dcf.exit_share_of_value == pytest.approx(0.86, abs=0.005)


def test_holding_period_must_be_at_least_one_year():
    with pytest.raises(ValueError):
        discounted_cash_flow([], exit_noi=1, discount_rate=DISCOUNT_RATE, exit_yield=EXIT_YIELD)
