"""Kronborgsvägen 20 med två hyresgäster, löst i Excel innan koden skrevs."""

import pytest

from src.phase2_valuation.leases import (
    Lease,
    PropertyCashFlowAssumptions,
    costs,
    lease_rent,
    noi,
    stabilised_exit,
    value_with_leases,
    wault,
)

TENANT_A = Lease(tenant="A", area_sqm=1_200, contract_rent_per_sqm=1_700, expiry_year=2, void_years_after_expiry=1)
TENANT_B = Lease(tenant="B", area_sqm=800, contract_rent_per_sqm=1_900, expiry_year=5)

KRONBORGSVAGEN_20 = PropertyCashFlowAssumptions(
    leases=[TENANT_A, TENANT_B],
    market_rent_per_sqm=1_800,
    indexation=0.02,
    opex_per_sqm=430,
    property_tax=180_000,
)


def test_wault():
    assert wault([TENANT_A, TENANT_B]) == pytest.approx(3.28, abs=0.005)


def test_tenant_a_pays_contract_rent_then_void_then_market_rent():
    rents = [lease_rent(TENANT_A, KRONBORGSVAGEN_20, year) for year in range(1, 7)]
    assert rents == pytest.approx([2_040_000, 2_080_800, 0, 2_292_209, 2_338_053, 2_384_815], abs=1)


def test_tenant_b_is_over_rented_and_reverts_down_in_year_6():
    rents = [lease_rent(TENANT_B, KRONBORGSVAGEN_20, year) for year in range(1, 7)]
    assert rents == pytest.approx([1_520_000, 1_550_400, 1_581_408, 1_613_036, 1_645_297, 1_589_876], abs=1)
    assert rents[5] < rents[4]


def test_costs_cover_whole_building_even_when_vacant():
    assert costs(KRONBORGSVAGEN_20, 1) == pytest.approx(1_040_000)
    assert costs(KRONBORGSVAGEN_20, 3) == pytest.approx(1_082_016, abs=1)


def test_noi_per_year():
    assert [noi(KRONBORGSVAGEN_20, year) for year in range(1, 7)] == pytest.approx(
        [2_520_000, 2_570_400, 499_392, 2_801_589, 2_857_621, 2_826_447], abs=1
    )


def test_market_value_with_five_year_dcf():
    result = value_with_leases(KRONBORGSVAGEN_20, holding_period_years=5, discount_rate=0.0725, exit_yield=0.0525)
    assert [y.present_value for y in result.years] == pytest.approx(
        [2_349_650, 2_234_633, 404_809, 2_117_460, 2_013_808], abs=1
    )
    assert result.exit_value == pytest.approx(53_837_083, abs=1)
    assert result.pv_exit_value == pytest.approx(37_939_798, abs=1)
    assert result.market_value == pytest.approx(47_060_158, abs=1)


def test_tenant_leaving_at_exit_is_valued_as_let_minus_lost_rent():
    b_leaves = TENANT_B.model_copy(update={"void_years_after_expiry": 1})
    scenario = KRONBORGSVAGEN_20.model_copy(update={"leases": [TENANT_A, b_leaves]})
    exit_noi, deduction = stabilised_exit(scenario, holding_period_years=5)
    assert exit_noi == pytest.approx(noi(KRONBORGSVAGEN_20, 6))
    assert deduction == pytest.approx(lease_rent(TENANT_B, KRONBORGSVAGEN_20, 6))
    leaves = value_with_leases(scenario, 5, 0.0725, 0.0525).market_value
    stays = value_with_leases(KRONBORGSVAGEN_20, 5, 0.0725, 0.0525).market_value
    assert leaves < stays


def test_lease_running_past_exit_has_no_void_deduction():
    long_lease = TENANT_B.model_copy(update={"expiry_year": 10})
    scenario = KRONBORGSVAGEN_20.model_copy(update={"leases": [TENANT_A, long_lease]})
    assert stabilised_exit(scenario, holding_period_years=5)[1] == 0
