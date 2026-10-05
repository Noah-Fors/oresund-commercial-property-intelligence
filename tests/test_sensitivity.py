"""Känslighetsmatrisen för Kronborgsvägen 20, byggd med Data Table i Excel."""

import pytest

from src.phase2_valuation.sensitivity import yield_rent_matrix
from tests.test_leases import KRONBORGSVAGEN_20

EXIT_YIELD = 0.059797


@pytest.fixture
def matrix():
    return yield_rent_matrix(KRONBORGSVAGEN_20, EXIT_YIELD, holding_period_years=5)


def test_matrix_shape_and_axes(matrix):
    assert matrix.shape == (5, 5)
    assert list(matrix.columns) == pytest.approx([1_620, 1_710, 1_800, 1_890, 1_980])


def test_centre_is_the_base_case(matrix):
    assert matrix.iloc[2, 2] == pytest.approx(41_142_351, rel=1e-5)


def test_corners_match_excel(matrix):
    assert matrix.iloc[0, 0] == pytest.approx(39_632_172, rel=1e-4)
    assert matrix.iloc[4, 4] == pytest.approx(42_262_563, rel=1e-4)


def test_value_falls_with_yield_and_rises_with_rent(matrix):
    for column in matrix.columns:
        assert matrix[column].is_monotonic_decreasing
    for _, row in matrix.iterrows():
        assert row.is_monotonic_increasing


def test_market_rent_matters_more_than_yield_for_this_short_wault_property(matrix):
    base = matrix.iloc[2, 2]
    yield_up = matrix.iloc[3, 2] / base - 1
    rent_down = matrix.iloc[2, 1] / base - 1
    assert rent_down < yield_up < 0
