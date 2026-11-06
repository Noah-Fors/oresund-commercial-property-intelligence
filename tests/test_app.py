"""Kör hela Streamlit-appen i testläge och kontrollerar värderingsfliken."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")


def _metrics(at: AppTest) -> dict[str, str]:
    return {metric.label: metric.value for metric in at.metric}


def test_app_runs_and_values_kronborgsvagen_like_the_excel_model():
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception
    assert at.selectbox[0].value == "Kronborgsvägen 20"
    metrics = _metrics(at)
    assert metrics["Marknadsvärde"] == "41,1 Mkr"
    assert metrics["Yield-krav"] == "5,98 %"
    assert metrics["WAULT"] == "3,3 år"


def test_every_sample_property_can_be_valued():
    at = AppTest.from_file(APP, default_timeout=120).run()
    for address in at.selectbox[0].options:
        at.selectbox[0].select(address).run()
        assert not at.exception, address
        assert _metrics(at)["Marknadsvärde"].endswith("Mkr"), address
