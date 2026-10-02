import streamlit as st
from streamlit_folium import st_folium

from src.phase1_location_scoring.location_map import (
    CITY_LABELS,
    PROPERTY_TYPE_LABELS,
    build_score_map,
)
from src.phase1_location_scoring.sample_data import load_properties, load_transit_stops
from src.phase1_location_scoring.scoring import TRANSIT_HALF_DISTANCE_M, score_transit

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
        "Transit-poäng 0–100 utifrån avståndet till närmaste tåg- eller "
        f"spårvagnsstation. Poängen halveras var {TRANSIT_HALF_DISTANCE_M} m. "
        "Arbetsplatser och kommersiell täthet läggs till senare. "
        "Exempeldata, koordinater delvis ungefärliga."
    )

    stops = load_transit_stops()
    scores = score_transit(load_properties(), stops)

    st_folium(
        build_score_map(scores, stops),
        height=560,
        use_container_width=True,
        returned_objects=[],
    )

    table = scores.assign(
        city=scores.city.map(CITY_LABELS),
        property_type=scores.property_type.map(PROPERTY_TYPE_LABELS),
    )
    st.dataframe(
        table[["address", "city", "property_type", "nearest_stop", "distance_m", "transit_score"]],
        hide_index=True,
        use_container_width=True,
        column_config={
            "address": "Adress",
            "city": "Stad",
            "property_type": "Typ",
            "nearest_stop": "Närmaste station",
            "distance_m": st.column_config.NumberColumn("Avstånd (m)", format="%d"),
            "transit_score": st.column_config.ProgressColumn(
                "Transit-poäng", min_value=0, max_value=100, format="%.0f"
            ),
        },
    )

with tab2:
    st.header("Fas 2 — Värderingsmotor")
    st.info("Inte implementerad än. Se docs/plan.md för fasbeskrivning.")

with tab3:
    st.header("Fas 3 — Marknadsdashboard och rapport")
    st.info("Inte implementerad än. Se docs/plan.md för fasbeskrivning.")
