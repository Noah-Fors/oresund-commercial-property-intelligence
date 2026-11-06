"""Fastighetsuppgifter och normalvärden från MSCI Property Intel (tidigare Datscha).

Datan är licensierad via Lunds tekniska högskola och får inte publiceras. Arbetsboken
ligger därför i data/raw/, som inte checkas in i git. I repot hamnar bara det som
räknas fram ur den, till exempel en kalibrerad yield-kurva.

Två flikar:

- Fastigheter: en rad per fastighet (fastighetsbeteckning, typkod, taxerad area ...).
- Normalvärden: marknadshyra, vakans och direktavkastning för fastighetens lägesområde,
  en rad per källa (Croisette, Cushman & Wakefield, Forum). Antalet källor varierar
  mellan fastigheterna, beroende på vad Property Intel visar.
"""

from collections import Counter
from datetime import date
from enum import Enum
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from src.phase1_location_scoring.models import City, Coordinates, PropertyType

from .data import LoadResult, _add_sheet, _records, _validate
from .models import Segment

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
WORKBOOK = RAW_DIR / "property_intel.xlsx"
PROPERTIES_SHEET = "Fastigheter"
NORMALS_SHEET = "Normalvärden"

KNOWN_SOURCES = ("Croisette", "Cushman & Wakefield", "Forum")
LOCATION_CLASSES = ("AA", "A", "B", "C", "D")

# Vilket segment i källornas tabeller som gäller för respektive fastighetstyp.
# Blandfastigheter har flera segment (butik i gatuplan, bostäder ovanför).
SEGMENTS_FOR_TYPE: dict[PropertyType, set[Segment]] = {
    PropertyType.OFFICE: {Segment.OFFICE},
    PropertyType.RETAIL_LOCAL: {Segment.RETAIL},
    PropertyType.RETAIL_EXTERNAL: {Segment.RETAIL},
    PropertyType.LOGISTICS: {Segment.INDUSTRIAL},
    PropertyType.MIXED_USE: {Segment.RESIDENTIAL, Segment.RETAIL, Segment.OFFICE},
}


class Heating(str, Enum):
    WARM = "varm"  # varmhyra: värmen ingår i hyran
    COLD = "kall"  # kallhyra: hyresgästen betalar värmen själv


class PropertyRecord(BaseModel):
    """En verklig fastighet som uppslagen i Property Intel."""

    designation: str = Field(..., min_length=1, description="Fastighetsbeteckning, t.ex. 'Odense 1'.")
    address: str = Field(..., min_length=1)
    city: City
    property_type: PropertyType
    type_code: int = Field(..., ge=100, le=999, description="Taxeringens typkod, t.ex. 325.")
    taxed_area_sqm: float = Field(..., gt=0, description="Taxerad area i kvm.")
    tax_value_ksek: float = Field(..., gt=0, description="Taxeringsvärde i tusental kronor.")
    value_year: int | None = Field(default=None, ge=1800, le=2030, description="Värdeår.")
    coordinates: Coordinates
    collected: date


class NormalValue(BaseModel):
    """En källas normalvärden för det lägesområde fastigheten ligger i."""

    designation: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    segment: Segment
    location: str = Field(..., min_length=1, description="Läge som källan skriver det, t.ex. 'C Malmö tätort'.")
    value_years: str | None = Field(default=None, description="Värdeårsintervall, t.ex. '2010 -' eller '- 2009'.")
    rent_per_sqm: float = Field(..., ge=300, le=10_000, description="Hyra i kr/kvm/år.")
    vacancy_pct: float = Field(..., ge=0, le=60, description="Vakans i procent, 10 % skrivs 10.")
    yield_pct: float = Field(..., ge=1, le=15, description="Direktavkastning i procent, 7,25 % skrivs 7,25.")
    heating: Heating
    published: date

    @field_validator("value_years", mode="before")
    @classmethod
    def _excel_number_to_text(cls, value):
        # Excel tolkar "-2009" som talet -2009.
        if isinstance(value, (int, float)):
            return f"- {abs(int(value))}" if value < 0 else str(int(value))
        return value

    @model_validator(mode="after")
    def _location_starts_with_class(self) -> "NormalValue":
        if self.location_class is None:
            raise ValueError(
                f"Läget '{self.location}' börjar inte med en lägesklass ({', '.join(LOCATION_CLASSES)}). "
                "Skriv läget exakt som källan, t.ex. 'C Malmö tätort'."
            )
        return self

    @property
    def location_class(self) -> str | None:
        first = self.location.split()[0].upper()
        return first if first in LOCATION_CLASSES else None


