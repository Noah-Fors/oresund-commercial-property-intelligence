"""Kronborgsvägen 20 med location score 36,8, löst i Excel innan koden skrevs."""

import pytest

from src.phase1_location_scoring.models import City, PropertyType
from src.phase2_valuation.leases import value_with_leases
from src.phase2_valuation.yields import (
    BASE_YIELDS,
    discount_rate,
    location_yield_adjustment,
    required_yield,
)
from tests.test_leases import KRONBORGSVAGEN_20

ORIGINAL_VALUE = 47_060_158


def test_normal_location_gets_base_yield():
    assert location_yield_adjustment(60) == 0
    assert required_yield(PropertyType.OFFICE, City.MALMO, 60) == pytest.approx(0.0525)


def test_adjustment_is_asymmetric_and_bounded():
    assert location_yield_adjustment(100) > -0.0050
    assert location_yield_adjustment(0) < 0.0100
    assert abs(location_yield_adjustment(0)) > abs(location_yield_adjustment(100))


def test_better_location_never_increases_yield():
    scores = range(0, 101, 10)
    yields = [required_yield(PropertyType.OFFICE, City.MALMO, s) for s in scores]
    assert yields == sorted(yields, reverse=True)


def test_every_property_type_and_city_has_a_base_yield():
    for property_type in PropertyType:
        assert set(BASE_YIELDS[property_type]) == set(City)


def test_kronborgsvagen_yield_and_value():
    y = required_yield(PropertyType.OFFICE, City.MALMO, 36.8)
    assert y == pytest.approx(0.059797, abs=0.000001)
    assert discount_rate(y, 0.02) == pytest.approx(0.079797, abs=0.000001)

    result = value_with_leases(KRONBORGSVAGEN_20, 5, discount_rate(y, 0.02), y)
    assert result.market_value == pytest.approx(41_142_351, abs=1)
    assert result.market_value / ORIGINAL_VALUE - 1 == pytest.approx(-0.1257, abs=0.0001)


def test_raising_only_exit_yield_understates_the_risk():
    y = required_yield(PropertyType.OFFICE, City.MALMO, 36.8)
    only_exit = value_with_leases(KRONBORGSVAGEN_20, 5, 0.0725, y).market_value
    both = value_with_leases(KRONBORGSVAGEN_20, 5, discount_rate(y, 0.02), y).market_value
    assert both < only_exit < ORIGINAL_VALUE
