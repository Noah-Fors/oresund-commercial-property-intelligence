"""Streamlit-fliken för Fas 2: värdera en fastighet med DCF."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pydantic import ValidationError

from src.phase1_location_scoring.location_map import CITY_LABELS, PROPERTY_TYPE_LABELS
from src.phase1_location_scoring.models import City, PropertyType

from .defaults import (
    DEFAULT_HOLDING_PERIOD,
    DEFAULT_INDEXATION,
    DEFAULT_MARKET_RENT,
    DEFAULT_OPEX,
    DEFAULT_PROPERTY_TAX_PER_SQM,
    default_leases,
)
from .leases import Lease, PropertyCashFlowAssumptions, costs, lease_rent, value_with_leases, wault
from .monte_carlo import Uncertainty, simulate
from .sensitivity import yield_rent_matrix
from .yields import discount_rate, required_yield

BAR_COLOR = "#2a78d6"
REFERENCE_INK = "#52514e"


def _sv_number(value: float, decimals: int = 0) -> str:
    """Svensk talformatering: mellanslag som tusentalsavgränsare, komma som decimaltecken."""
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")


def _mkr(value: float) -> str:
    return f"{_sv_number(value / 1e6, 1)} Mkr"


def _pct(value: float) -> str:
    return f"{_sv_number(value * 100, 2)} %"


def _inputs(scores: pd.DataFrame) -> tuple[str, PropertyCashFlowAssumptions, float, int] | None:
    addresses = list(scores.address)
    default_index = addresses.index("Kronborgsvägen 20") if "Kronborgsvägen 20" in addresses else 0
    address = st.selectbox("Fastighet", addresses, index=default_index)
    row = scores.set_index("address").loc[address]
    property_type, city = PropertyType(row.property_type), City(row.city)
    location_score = float(row.total_score)

    st.markdown(
        f"**{PROPERTY_TYPE_LABELS[property_type.value]}, {CITY_LABELS[city.value]}** · "
        f"location score **{location_score:.0f}** (från Fas 1)"
    )

    model_yield = required_yield(property_type, city, location_score)
    override = st.checkbox("Skriv över yield-kravet", key=f"override_{address}")
    if override:
        exit_yield = st.number_input(
            "Yield-krav (%)", value=round(model_yield * 100, 2), step=0.05, format="%.2f",
            key=f"yield_{address}",
        ) / 100
    else:
        exit_yield = model_yield
        st.caption(f"Yield-krav från location score: **{_pct(model_yield)}**")

    st.markdown("**Hyresgäster**")
    leases_default = pd.DataFrame([lease.model_dump() for lease in default_leases(address, property_type)])
    edited = st.data_editor(
        leases_default,
        num_rows="dynamic",
        hide_index=True,
        key=f"leases_{address}",
        column_config={
            "tenant": st.column_config.TextColumn("Namn", help="Hyresgäst"),
            "area_sqm": st.column_config.NumberColumn("Kvm", min_value=1, format="%d"),
            "contract_rent_per_sqm": st.column_config.NumberColumn(
                "Hyra", min_value=0, format="%d", help="Kontraktshyra år 1, kr/kvm"
            ),
            "expiry_year": st.column_config.NumberColumn(
                "Ut år", min_value=1, step=1, format="%d", help="Sista året kontraktshyran betalas"
            ),
            "void_years_after_expiry": st.column_config.NumberColumn(
                "Tomt", min_value=0, step=1, format="%d", help="Antal år lokalen står tom innan den hyrs ut igen"
            ),
        },
    )

    total_area = float(edited.area_sqm.fillna(0).sum())
    market_rent = st.number_input(
        "Marknadshyra år 1 (kr/kvm)", value=int(DEFAULT_MARKET_RENT[property_type]), step=50,
        key=f"rent_{address}",
    )
    indexation = st.number_input(
        "KPI per år (%)", value=DEFAULT_INDEXATION * 100, step=0.25, format="%.2f", key=f"kpi_{address}"
    ) / 100
    opex = st.number_input(
        "Opex år 1 (kr/kvm)", value=int(DEFAULT_OPEX[property_type]), step=10, key=f"opex_{address}"
    )
    property_tax = st.number_input(
        "Fastighetsskatt år 1 (kr)",
        value=int(DEFAULT_PROPERTY_TAX_PER_SQM[property_type] * total_area),
        step=10_000,
        key=f"tax_{address}",
    )
    holding_period = st.slider("Kalkylperiod (år)", 3, 10, DEFAULT_HOLDING_PERIOD, key=f"hold_{address}")

    try:
        leases = [Lease(**record) for record in edited.dropna(how="all").to_dict("records")]
        assumptions = PropertyCashFlowAssumptions(
            leases=leases,
            market_rent_per_sqm=market_rent,
            indexation=indexation,
            opex_per_sqm=opex,
            property_tax=property_tax,
        )
    except (ValidationError, TypeError):
        st.error("Kontrollera hyresgästtabellen: varje rad behöver namn, area, hyra och när kontraktet löper ut.")
        return None
    return address, assumptions, exit_yield, holding_period


def _cash_flow_table(a: PropertyCashFlowAssumptions, result, holding_period: int) -> pd.DataFrame:
    years = range(1, holding_period + 2)
    rows = {f"Hyra {lease.tenant}": [lease_rent(lease, a, y) for y in years] for lease in a.leases}
    rows["Kostnader"] = [-costs(a, y) for y in years]
    rows["NOI"] = [sum(column) for column in zip(*rows.values())]
    rows["PV av NOI"] = [y.present_value for y in result.years] + [np.nan]
    table = pd.DataFrame(rows, index=[f"År {y}" for y in years]).T
    table.columns = [*table.columns[:-1], f"År {holding_period + 1} (exit)"]
    return table.map(lambda v: "" if pd.isna(v) else _sv_number(v))


def _monte_carlo_chart(values: np.ndarray, base_value: float) -> go.Figure:
    mkr = values / 1e6
    p10, p50, p90 = np.percentile(mkr, [10, 50, 90])
    fig = go.Figure(
        go.Histogram(
            x=mkr,
            nbinsx=60,
            marker=dict(color=BAR_COLOR, line=dict(color="white", width=0.5)),
            hovertemplate="Värde %{x:.1f} Mkr<br>%{y} scenarier<extra></extra>",
        )
    )
    for x, label, position in (
        (p10, f"P10 {_sv_number(p10, 1)}", "top left"),
        (p50, f"Median {_sv_number(p50, 1)}", "top left"),
        (p90, f"P90 {_sv_number(p90, 1)}", "top right"),
    ):
        fig.add_vline(x=x, line=dict(color=REFERENCE_INK, dash="dash", width=1.2),
                      annotation_text=label, annotation_position=position)
    fig.add_vline(x=base_value / 1e6, line=dict(color=REFERENCE_INK, width=2))
    # Basfallet ligger nära medianen, så dess etikett placeras lägre för att inte krocka.
    fig.add_annotation(x=base_value / 1e6, y=0.8, yref="paper", xanchor="left", showarrow=False,
                       text=f" <b>Basfall {_sv_number(base_value / 1e6, 1)}</b>",
                       bgcolor="rgba(255,255,255,0.85)")
    fig.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_title="Marknadsvärde (Mkr)",
        yaxis_title="Antal scenarier",
        bargap=0.02,
        showlegend=False,
    )
    return fig


def render_valuation_tab(scores: pd.DataFrame) -> None:
    st.header("Fas 2 — Värderingsmotor")
    st.caption(
        "DCF kontrakt för kontrakt. Yield-kravet räknas fram från location score (Fas 1) och "
        "basyield per fastighetstyp och stad; discount rate = yield + KPI. Basyields, marknadshyror "
        "och kostnader är exempelvärden, inte aktuella marknadsdata. Endast Kronborgsvägen 20 har "
        "verkliga räkneexempel på hyresgäster; övriga börjar med en hyresgäst till marknadshyra."
    )

    left, right = st.columns([1, 2], gap="large")
    with left:
        inputs = _inputs(scores)
    if inputs is None:
        return
    address, a, exit_yield, holding_period = inputs
    rate = discount_rate(exit_yield, a.indexation)
    result = value_with_leases(a, holding_period, rate, exit_yield)

    with right:
        cols = st.columns(5)
        cols[0].metric("Marknadsvärde", _mkr(result.market_value))
        cols[1].metric("Värde per kvm", f"{_sv_number(result.market_value / a.total_area_sqm)} kr")
        cols[2].metric("Yield-krav", _pct(exit_yield))
        cols[3].metric("Discount rate", _pct(rate))
        cols[4].metric("WAULT", f"{_sv_number(wault(a.leases), 1)} år")

        st.subheader("Kassaflöde (kr)")
        st.dataframe(_cash_flow_table(a, result, holding_period), width="stretch")
        st.caption(
            f"Exit value {_mkr(result.exit_value)} i slutet av år {holding_period}, nuvärde "
            f"{_mkr(result.pv_exit_value)}: {_sv_number(result.exit_share_of_value * 100)} % av marknadsvärdet."
        )

        st.subheader("Känslighetsanalys: marknadsvärde (Mkr)")
        matrix = yield_rent_matrix(a, exit_yield, holding_period)
        matrix.index = [f"Yield {_pct(y)}" for y in matrix.index]
        matrix.columns = [f"{_sv_number(rent)} kr/kvm" for rent in matrix.columns]
        st.dataframe(matrix.map(lambda v: _sv_number(v / 1e6, 1)), width="stretch")
        st.caption("Rader: yield-krav ±0,50 procentenheter. Kolumner: marknadshyra ±10 %. Discount rate följer yielden.")

        st.subheader("Monte Carlo-simulering")
        signature = (address, a.model_dump_json(), exit_yield, holding_period)
        if st.button("Kör 10 000 scenarier"):
            st.session_state["monte_carlo"] = (signature, simulate(a, exit_yield, holding_period))
        stored = st.session_state.get("monte_carlo")
        if stored and stored[0] == signature:
            simulation = stored[1]
            values = np.array(simulation.values)
            st.plotly_chart(_monte_carlo_chart(values, result.market_value), width="stretch")
            u = Uncertainty()
            st.markdown(
                f"Med de osäkerheter som antagits kan investeringens värde efter {holding_period} år "
                f"motsvara mellan **{_mkr(simulation.percentile(10))}** och **{_mkr(simulation.percentile(90))}** "
                "idag, med 80 % sannolikhet. Intervallet beskriver osäkerheten i investeringens utfall, "
                "inte osäkerheten i dagens marknadsvärde."
            )
            st.caption(
                f"Antaganden: yield ±{_sv_number(u.exit_yield_sd * 100, 2)} procentenheter, marknadshyra "
                f"±{_sv_number(u.market_rent_sd * 100, 1)} %, KPI ±{_sv_number(u.indexation_sd * 100, 2)} "
                "procentenheter (standardavvikelser), tomställning 0/1/2 år (25/50/25 %) för hyresgäster som "
                f"flyttar och {_sv_number(u.renewal_probability * 100)} % sannolikhet att övriga förnyar. "
                "Antagandena slumpas oberoende av varandra, vilket troligen underskattar risken."
            )
        else:
            st.caption("Klicka för att simulera. Simuleringen körs om när du ändrar något i indata.")
