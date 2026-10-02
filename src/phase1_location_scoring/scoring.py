"""Beräkning av location score-komponenter.

Just nu finns bara transit-poänget. Arbetsplatser och kommersiell täthet
läggs till när vi har data för dem.
"""

from math import asin, cos, radians, sin, sqrt

from .models import Coordinates

EARTH_RADIUS_M = 6_371_000

# Avståndet där transit-poänget har halverats (100 -> 50).
TRANSIT_HALF_DISTANCE_M = 700


def distance_m(a: Coordinates, b: Coordinates) -> float:
    """Fågelvägen i meter mellan två punkter (haversine-formeln)."""
    lat1, lon1 = radians(a.latitude), radians(a.longitude)
    lat2, lon2 = radians(b.latitude), radians(b.longitude)
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_M * asin(sqrt(h))


def nearest_distance_m(point: Coordinates, targets: list[Coordinates]) -> float:
    return min(distance_m(point, target) for target in targets)


def transit_score(
    distance_to_stop_m: float, half_distance_m: float = TRANSIT_HALF_DISTANCE_M
) -> float:
    """Exponentiell distance decay: 100 vid 0 m, halveras var `half_distance_m`."""
    return 100 * 0.5 ** (distance_to_stop_m / half_distance_m)
