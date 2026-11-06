"""Räknar verksamheter från OpenStreetMap runt varje exempelfastighet.

Körs från projektmappen:
    python -m src.phase1_location_scoring.fetch_osm

Alla räkningar skickas i en enda förfrågan till Overpass API.
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
# (sekunder för att få kontakt, sekunder för att vänta på svaret)
TIMEOUT = (10, 180)
RADIUS_M = 500
OUTPUT_PATH = SAMPLE_DIR / "osm_counts.csv"

# Verksamheter som drar kunder till ett område.
COMMERCIAL_FILTERS = [
    "[shop]",
    '[amenity~"^(restaurant|cafe|fast_food|bar|pub|bank|pharmacy)$"]',
]
# Kontor och företag, som proxy för arbetsplatser.
OFFICE_FILTERS = ["[office]"]


def _count_block(point: Coordinates, filters: list[str], radius_m: int) -> str:
    around = f"(around:{radius_m},{point.latitude},{point.longitude})"
    parts = "\n".join(f"  nwr{around}{f};" for f in filters)
    return f"(\n{parts}\n);\nout count;"


def batch_query(points: list[Coordinates], radius_m: int = RADIUS_M) -> str:
    """En fråga med två räkningar per punkt: först handel, sedan kontor."""
    blocks = []
    for point in points:
        blocks.append(_count_block(point, COMMERCIAL_FILTERS, radius_m))
        blocks.append(_count_block(point, OFFICE_FILTERS, radius_m))
    return "[out:json][timeout:170];\n" + "\n".join(blocks)


def parse_counts(response_json: dict) -> list[int]:
    return [int(element["tags"]["total"]) for element in response_json["elements"]]


def _post(url: str, query: str, attempts: int) -> requests.Response:
    """Skickar frågan. Försöker igen om servern är tillfälligt överbelastad."""
    for attempt in range(1, attempts + 1):
        response = requests.post(url, data={"data": query}, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code not in (429, 504) or attempt == attempts:
            return response
        time.sleep(10 * attempt)
    return response


def fetch_counts(query: str, attempts: int = 2) -> list[int]:
    """Provar servrarna i tur och ordning tills någon svarar."""
    errors = []
    for url in OVERPASS_URLS:
        print(f"Frågar {url} …", flush=True)
        try:
            response = _post(url, query, attempts)
        except requests.RequestException as exc:
            reason = exc.__class__.__name__
        else:
            if response.ok:
                return parse_counts(response.json())
            reason = f"HTTP {response.status_code}"
        errors.append(f"{url}: {reason}")
        print(f"  svarade inte ({reason}), provar nästa server …", flush=True)
    raise RuntimeError("Ingen Overpass-server svarade:\n  " + "\n  ".join(errors))


def main() -> None:
    properties = load_properties()
    counts = fetch_counts(batch_query([p.coordinates for p in properties]))
    if len(counts) != 2 * len(properties):
        raise RuntimeError(f"Väntade {2 * len(properties)} siffror men fick {len(counts)}.")

    rows = [
        {
            "address": prop.address,
            "commercial_count": counts[2 * i],
            "office_count": counts[2 * i + 1],
            "radius_m": RADIUS_M,
            "fetched": date.today().isoformat(),
        }
        for i, prop in enumerate(properties)
    ]
    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print("\nResultat:")
    for row in rows:
        print(
            f"{row['address']:30} handel/restaurang: {row['commercial_count']:4}"
            f"   kontor: {row['office_count']:4}"
        )
    print(f"\nSparat i {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
