from unittest import mock

import pytest

from src.phase1_location_scoring import fetch_osm
from src.phase1_location_scoring.models import Coordinates


def test_batch_query_has_two_counts_per_point():
    points = [Coordinates(latitude=55.6, longitude=13.0), Coordinates(latitude=55.7, longitude=13.2)]
    query = fetch_osm.batch_query(points, radius_m=500)
    assert query.count("out count;") == 4
    assert "nwr(around:500,55.6,13.0)[shop];" in query
    assert "nwr(around:500,55.7,13.2)[office];" in query


def test_parse_counts_reads_every_total_in_order():
    response = {"elements": [{"type": "count", "tags": {"total": "15"}}, {"type": "count", "tags": {"total": "3"}}]}
    assert fetch_osm.parse_counts(response) == [15, 3]


def _response(status: int, totals: tuple[int, ...] = ()):
    response = mock.Mock(status_code=status, ok=status == 200)
    response.json.return_value = {"elements": [{"tags": {"total": str(t)}} for t in totals]}
    return response


def test_fetch_counts_falls_back_to_mirror_on_406():
    urls = ["https://main", "https://mirror"]
    with mock.patch.object(fetch_osm, "OVERPASS_URLS", urls), mock.patch.object(
        fetch_osm.requests, "post", side_effect=[_response(406), _response(200, (4, 2))]
    ) as post:
        assert fetch_osm.fetch_counts("query") == [4, 2]
    assert [c.args[0] for c in post.call_args_list] == urls


def test_fetch_counts_explains_when_every_server_fails():
    with mock.patch.object(fetch_osm, "OVERPASS_URLS", ["https://a", "https://b"]), mock.patch.object(
        fetch_osm.requests, "post", return_value=_response(406)
    ):
        with pytest.raises(RuntimeError, match="Ingen Overpass-server svarade"):
            fetch_osm.fetch_counts("query")
