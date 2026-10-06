from datetime import date, datetime

import pytest
from openpyxl import load_workbook

from src.phase3_market_report.data import (
    LISTINGS_SHEET,
    METRICS_SHEET,
    create_template,
    load_listings,
    load_metrics,
)
from src.phase3_market_report.models import MarketMetric, Metric, OfficeListing


def _fill(path, sheet, rows):
    wb = load_workbook(path)
    ws = wb[sheet]
    header = [cell.value for cell in ws[1]]
    for r, row in enumerate(rows, start=2):
        for key, value in row.items():
            ws.cell(row=r, column=header.index(key) + 1, value=value)
    wb.save(path)


@pytest.fixture
def workbook(tmp_path):
    path = tmp_path / "market.xlsx"
    create_template(path)
    return path


def test_template_is_never_overwritten(workbook):
    with pytest.raises(FileExistsError):
        create_template(workbook)


def test_empty_template_loads_without_rows_or_errors(workbook):
    assert load_metrics(workbook).rows == []
    assert load_listings(workbook).errors == []


def test_single_value_metric_gets_high_equal_to_low():
    metric = MarketMetric(city="malmo", submarket="CBD", metric="prime_yield", low=4.85,
                          source="Exempel", published=date(2026, 3, 31))
    assert metric.high == 4.85
    assert metric.unit == "%"


def test_percent_written_as_decimal_is_rejected():
    with pytest.raises(ValueError, match="4.85"):
        MarketMetric(city="malmo", submarket="CBD", metric="vacancy_rate", low=0.10,
                     source="Exempel", published=date(2026, 3, 31))


def test_monthly_rent_is_caught():
    with pytest.raises(ValueError, match="per månad"):
        OfficeListing(address="Stortorget 1", city="malmo", district="Centrum", area_sqm=200,
                      asking_rent_per_sqm=35_000, source="Exempel", collected=date(2026, 10, 6))


def test_metrics_sheet_reads_excel_dates_and_ranges(workbook):
    _fill(workbook, METRICS_SHEET, [
        {"city": "lund", "submarket": "Lägesklass A", "metric": "rent_range", "low": 1700, "high": 2700,
         "source": "Exempel", "published": datetime(2026, 6, 30)},
    ])
    result = load_metrics(workbook)
    assert result.errors == []
    [metric] = result.rows
    assert metric.metric is Metric.RENT_RANGE
    assert metric.published == date(2026, 6, 30)
    assert metric.midpoint == 2200


def test_listing_errors_point_to_the_excel_row(workbook):
    valid = {"address": "Stortorget 1", "city": "malmo", "district": "Centrum", "area_sqm": 250,
             "asking_rent_per_sqm": 2100, "source": "Exempel", "collected": "2026-10-06",
             "latitude": 55.6066, "longitude": 13.0010}
    _fill(workbook, LISTINGS_SHEET, [
        valid,
        {**valid, "city": "Malmö"},
        {**valid, "longitude": None},
        {**valid, "asking_rent_per_sqm": None},
    ])
    result = load_listings(workbook)
    assert len(result.rows) == 2
    assert result.rows[0].coordinates.latitude == 55.6066
    assert result.rows[1].asking_rent_per_sqm is None
    assert result.errors[0].startswith("rad 3: city")
    assert result.errors[1].startswith("rad 4: coordinates")
