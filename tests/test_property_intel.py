"""Tester för insamlingen från MSCI Property Intel. Siffrorna är påhittade, inte licensierad data."""

from datetime import datetime

import pytest
from openpyxl import load_workbook

from src.phase3_market_report.models import Segment
from src.phase3_market_report.property_intel import (
    NORMALS_SHEET,
    PROPERTIES_SHEET,
    NormalValue,
    create_template,
    load_normal_values,
    load_properties,
)

OFFICE = {"designation": "Exempel 1", "address": "Exempelgatan 1", "city": "malmo", "property_type": "office",
          "type_code": 325, "taxed_area_sqm": 5000, "tax_value_ksek": 80000, "value_year": 1990,
          "latitude": 55.60, "longitude": 13.00, "collected": datetime(2026, 11, 6)}
NORMAL = {"designation": "Exempel 1", "source": "Croisette", "segment": "office", "location": "C Malmö tätort",
          "value_years": "- 2009", "rent_per_sqm": 1500, "vacancy_pct": 10, "yield_pct": 7.1,
          "heating": "varm", "published": datetime(2026, 6, 30)}


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
    path = tmp_path / "property_intel.xlsx"
    create_template(path)
    _fill(path, PROPERTIES_SHEET, [OFFICE])
    return path


def test_valid_property_and_normal_values_load(workbook):
    _fill(workbook, NORMALS_SHEET, [NORMAL, {**NORMAL, "source": "Forum", "location": "B Övriga Malmö"}])
    [prop] = load_properties(workbook).rows
    assert prop.coordinates.latitude == 55.60
    result = load_normal_values(workbook)
    assert result.errors == []
    assert [v.location_class for v in result.rows] == ["C", "B"]


def test_sources_may_vary_and_unknown_sources_are_allowed(workbook):
    _fill(workbook, NORMALS_SHEET, [{**NORMAL, "source": "Newsec"}])
    assert len(load_normal_values(workbook).rows) == 1


def test_value_years_that_excel_turned_into_a_negative_number_become_text():
    value = NormalValue(**{**NORMAL, "value_years": -2009})
    assert value.value_years == "- 2009"


def test_location_must_start_with_a_location_class():
    with pytest.raises(ValueError, match="lägesklass"):
        NormalValue(**{**NORMAL, "location": "Malmö tätort"})


def test_yield_written_as_decimal_is_rejected():
    with pytest.raises(ValueError):
        NormalValue(**{**NORMAL, "yield_pct": 0.071})


def test_normal_value_for_unknown_property_is_an_error(workbook):
    _fill(workbook, NORMALS_SHEET, [{**NORMAL, "designation": "Saknas 9"}])
    assert load_normal_values(workbook).errors == ["rad 2: Saknas 9 finns inte i fliken Fastigheter."]


def test_wrong_segment_for_property_type_is_an_error(workbook):
    _fill(workbook, NORMALS_SHEET, [{**NORMAL, "segment": "residential"}])
    [error] = load_normal_values(workbook).errors
    assert "Läs raden för fastighetens typ" in error


def test_mixed_use_may_have_one_row_per_segment_and_source(workbook):
    _fill(workbook, PROPERTIES_SHEET, [{**OFFICE, "property_type": "mixed_use", "type_code": 321}])
    _fill(workbook, NORMALS_SHEET, [
        {**NORMAL, "segment": "residential", "location": "A Slottsstaden", "yield_pct": 4.0, "vacancy_pct": 0},
        {**NORMAL, "segment": "retail"},
        {**NORMAL, "segment": "retail"},
    ])
    result = load_normal_values(workbook)
    assert {v.segment for v in result.rows} == {Segment.RESIDENTIAL, Segment.RETAIL}
    assert result.errors == ["rad 4: Croisette har redan en rad för Exempel 1 (retail)."]


def test_duplicate_designation_is_an_error(workbook):
    _fill(workbook, PROPERTIES_SHEET, [OFFICE, OFFICE])
    assert load_properties(workbook).errors == ["Exempel 1: fastighetsbeteckningen finns på flera rader."]


def test_template_is_never_overwritten(workbook):
    with pytest.raises(FileExistsError):
        create_template(workbook)
