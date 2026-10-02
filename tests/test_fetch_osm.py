from src.phase1_location_scoring.fetch_osm import (
    COMMERCIAL_FILTERS,
    count_query,
    parse_count,
)
from src.phase1_location_scoring.models import Coordinates


def test_count_query_searches_around_the_point():
    query = count_query(Coordinates(latitude=55.6, longitude=13.0), COMMERCIAL_FILTERS, radius_m=500)
    assert "nwr(around:500,55.6,13.0)[shop];" in query
    assert query.endswith("out count;")


def test_parse_count_reads_total():
    response = {"elements": [{"type": "count", "tags": {"nodes": "12", "ways": "3", "total": "15"}}]}
    assert parse_count(response) == 15
