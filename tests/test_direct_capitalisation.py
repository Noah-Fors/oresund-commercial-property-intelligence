"""Räkneexemplet Kronborgsvägen 20, löst för hand i Excel innan koden skrevs."""

import pytest
from pydantic import ValidationError

from src.phase2_valuation.direct_capitalisation import (
    OperatingAssumptions,
    direct_capitalisation_value,
    gross_potential_rent,
    noi,
    rental_income,
)

KRONBORGSVAGEN_20 = OperatingAssumptions(
    area_sqm=2_000,
    market_rent_per_sqm=1_800,
    vacancy_rate=0.08,
    operating_cost_per_sqm=350,
    maintenance_per_sqm=80,
    property_tax=180_000,
)


def test_gross_potential_rent():
    assert gross_potential_rent(KRONBORGSVAGEN_20) == pytest.approx(3_600_000)


def test_rental_income_after_vacancy():
    assert rental_income(KRONBORGSVAGEN_20) == pytest.approx(3_312_000)


def test_noi():
    assert noi(KRONBORGSVAGEN_20) == pytest.approx(2_272_000)


def test_market_value_and_value_per_sqm():
    value = direct_capitalisation_value(noi(KRONBORGSVAGEN_20), required_yield=0.0525)
    assert value == pytest.approx(43_276_190.48, abs=0.01)
    assert value / KRONBORGSVAGEN_20.area_sqm == pytest.approx(21_638.10, abs=0.01)


def test_yield_expansion_lowers_value_by_8_7_percent():
    before = direct_capitalisation_value(2_272_000, 0.0525)
    after = direct_capitalisation_value(2_272_000, 0.0575)
    assert after == pytest.approx(39_513_043.48, abs=0.01)
    assert 1 - after / before == pytest.approx(0.0870, abs=0.0001)


def test_vacancy_rate_must_be_a_fraction():
    # 8 istället för 0.08 är ett vanligt misstag och ska stoppas direkt.
    with pytest.raises(ValidationError):
        OperatingAssumptions(**(KRONBORGSVAGEN_20.model_dump() | {"vacancy_rate": 8}))


def test_yield_must_be_positive():
    with pytest.raises(ValueError):
        direct_capitalisation_value(2_272_000, 0)
