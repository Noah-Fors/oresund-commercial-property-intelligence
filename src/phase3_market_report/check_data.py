"""Kontrollerar arbetsboken med marknadsdata och skriver ut en sammanfattning.

Kör från projektmappen:
    python -m src.phase3_market_report.check_data

Skapar en tom mall om arbetsboken inte finns.
"""

from collections import Counter

from src.phase1_location_scoring.models import CITY_LABELS

from .data import WORKBOOK, create_template, load_listings, load_metrics


def main() -> None:
    if not WORKBOOK.exists():
        create_template()
        print(f"Skapade en tom mall: {WORKBOOK}")
        return

    metrics, listings = load_metrics(), load_listings()
    print(f"Nyckeltal: {len(metrics.rows)} giltiga rader")
    for metric in metrics.rows:
        value = f"{metric.low:g}" if metric.low == metric.high else f"{metric.low:g}–{metric.high:g}"
        print(f"  {CITY_LABELS[metric.city.value]:<12} {metric.submarket:<18} {metric.metric.value:<20} "
              f"{value} {metric.unit}  ({metric.source}, {metric.published})")

    print(f"\nAnnonser: {len(listings.rows)} giltiga rader")
    per_city = Counter(listing.city for listing in listings.rows)
    for city, count in per_city.items():
        with_rent = sum(1 for l in listings.rows if l.city == city and l.asking_rent_per_sqm is not None)
        print(f"  {CITY_LABELS[city.value]:<12} {count} annonser, {with_rent} med angiven hyra")

    errors = [("Nyckeltal", e) for e in metrics.errors] + [("Annonser", e) for e in listings.errors]
    if errors:
        print(f"\n{len(errors)} fel att rätta:")
        for sheet, error in errors:
            print(f"  {sheet}, {error}")
    else:
        print("\nInga fel.")


if __name__ == "__main__":
    main()
