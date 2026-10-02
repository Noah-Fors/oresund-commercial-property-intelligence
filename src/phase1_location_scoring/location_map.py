"""Interaktiv Folium-karta över location score."""

from html import escape

import folium
import pandas as pd
from branca.colormap import LinearColormap

from .models import HighwayInterchange, TransitStop

# Sekventiell blå skala (ljus = lågt, mörk = högt). Börjar på en mellanljus
# nyans så att även låga poäng syns mot den ljusa bakgrundskartan.
SCORE_COLORS = [
    "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6",
    "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b",
]
REFERENCE_INK = "#52514e"
SURFACE = "#fcfcfb"

PROPERTY_TYPE_LABELS = {
    "office": "Kontor",
    "retail_local": "Tätortshandel",
    "retail_external": "Externhandel",
    "logistics": "Logistik",
    "mixed_use": "Blandad",
}
CITY_LABELS = {"malmo": "Malmö", "lund": "Lund", "helsingborg": "Helsingborg"}


def _meters(value: int) -> str:
    return f"{value:,} m".replace(",", " ")


def _property_tooltip(row) -> str:
    return (
        f"<b>{escape(row.address)}</b><br>"
        f"{CITY_LABELS[row.city]} · {PROPERTY_TYPE_LABELS[row.property_type]}<br>"
        f"<b>Location score: {row.total_score:.0f}</b> / 100<br>"
        f"Kollektivtrafik: {row.transit_score:.0f} "
        f"({escape(row.nearest_stop)}, {_meters(row.stop_distance_m)})<br>"
        f"Motorväg: {row.highway_score:.0f} "
        f"({escape(row.nearest_interchange)}, {_meters(row.interchange_distance_m)})"
    )


def _reference_marker(coords, tooltip: str, filled: bool) -> folium.CircleMarker:
    return folium.CircleMarker(
        location=(coords.latitude, coords.longitude),
        radius=5,
        color=REFERENCE_INK,
        weight=2,
        fill=True,
        fill_color=REFERENCE_INK if filled else SURFACE,
        fill_opacity=1,
        tooltip=tooltip,
    )


def build_score_map(
    scores: pd.DataFrame,
    stops: list[TransitStop],
    interchanges: list[HighwayInterchange],
) -> folium.Map:
    colormap = LinearColormap(SCORE_COLORS, vmin=0, vmax=100, caption="Location score (0–100)")

    fmap = folium.Map(tiles="OpenStreetMap", control_scale=True)

    for stop in stops:
        _reference_marker(stop.coordinates, f"Station: {escape(stop.name)}", filled=False).add_to(fmap)
    for ic in interchanges:
        tooltip = f"Trafikplats: {escape(ic.name)} ({escape(ic.road)})"
        _reference_marker(ic.coordinates, tooltip, filled=True).add_to(fmap)

    for row in scores.itertuples():
        folium.CircleMarker(
            location=(row.latitude, row.longitude),
            radius=9,
            color=SURFACE,
            weight=2,
            fill=True,
            fill_color=colormap(row.total_score),
            fill_opacity=1,
            tooltip=folium.Tooltip(_property_tooltip(row)),
        ).add_to(fmap)

    colormap.add_to(fmap)

    lats = list(scores.latitude) + [p.coordinates.latitude for p in [*stops, *interchanges]]
    lons = list(scores.longitude) + [p.coordinates.longitude for p in [*stops, *interchanges]]
    fmap.fit_bounds([(min(lats), min(lons)), (max(lats), max(lons))], padding=(20, 20))
    return fmap
