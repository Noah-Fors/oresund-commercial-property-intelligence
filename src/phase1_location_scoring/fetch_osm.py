"""Räknar verksamheter från OpenStreetMap runt varje exempelfastighet.

Körs från projektmappen:
    python -m src.phase1_location_scoring.fetch_osm

Resultatet sparas i data/sample/osm_counts.csv.
"""

import csv
import time
from datetime import date

import requests

from .models import Coordinates
from .sample_data import SAMPLE_DIR, load_properties

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
RADIUS_M = 500
OUTPUT_PATH = SAMPLE_DIR / "osm_counts.csv"

# Verksamheter som drar kunder till ett område.
COMMERCIAL_FILTERS = [
    "[shop]",
    '[amenity~"^(restaurant|cafe|fast_food|bar|pub|bank|pharmacy)$"]',
]
# Kontor och företag, som proxy för arbetsplatser.
OFFICE_FILTERS = ["[office]"]


def count_query(point: Coordinates, filters: list[str], radius_m: int = RADIUS_M) -> str:
    around = f"(around:{radius_m},{point.latitude},{point.longitude})"
    parts = "\n".join(f"  nwr{around}{f};" for f in filters)
    return f"[out:json][timeout:60];\n(\n{parts}\n);\nout count;"


def parse_count(response_json: dict) -> int:
    return int(response_json["elements"][0]["tags"]["total"])


def fetch_count(query: str, attempts: int = 4) -> int:
    """Skickar frågan till Overpass. Försöker igen om servern är överbelastad."""
    for attempt in range(1, attempts + 1):
        response = requests.post(
            OVERPASS_URL,
            data={"data": query},
            headers={"User-Agent": "oresund-property-intelligence (portfolio project)"},
            timeout=90,
        )
        if response.status_code not in (429, 504) or attempt == attempts:
            break
        time.sleep(10 * attempt)
    response.raise_for_status()
    return parse_count(response.json())


def main() -> None:
    rows = []
    for prop in load_properties():
        commercial = fetch_count(count_query(prop.coordinates, COMMERCIAL_FILTERS))
        time.sleep(1)
        offices = fetch_count(count_query(prop.coordinates, OFFICE_FILTERS))
        time.sleep(1)
        rows.append(
            {
                "address": prop.address,
                "commercial_count": commercial,
                "office_count": offices,
                "radius_m": RADIUS_M,
                "fetched": date.today().isoformat(),
            }
        )
        print(f"{prop.address:30} handel/restaurang: {commercial:4}   kontor: {offices:4}")

    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSparat i {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
