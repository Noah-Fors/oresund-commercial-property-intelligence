from unittest import mock

import pytest

from src.phase1_location_scoring import fetch_osm
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


def _response(status: int, total: int = 0):
    response = mock.Mock(status_code=status, ok=status == 200)
    response.json.return_value = {"elements": [{"tags": {"total": str(total)}}]}
    return response


def test_fetch_count_falls_back_to_mirror_and_remembers_it():
    urls = ["https://main", "https://mirror"]
    with mock.patch.object(fetch_osm, "OVERPASS_URLS", urls), mock.patch.object(
        fetch_osm.requests, "post", side_effect=[_response(406), _response(200, 42), _response(200, 7)]
    ) as post:
        assert fetch_osm.fetch_count("query") == 42
        assert fetch_osm.fetch_count("query") == 7
    assert [c.args[0] for c in post.call_args_list] == ["https://main", "https://mirror", "https://mirror"]


def test_fetch_count_explains_when_every_server_fails():
    with mock.patch.object(fetch_osm, "OVERPASS_URLS", ["https://a", "https://b"]), mock.patch.object(
        fetch_osm.requests, "post", return_value=_response(406)
    ):
        with pytest.raises(RuntimeError, match="Ingen Overpass-server svarade"):
            fetch_osm.fetch_count("query")
