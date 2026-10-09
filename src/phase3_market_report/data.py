"""Excel-arbetsboken där marknadsdata samlas in för hand, och inläsning av den.

Arbetsboken har två flikar som läses av koden: "Nyckeltal" (MarketMetric) och
"Annonser" (OfficeListing). Varje rad valideras för sig, så ett fel på en rad
stoppar inte resten. Felen returneras med Excel-radnummer så att de går att hitta.
"""

import shutil
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from pydantic import BaseModel, ValidationError

from src.phase1_location_scoring.models import City

from .models import MarketMetric, Metric, OfficeListing, Segment

MARKET_DIR = Path(__file__).resolve().parents[2] / "data" / "market"
WORKBOOK = MARKET_DIR / "office_market_data.xlsx"
METRICS_SHEET = "Nyckeltal"
LISTINGS_SHEET = "Annonser"

# Kolumn, bredd, förklaring (visas som kommentar i rubrikcellen).
METRIC_COLUMNS = [
    ("city", 13, "malmo, lund eller helsingborg (välj i listan)."),
    ("submarket", 18, "Delområdet siffran gäller, t.ex. CBD, Västra Hamnen, Lägesklass A, Hela staden."),
    ("segment", 12, "office (kontor), retail (butik) eller industrial (industri). Välj i listan."),
    ("metric", 20, "Välj i listan: prime_rent, rent_range, vacancy_rate, prime_yield, take_up, transaction_volume."),
    ("low", 10, "Värdet, eller lägsta värdet om rapporten anger ett intervall. Procent som tal: 4,85 % skrivs 4,85."),
    ("high", 10, "Högsta värdet i intervallet. Lämna tomt om rapporten anger ett enda värde."),
    ("source", 22, "Vem som publicerat siffran, t.ex. Cushman & Wakefield MarketBeat Q2 2026."),
    ("published", 13, "Rapportens datum (ÅÅÅÅ-MM-DD). För kvartalsrapporter: kvartalets sista dag."),
    ("url", 40, "Länk till rapporten."),
]
LISTING_COLUMNS = [
    ("address", 24, "Gatuadress som i annonsen."),
    ("city", 13, "malmo, lund eller helsingborg (välj i listan)."),
    ("district", 18, "Stadsdel, t.ex. Centrum, Västra Hamnen, Hyllie, Ideon."),
    ("area_sqm", 10, "Lokalens area i kvm. Flera lokaler i samma annons = en rad per lokal."),
    ("asking_rent_per_sqm", 12, "Begärd hyra i kr/kvm/år. Månadshyra räknas om: månadshyra × 12 / kvm. Tomt om hyran inte anges."),
    ("rent_terms", 28, "Vad hyran inkluderar enligt annonsen, t.ex. 'inkl. värme och kyla, tillägg fastighetsskatt'."),
    ("latitude", 11, "Valfritt. Högerklicka på platsen i Google Maps, första talet."),
    ("longitude", 11, "Valfritt. Högerklicka på platsen i Google Maps, andra talet."),
    ("source", 16, "Annonssajt eller hyresvärd, t.ex. Objektvision, Wihlborgs."),
    ("url", 40, "Länk till annonsen."),
    ("collected", 13, "Datum du läste annonsen (ÅÅÅÅ-MM-DD)."),
]

INSTRUCTIONS = [
    "Öresund Commercial Property Intelligence — insamling av kontorsdata",
    "",
    "Fliken Nyckeltal: siffror ur publicerade marknadsrapporter (en rad per siffra).",
    "Fliken Annonser: lediga kontorslokaler från annonssajter (en rad per lokal).",
    "",
    "Regler:",
    "1. Skriv bara in fakta du läst själv (adress, kvm, hyra) och länken. Kopiera inte annonstexter eller bilder.",
    "2. Formatera inte celler som procent. 4,85 % skrivs som talet 4,85.",
    "3. Hyra anges alltid i kr/kvm/år. Månadshyra × 12 / kvm. Total årshyra / kvm.",
    "4. Annonser utan angiven hyra tas också med (lämna hyran tom). Andelen säger något om marknaden.",
    "5. Ändra inte rubrikraden. Lägg inte till tomma rader mitt i tabellen.",
    "6. Kontrollera filen med: python -m src.phase3_market_report.check_data",
    "",
    "Håll muspekaren över en rubrik för att se vad kolumnen ska innehålla.",
]


