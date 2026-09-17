import streamlit as st

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
    st.info("Inte implementerad än. Se docs/plan.md för fasbeskrivning.")

with tab2:
    st.header("Fas 2 — Värderingsmotor")
    st.info("Inte implementerad än. Se docs/plan.md för fasbeskrivning.")

with tab3:
    st.header("Fas 3 — Marknadsdashboard och rapport")
    st.info("Inte implementerad än. Se docs/plan.md för fasbeskrivning.")
