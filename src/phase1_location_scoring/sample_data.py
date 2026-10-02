"""Inläsning av exempeldatan i data/sample/."""

import csv
from pathlib import Path

from .models import CommercialProperty, Coordinates

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


def load_transit_stops(path: Path = SAMPLE_DIR / "transit_stops.csv") -> list[Coordinates]:
    with open(path, encoding="utf-8") as f:
        return [_coordinates(row) for row in csv.DictReader(f)]
