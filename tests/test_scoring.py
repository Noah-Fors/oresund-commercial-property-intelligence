import pytest

from src.phase1_location_scoring.models import Coordinates
from src.phase1_location_scoring.sample_data import load_properties, load_transit_stops
from src.phase1_location_scoring.scoring import distance_m, transit_score


def test_one_degree_of_latitude_is_about_111_km():
    a = Coordinates(latitude=55.5, longitude=13.0)
    b = Coordinates(latitude=56.0, longitude=13.0)
    assert distance_m(a, b) == pytest.approx(55_597, rel=0.001)


def test_transit_score_is_100_at_the_stop():
    assert transit_score(0) == 100


def test_transit_score_halves_every_700_m():
    assert transit_score(700) == pytest.approx(50)
    assert transit_score(1400) == pytest.approx(25)


def test_transit_score_falls_with_distance_but_never_below_zero():
    assert transit_score(100) > transit_score(500) > transit_score(5000) > 0


def test_sample_data_loads():
    assert len(load_properties()) == 15
    assert len(load_transit_stops()) == 9
