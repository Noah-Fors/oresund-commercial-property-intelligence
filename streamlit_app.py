import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.phase1_location_scoring.location_map import (
    CITY_LABELS,
    PROPERTY_TYPE_LABELS,
    build_score_map,
)
from src.phase1_location_scoring.sample_data import (
    load_commercial_counts,
    load_highway_interchanges,
    load_properties,
    load_transit_stops,
)
from src.phase1_location_scoring.scoring import (
    COMMERCIAL_HALF_COUNT,
    HIGHWAY_HALF_DISTANCE_M,
    TRANSIT_HALF_DISTANCE_M,
    WEIGHTS,
    score_properties,
)
from src.phase2_valuation.ui import render_valuation_tab

st.set_page_config(
    page_title="Öresund Commercial Property Intelligence",
    page_icon="🏢",
    layout="wide",
)

st.title("🏢 Öresund Commercial Property Intelligence Platform")
st.caption(
    "Geospatial location scoring, fastighetsvärdering och marknadsdata "
    "för kommersiella fastigheter i Malmö / Lund / Helsingborg."
)

tab1, tab2, tab3 = st.tabs(
    ["📍 Location scoring", "💰 Värderingsmotor", "📊 Marknadsrapport"]
)

with tab1:
    st.header("Fas 1 — Geospatial location scoring")
    st.caption(
        "Location score 0–100, viktat efter fastighetstyp. Just nu ingår avstånd till "
        f"närmaste tåg-/spårvagnsstation (halveras var {TRANSIT_HALF_DISTANCE_M} m) och "
        f"till närmaste motorvägstrafikplats (halveras var {HIGHWAY_HALF_DISTANCE_M} m), "
        "samt kommersiell täthet: antal butiker, restauranger, caféer, barer, banker och "
        f"apotek inom 500 m enligt OpenStreetMap ({COMMERCIAL_HALF_COUNT} verksamheter ger 50 poäng). "
        "OpenStreetMap kan vara ofullständigt, t.ex. saknas troligen butikerna inne i Emporia. "
        "Arbetsplatser saknar tillförlitlig data än och hoppas över. "
        "Exempeldata, koordinater delvis ungefärliga."
    )

    stops = load_transit_stops()
    interchanges = load_highway_interchanges()
    scores = score_properties(load_properties(), stops, interchanges, load_commercial_counts())

    st_folium(
        build_score_map(scores, stops, interchanges),
        height=560,
        use_container_width=True,
        returned_objects=[],
    )

    table = scores.assign(
        city=scores.city.map(CITY_LABELS),
        property_type=scores.property_type.map(PROPERTY_TYPE_LABELS),
    )

    def score_column(label: str):
        return st.column_config.ProgressColumn(label, min_value=0, max_value=100, format="%.0f")

    st.dataframe(
        table[[
            "address", "city", "property_type", "total_score",
            "transit_score", "nearest_stop", "highway_score", "nearest_interchange",
            "commercial_density_score", "commercial_count",
        ]],
        hide_index=True,
        width="stretch",
        column_config={
            "address": "Adress",
            "city": "Stad",
            "property_type": "Typ",
            "total_score": score_column("Location score"),
            "transit_score": score_column("Kollektivtrafik"),
            "nearest_stop": "Närmaste station",
            "highway_score": score_column("Motorväg"),
            "nearest_interchange": "Närmaste trafikplats",
            "commercial_density_score": score_column("Kommersiell täthet"),
            "commercial_count": st.column_config.NumberColumn("Verksamheter inom 500 m", format="%d"),
        },
    )

    with st.expander("Hur vikterna fungerar"):
        st.markdown(
            "Varje fastighetstyp väger parametrarna olika. Parametrar som saknar "
            "data hoppas över, och de övrigas vikter skalas upp så att de summerar till 100 %."
        )
        st.dataframe(
            pd.DataFrame(
                {PROPERTY_TYPE_LABELS[t.value]: w for t, w in WEIGHTS.items()}
            ).T.rename(columns={
                "transit_score": "Kollektivtrafik (%)",
                "employment_score": "Arbetsplatser (%)",
                "commercial_density_score": "Kommersiell täthet (%)",
                "highway_score": "Motorväg (%)",
            }),
            width="stretch",
        )

with tab2:
    render_valuation_tab(scores)

with tab3:
    st.header("Fas 3 — Marknadsdashboard och rapport")
    st.info("Inte implementerad än. Se docs/plan.md för fasbeskrivning.")
