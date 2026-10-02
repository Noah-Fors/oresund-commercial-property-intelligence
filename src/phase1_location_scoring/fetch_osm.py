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

# Huvudservern först, sedan speglingar. Huvudservern avvisar ibland
# automatiska anrop med 406, och då provas nästa server i listan.
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
HEADERS = {
    "User-Agent": (
        "oresund-property-intelligence/1.0 "
        "(+https://github.com/Noah-Fors/oresund-commercial-property-intelligence)"
    ),
    "Accept": "*/*",
    "Accept-Language": "sv,en;q=0.8",
}
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


def _post(url: str, query: str, attempts: int) -> requests.Response:
    """Skickar frågan. Försöker igen om servern är tillfälligt överbelastad."""
    for attempt in range(1, attempts + 1):
        response = requests.post(url, data={"data": query}, headers=HEADERS, timeout=60)
        if response.status_code not in (429, 504) or attempt == attempts:
            return response
        time.sleep(10 * attempt)
    return response


def fetch_count(query: str, attempts: int = 3) -> int:
    """Provar servrarna i tur och ordning tills någon svarar.

    En server som svarar flyttas först i listan, så att nästa fråga går dit direkt.
    """
    errors = []
    for url in list(OVERPASS_URLS):
        try:
            response = _post(url, query, attempts)
        except requests.RequestException as exc:
            reason = exc.__class__.__name__
        else:
            if response.ok:
                OVERPASS_URLS.remove(url)
                OVERPASS_URLS.insert(0, url)
                return parse_count(response.json())
            reason = f"HTTP {response.status_code}"
        errors.append(f"{url}: {reason}")
        print(f"    {url} svarade inte ({reason}), provar nästa server …", flush=True)
    raise RuntimeError("Ingen Overpass-server svarade:\n  " + "\n  ".join(errors))


def main() -> None:
    rows = []
    for prop in load_properties():
        print(f"Hämtar {prop.address} …", flush=True)
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
        print(f"  -> handel/restaurang: {commercial:4}   kontor: {offices:4}", flush=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print("\nResultat:")
    for row in rows:
        print(f"{row['address']:30} handel/restaurang: {row['commercial_count']:4}   kontor: {row['office_count']:4}")
    print(f"\nSparat i {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
