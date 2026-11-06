"""Kontrollerar arbetsboken med data från MSCI Property Intel.

Kör från projektmappen:
    python -m src.phase3_market_report.check_property_intel

Skapar en tom mall i data/raw/ om arbetsboken inte finns.
"""

from collections import defaultdict

from src.phase1_location_scoring.models import CITY_LABELS, PROPERTY_TYPE_LABELS

from .models import SEGMENT_LABELS
from .property_intel import WORKBOOK, create_template, load_normal_values, load_properties


def main() -> None:
    if not WORKBOOK.exists():
        create_template()
        print(f"Skapade en tom mall: {WORKBOOK}")
        print("Filen innehåller licensierad data och checkas inte in i git.")
        return

    try:
        properties = load_properties()
        normals = load_normal_values(properties=properties.rows)
    except PermissionError:
        print("Arbetsboken är öppen i Excel. Stäng Excel och kör kommandot igen.")
        return

    by_property = defaultdict(list)
    for value in normals.rows:
        by_property[value.designation.casefold()].append(value)

    print(f"Fastigheter: {len(properties.rows)} giltiga rader")
    for prop in properties.rows:
        values = by_property[prop.designation.casefold()]
        print(f"  {prop.designation:<20} {CITY_LABELS[prop.city.value]:<12} "
              f"{PROPERTY_TYPE_LABELS[prop.property_type.value]:<14} {prop.taxed_area_sqm:>8,.0f} kvm  "
              f"{len(values)} källor")
        for v in values:
            print(f"      {v.source:<20} {SEGMENT_LABELS[v.segment.value]:<9} {v.location:<22} "
                  f"hyra {v.rent_per_sqm:>6,.0f}  vakans {v.vacancy_pct:>5.2f} %  dir.avk {v.yield_pct:.2f} %")

    without = [p.designation for p in properties.rows if not by_property[p.designation.casefold()]]
    if without:
        print(f"\nSaknar normalvärden: {', '.join(without)}")

    errors = [("Fastigheter", e) for e in properties.errors] + [("Normalvärden", e) for e in normals.errors]
    if errors:
        print(f"\n{len(errors)} fel att rätta:")
        for sheet, error in errors:
            print(f"  {sheet}, {error}")
    else:
        print("\nInga fel.")


if __name__ == "__main__":
    main()
