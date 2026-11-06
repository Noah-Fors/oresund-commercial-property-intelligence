import pytest

from src.phase1_location_scoring.models import Coordinates, LocationScoreComponents, PropertyType
from src.phase1_location_scoring.sample_data import (
    load_commercial_counts,
    load_highway_interchanges,
    load_properties,
    load_transit_stops,
)
from src.phase1_location_scoring.scoring import (
    WEIGHTS,
    commercial_density_score,
    distance_m,
    highway_score,
    score_properties,
    total_score,
    transit_score,
)


def test_one_degree_of_latitude_is_about_111_km():
    a = Coordinates(latitude=55.5, longitude=13.0)
    b = Coordinates(latitude=56.0, longitude=13.0)
    assert distance_m(a, b) == pytest.approx(55_597, rel=0.001)


def test_transit_score_is_100_at_the_stop():
    assert transit_score(0) == 100


def test_transit_score_halves_every_700_m():
    assert transit_score(700) == pytest.approx(50)
    assert transit_score(1400) == pytest.approx(25)


def test_highway_score_halves_every_2000_m():
    assert highway_score(2000) == pytest.approx(50)


def test_scores_fall_with_distance_but_never_below_zero():
    assert transit_score(100) > transit_score(500) > transit_score(5000) > 0


def test_commercial_density_saturates():
    assert commercial_density_score(0) == 0
    assert commercial_density_score(50) == pytest.approx(50)
    assert commercial_density_score(100) == pytest.approx(75)
    assert commercial_density_score(300) < 100


@pytest.mark.parametrize("property_type", list(PropertyType))
def test_every_property_type_has_weights_summing_to_100(property_type):
    assert sum(WEIGHTS[property_type].values()) == 100


def test_total_score_skips_components_without_data():
    # Logistik: kollektivtrafik 10 %, motorväg 80 %. Arbetsplatser saknar data.
    components = LocationScoreComponents(transit_score=0, highway_score=90)
    assert total_score(components, PropertyType.LOGISTICS) == pytest.approx(80)


def test_highway_does_not_count_for_local_retail():
    components = LocationScoreComponents(transit_score=50, highway_score=100)
    assert total_score(components, PropertyType.RETAIL_LOCAL) == pytest.approx(50)


def test_sample_data_loads():
    assert len(load_properties()) == 15
    assert len(load_transit_stops()) == 9
    assert len(load_highway_interchanges()) == 12
    assert set(load_commercial_counts()) == {p.address for p in load_properties()}


def test_score_properties_ranks_best_location_first():
    scores = score_properties(
        load_properties(), load_transit_stops(), load_highway_interchanges(), load_commercial_counts()
    )
    assert len(scores) == 15
    assert scores.total_score.is_monotonic_decreasing
    assert scores.total_score.between(0, 100).all()
