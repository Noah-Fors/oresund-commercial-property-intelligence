"""Inläsning av exempeldatan i data/sample/."""

import csv
from pathlib import Path

from .models import CommercialProperty, Coordinates, HighwayInterchange, TransitStop

SAMPLE_DIR = Path(__file__).resolve().parents[2] / "data" / "sample"


def _coordinates(row: dict[str, str]) -> Coordinates:
    return Coordinates(latitude=float(row["latitude"]), longitude=float(row["longitude"]))


def load_properties(path: Path = SAMPLE_DIR / "properties.csv") -> list[CommercialProperty]:
    with open(path, encoding="utf-8") as f:
        return [
            CommercialProperty(
                address=row["address"],
                city=row["city"],
                property_type=row["property_type"],
                coordinates=_coordinates(row),
            )
            for row in csv.DictReader(f)
        ]


def load_transit_stops(path: Path = SAMPLE_DIR / "transit_stops.csv") -> list[TransitStop]:
    with open(path, encoding="utf-8") as f:
        return [
            TransitStop(
                name=row["name"],
                city=row["city"],
                stop_type=row["stop_type"],
                coordinates=_coordinates(row),
            )
            for row in csv.DictReader(f)
        ]


def load_highway_interchanges(
    path: Path = SAMPLE_DIR / "highway_interchanges.csv",
) -> list[HighwayInterchange]:
    with open(path, encoding="utf-8") as f:
        return [
            HighwayInterchange(name=row["name"], road=row["road"], coordinates=_coordinates(row))
            for row in csv.DictReader(f)
        ]


def load_commercial_counts(path: Path = SAMPLE_DIR / "osm_counts.csv") -> dict[str, int]:
    """Antal butiker/restauranger inom 500 m per adress, hämtat med fetch_osm.py."""
    with open(path, encoding="utf-8") as f:
        return {row["address"]: int(row["commercial_count"]) for row in csv.DictReader(f)}
