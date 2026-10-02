"""Interaktiv Folium-karta över location score."""

from html import escape

import folium
import pandas as pd
from branca.colormap import LinearColormap

from .models import TransitStop

# Sekventiell blå skala (ljus = lågt, mörk = högt). Börjar på en mellanljus
# nyans så att även låga poäng syns mot den ljusa bakgrundskartan.
SCORE_COLORS = [
    "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6",
    "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b",
]
STOP_INK = "#52514e"
SURFACE = "#fcfcfb"

PROPERTY_TYPE_LABELS = {
    "office": "Kontor",
    "retail": "Handel",
    "logistics": "Logistik",
    "mixed_use": "Blandad",
}
CITY_LABELS = {"malmo": "Malmö", "lund": "Lund", "helsingborg": "Helsingborg"}


def _property_tooltip(row) -> str:
    distance = f"{row.distance_m:,}".replace(",", " ")
    return (
        f"<b>{escape(row.address)}</b><br>"
        f"{CITY_LABELS[row.city]} · {PROPERTY_TYPE_LABELS[row.property_type]}<br>"
        f"Närmaste station: {escape(row.nearest_stop)} ({distance} m)<br>"
        f"<b>Transit-poäng: {row.transit_score:.0f}</b> / 100"
    )


def build_score_map(scores: pd.DataFrame, stops: list[TransitStop]) -> folium.Map:
    colormap = LinearColormap(SCORE_COLORS, vmin=0, vmax=100, caption="Transit-poäng (0–100)")

    fmap = folium.Map(tiles="OpenStreetMap", control_scale=True)

    for stop in stops:
        folium.CircleMarker(
            location=(stop.coordinates.latitude, stop.coordinates.longitude),
            radius=5,
            color=STOP_INK,
            weight=2,
            fill=True,
            fill_color=SURFACE,
            fill_opacity=1,
            tooltip=f"Station: {escape(stop.name)}",
        ).add_to(fmap)

    for row in scores.itertuples():
        folium.CircleMarker(
            location=(row.latitude, row.longitude),
            radius=9,
            color=SURFACE,
            weight=2,
            fill=True,
            fill_color=colormap(row.transit_score),
            fill_opacity=1,
            tooltip=folium.Tooltip(_property_tooltip(row)),
        ).add_to(fmap)

    colormap.add_to(fmap)

    lats = list(scores.latitude) + [s.coordinates.latitude for s in stops]
    lons = list(scores.longitude) + [s.coordinates.longitude for s in stops]
    fmap.fit_bounds([(min(lats), min(lons)), (max(lats), max(lons))], padding=(20, 20))
    return fmap