def create_template(path: Path = WORKBOOK) -> None:
    """Skapar en tom arbetsbok med rubriker, förklaringar och rullistor. Skriver aldrig över."""
    if path.exists():
        raise FileExistsError(f"{path} finns redan och skrivs inte över.")
    wb = Workbook()
    info = wb.active
    info.title = "Instruktioner"
    for row, text in enumerate(INSTRUCTIONS, start=1):
        info.cell(row=row, column=1, value=text)
    info["A1"].font = Font(bold=True, size=14)
    info.column_dimensions["A"].width = 110

    cities = ",".join(c.value for c in City)
    metrics = ",".join(m.value for m in Metric)
    segments = ",".join(s.value for s in Segment)
    _add_sheet(wb, METRICS_SHEET, METRIC_COLUMNS, {"city": cities, "segment": segments, "metric": metrics},
               numbers=("low", "high"))
    _add_sheet(wb, LISTINGS_SHEET, LISTING_COLUMNS, {"city": cities},
               numbers=("area_sqm", "asking_rent_per_sqm", "latitude", "longitude"))
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def _add_sheet(wb: Workbook, title: str, columns, dropdowns: dict[str, str], numbers: tuple[str, ...]) -> None:
    ws = wb.create_sheet(title)
    header_fill = PatternFill("solid", fgColor="DCE9F9")
    for index, (name, width, help_text) in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=index, value=name)
        cell.font = Font(bold=True)
        cell.fill = header_fill
        cell.comment = Comment(help_text, "Mall")
        letter = cell.column_letter
        ws.column_dimensions[letter].width = width
        cell_range = f"{letter}2:{letter}1000"
        if name in dropdowns:
            validation = DataValidation(type="list", formula1=f'"{dropdowns[name]}"', allow_blank=True)
            ws.add_data_validation(validation)
            validation.add(cell_range)
        if name in numbers:
            for row in range(2, 1001):
                ws[f"{letter}{row}"].number_format = "0.00####"
        if name in ("published", "collected"):
            for row in range(2, 1001):
                ws[f"{letter}{row}"].number_format = "yyyy-mm-dd"
    ws.freeze_panes = "A2"


def _sheet_rows(ws) -> list[dict]:
    header = [cell.value for cell in ws[1]]
    rows = []
    for values in ws.iter_rows(min_row=2, values_only=True):
        if any(v is not None for v in values):
            rows.append({h: v for h, v in zip(header, values) if h})
    return rows


def upgrade_workbook(path: Path = WORKBOOK) -> Path | None:
    """Flyttar över befintliga rader till den senaste mallen om kolumner saknas.

    Rader i Nyckeltal utan segment får "office", eftersom allt som samlades in
    före segmentkolumnen gällde kontor. Originalet sparas som en backup bredvid.
    Returnerar backupens sökväg, eller None om arbetsboken redan var aktuell.
    """
    old = load_workbook(path)
    metric_header = [cell.value for cell in old[METRICS_SHEET][1]]
    if all(name in metric_header for name, _, _ in METRIC_COLUMNS):
        return None

    data = {sheet: _sheet_rows(old[sheet]) for sheet in (METRICS_SHEET, LISTINGS_SHEET)}
    for row in data[METRICS_SHEET]:
        row.setdefault("segment", Segment.OFFICE.value)

    new_path = path.with_name(path.stem + ".new.xlsx")
    new_path.unlink(missing_ok=True)
    create_template(new_path)
    wb = load_workbook(new_path)
    for sheet, rows in data.items():
        ws = wb[sheet]
        header = [cell.value for cell in ws[1]]
        for r, row in enumerate(rows, start=2):
            for key, value in row.items():
                if key in header:
                    ws.cell(row=r, column=header.index(key) + 1, value=value)
    wb.save(new_path)

    backup = path.with_name(path.stem + ".backup.xlsx")
    shutil.copy2(path, backup)
    new_path.replace(path)
    return backup


@dataclass
class LoadResult:
    rows: list[BaseModel]
    errors: list[str]  # "rad 5: area_sqm: Input should be greater than 0"


def _records(path: Path, sheet: str) -> list[tuple[int, dict]]:
    df = pd.read_excel(path, sheet_name=sheet, dtype=object)
    df = df.dropna(how="all")
    records = []
    for index, row in df.iterrows():
        record = {k: (None if pd.isna(v) else v) for k, v in row.items()}
        # Text som Excel tolkar som tal eller datum görs om till text där modellen vill ha text.
        for key, value in record.items():
            if isinstance(value, str):
                record[key] = value.strip() or None
            elif hasattr(value, "date") and key in ("published", "collected"):
                record[key] = value.date()
        records.append((int(index) + 2, record))  # +2: rubrikrad och 1-indexering i Excel
    return records


def _validate(records, build) -> LoadResult:
    rows, errors = [], []
    for excel_row, record in records:
        try:
            rows.append(build(record))
        except ValidationError as e:
            for err in e.errors():
                field = ".".join(str(p) for p in err["loc"]) or "rad"
                message = err["msg"].removeprefix("Value error, ")
                errors.append(f"rad {excel_row}: {field}: {message}")
    return LoadResult(rows, errors)


def load_metrics(path: Path = WORKBOOK) -> LoadResult:
    return _validate(_records(path, METRICS_SHEET), lambda r: MarketMetric(**r))


def _listing(record: dict) -> OfficeListing:
    lat, lon = record.pop("latitude"), record.pop("longitude")
    if (lat is None) != (lon is None):
        raise ValidationError.from_exception_data(
            "OfficeListing",
            [{"type": "value_error", "loc": ("coordinates",), "input": (lat, lon),
              "ctx": {"error": ValueError("Fyll i både latitude och longitude, eller ingen av dem.")}}],
        )
    if lat is not None:
        record["coordinates"] = {"latitude": lat, "longitude": lon}
    return OfficeListing(**record)


def load_listings(path: Path = WORKBOOK) -> LoadResult:
    return _validate(_records(path, LISTINGS_SHEET), _listing)
