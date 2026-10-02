"""Beräkning av location score.

Varje fastighet får delpoäng (0–100) per parameter, som sedan vägs ihop
med vikter som beror på fastighetstypen. Arbetsplatser och kommersiell
täthet saknar data än och hoppas över i totalen.
"""

from math import asin, cos, radians, sin, sqrt
import pandas as pd

from .models import (
    CommercialProperty,
    Coordinates,
    HighwayInterchange,
    LocationScoreComponents,
    PropertyType,
    TransitStop,
)

EARTH_RADIUS_M = 6_371_000

# Avståndet där delpoängen har halverats (100 -> 50).
TRANSIT_HALF_DISTANCE_M = 700
HIGHWAY_HALF_DISTANCE_M = 2000

# Vikter i procent per fastighetstyp. Varje rad summerar till 100.
WEIGHTS: dict[PropertyType, dict[str, int]] = {
    PropertyType.OFFICE: {
        "transit_score": 40, "employment_score": 35,
        "commercial_density_score": 15, "highway_score": 10,
    },
    PropertyType.RETAIL_LOCAL: {
        "transit_score": 30, "employment_score": 10,
        "commercial_density_score": 60, "highway_score": 0,
    },
    PropertyType.RETAIL_EXTERNAL: {
        "transit_score": 15, "employment_score": 10,
        "commercial_density_score": 40, "highway_score": 35,
    },
    PropertyType.LOGISTICS: {
        "transit_score": 10, "employment_score": 10,
        "commercial_density_score": 0, "highway_score": 80,
    },
    PropertyType.MIXED_USE: {
        "transit_score": 30, "employment_score": 25,
        "commercial_density_score": 35, "highway_score": 10,
    },
}


def distance_m(a: Coordinates, b: Coordinates) -> float:
    """Fågelvägen i meter mellan två punkter (haversine-formeln)."""
    lat1, lon1 = radians(a.latitude), radians(a.longitude)
    lat2, lon2 = radians(b.latitude), radians(b.longitude)
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_M * asin(sqrt(h))


def nearest(point: Coordinates, places: list) -> tuple:
    """Närmaste plats (station, trafikplats …) och avståndet dit i meter."""
    return min(
        ((place, distance_m(point, place.coordinates)) for place in places),
        key=lambda pair: pair[1],
    )


def decay_score(distance: float, half_distance_m: float) -> float:
    """Exponentiell distance decay: 100 vid 0 m, halveras var `half_distance_m`."""
    return 100 * 0.5 ** (distance / half_distance_m)


def transit_score(distance: float) -> float:
    return decay_score(distance, TRANSIT_HALF_DISTANCE_M)


def highway_score(distance: float) -> float:
    return decay_score(distance, HIGHWAY_HALF_DISTANCE_M)


def total_score(components: LocationScoreComponents, property_type: PropertyType) -> float:
    """Viktat medelvärde av de delpoäng som har data, med vikter för fastighetstypen."""
    weights = WEIGHTS[property_type]
    available = {
        name: value
        for name, value in components.model_dump().items()
        if value is not None and weights[name] > 0
    }
    weight_sum = sum(weights[name] for name in available)
    return sum(value * weights[name] for name, value in available.items()) / weight_sum


def score_properties(
    properties: list[CommercialProperty],
    stops: list[TransitStop],
    interchanges: list[HighwayInterchange],
) -> pd.DataFrame:
    """En rad per fastighet med delpoäng och totalt location score, bäst först."""
    rows = []
    for prop in properties:
        stop, stop_distance = nearest(prop.coordinates, stops)
        interchange, interchange_distance = nearest(prop.coordinates, interchanges)
        components = LocationScoreComponents(
            transit_score=transit_score(stop_distance),
            highway_score=highway_score(interchange_distance),
        )
        rows.append(
            {
                "address": prop.address,
                "city": prop.city.value,
                "property_type": prop.property_type.value,
                "latitude": prop.coordinates.latitude,
                "longitude": prop.coordinates.longitude,
                "nearest_stop": stop.name,
                "stop_distance_m": round(stop_distance),
                "nearest_interchange": f"{interchange.name} ({interchange.road})",
                "interchange_distance_m": round(interchange_distance),
                "transit_score": round(components.transit_score, 1),
                "highway_score": round(components.highway_score, 1),
                "total_score": round(total_score(components, prop.property_type), 1),
            }
        )
    return pd.DataFrame(rows).sort_values("total_score", ascending=False, ignore_index=True)