PROPERTY_COLUMNS = [
    ("designation", 18, "Fastighetsbeteckning som i Property Intel, t.ex. Odense 1."),
    ("address", 24, "Gatuadress."),
    ("city", 13, "malmo, lund eller helsingborg (välj i listan)."),
    ("property_type", 16, "office, retail_local (tätortshandel), retail_external (externhandel), logistics eller mixed_use."),
    ("type_code", 10, "Typkod, t.ex. 325 (hyreshusenhet, huvudsakligen lokaler)."),
    ("taxed_area_sqm", 12, "Taxerad area i kvm, utan mellanslag."),
    ("tax_value_ksek", 12, "Taxeringsvärde i kSEK (tusental kronor), som Property Intel visar det."),
    ("value_year", 10, "Värdeår. Lämna tomt om det saknas."),
    ("latitude", 11, "Högerklicka på fastigheten i Google Maps, första talet."),
    ("longitude", 11, "Högerklicka på fastigheten i Google Maps, andra talet."),
    ("collected", 13, "Datum du hämtade uppgifterna (ÅÅÅÅ-MM-DD)."),
]
NORMAL_COLUMNS = [
    ("designation", 18, "Samma fastighetsbeteckning som i fliken Fastigheter."),
    ("source", 22, "Croisette, Cushman & Wakefield eller Forum. Andra källor går också att skriva in."),
    ("segment", 12, "Raden du läst av: office (Kontor), retail (Butik), industrial (Industri), residential (Bostäder)."),
    ("location", 22, "Läge exakt som källan skriver det, t.ex. C Malmö tätort."),
    ("value_years", 12, "Värdeår som källan skriver det, t.ex. '2010 -'. Välj raden som matchar fastighetens värdeår."),
    ("rent_per_sqm", 11, "Hyra i kr/kvm/år."),
    ("vacancy_pct", 10, "Vakans i procent: 10 % skrivs 10."),
    ("yield_pct", 10, "Dir. avk i procent: 7,25 % skrivs 7,25."),
    ("heating", 10, "varm (varmhyra) eller kall (kallhyra)."),
    ("published", 13, "Källans datum, t.ex. 2026-06-30."),
]

INSTRUCTIONS = [
    "MSCI Property Intel: fastigheter och normalvärden",
    "",
    "LICENSIERAD DATA. Filen ligger i data/raw/ och checkas aldrig in i git. Dela den inte.",
    "",
    "Fliken Fastigheter: en rad per fastighet, från fastighetens översiktssida.",
    "Fliken Normalvärden: från fliken Marknadsinformation, en rad per källa som visas.",
    "  - Läs bara raden för fastighetens typ: Kontor för kontor, Butik för handel, Industri för logistik.",
    "  - Finns flera rader med olika värdeår, välj den som matchar fastighetens värdeår.",
    "  - Blandfastigheter: en rad för bostäder och en för butik, per källa.",
    "  - Antalet källor får variera mellan fastigheterna.",
    "",
    "Procent skrivs som tal: 7,25 % skrivs 7,25. Hyra i kr/kvm/år.",
    "Kontrollera filen med: python -m src.phase3_market_report.check_property_intel",
]


def create_template(path: Path = WORKBOOK) -> None:
    if path.exists():
        raise FileExistsError(f"{path} finns redan och skrivs inte över.")
    wb = Workbook()
    info = wb.active
    info.title = "Instruktioner"
    for row, text in enumerate(INSTRUCTIONS, start=1):
        info.cell(row=row, column=1, value=text)
    info["A1"].font = Font(bold=True, size=14)
    info["A3"].font = Font(bold=True, color="C00000")
    info.column_dimensions["A"].width = 110

    _add_sheet(
        wb, PROPERTIES_SHEET, PROPERTY_COLUMNS,
        {"city": ",".join(c.value for c in City), "property_type": ",".join(t.value for t in PropertyType)},
        numbers=("taxed_area_sqm", "tax_value_ksek", "latitude", "longitude"),
    )
    _add_sheet(
        wb, NORMALS_SHEET, NORMAL_COLUMNS,
        {"source": ",".join(KNOWN_SOURCES), "segment": ",".join(s.value for s in Segment),
         "heating": ",".join(h.value for h in Heating)},
        numbers=("rent_per_sqm", "vacancy_pct", "yield_pct"),
        open_lists=("source",),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def _property(record: dict) -> PropertyRecord:
    lat, lon = record.pop("latitude"), record.pop("longitude")
    record["coordinates"] = {"latitude": lat, "longitude": lon}
    return PropertyRecord(**record)


def _cross_sheet_error(excel_row: int, message: str) -> str:
    return f"rad {excel_row}: {message}"


def load_properties(path: Path = WORKBOOK) -> LoadResult:
    records = _records(path, PROPERTIES_SHEET)
    result = _validate(records, _property)
    counts = Counter(p.designation.casefold() for p in result.rows)
    duplicates = sorted({p.designation for p in result.rows if counts[p.designation.casefold()] > 1})
    for designation in duplicates:
        result.errors.append(f"{designation}: fastighetsbeteckningen finns på flera rader.")
    return result


def load_normal_values(path: Path = WORKBOOK, properties: list[PropertyRecord] | None = None) -> LoadResult:
    """Läser normalvärdena och kontrollerar dem mot fliken Fastigheter."""
    if properties is None:
        properties = load_properties(path).rows
    by_designation = {p.designation.casefold(): p for p in properties}

    rows, errors, seen = [], [], set()
    for excel_row, record in _records(path, NORMALS_SHEET):
        try:
            value = NormalValue(**record)
        except ValidationError:
            errors.extend(_validate([(excel_row, record)], lambda r: NormalValue(**r)).errors)
            continue
        prop = by_designation.get(value.designation.casefold())
        if prop is None:
            errors.append(_cross_sheet_error(excel_row, f"{value.designation} finns inte i fliken Fastigheter."))
            continue
        if value.segment not in SEGMENTS_FOR_TYPE[prop.property_type]:
            errors.append(_cross_sheet_error(
                excel_row,
                f"{value.designation} är {prop.property_type.value}, men raden gäller {value.segment.value}. "
                "Läs raden för fastighetens typ.",
            ))
            continue
        key = (value.designation.casefold(), value.source.casefold(), value.segment)
        if key in seen:
            errors.append(_cross_sheet_error(
                excel_row, f"{value.source} har redan en rad för {value.designation} ({value.segment.value})."
            ))
            continue
        seen.add(key)
        rows.append(value)
    return LoadResult(rows, errors)
