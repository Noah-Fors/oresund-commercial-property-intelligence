"""Datamodeller för Fas 1 — geospatial location scoring.

Modellerna här beskriver bara *strukturen* på datan (vad en fastighet är,
hur ett location score ser ut). Själva uträkningen av score hör hemma i
en separat modul (scoring.py), inte här.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

# Ungefärlig bounding box (WGS84-grader) för Skåne / Öresundsregionen.
# Används för att fånga uppenbart felaktiga koordinater tidigt.
_SKANE_LATITUDE_RANGE = (55.2, 56.4)
_SKANE_LONGITUDE_RANGE = (12.4, 14.6)


class City(str, Enum):
    MALMO = "malmo"
    LUND = "lund"
    HELSINGBORG = "helsingborg"


class PropertyType(str, Enum):
    OFFICE = "office"
    RETAIL = "retail"
    LOGISTICS = "logistics"
    MIXED_USE = "mixed_use"


class Coordinates(BaseModel):
    """En WGS84-punkt (latitud/longitud) inom Öresundsregionen."""

    latitude: float = Field(..., description="Latitud i grader (WGS84).")
    longitude: float = Field(..., description="Longitud i grader (WGS84).")

    @field_validator("latitude")
    @classmethod
    def _latitude_within_skane(cls, value: float) -> float:
        low, high = _SKANE_LATITUDE_RANGE
        if not (low <= value <= high):
            raise ValueError(
                f"Latitud {value} ligger utanför Skåne-regionen ({low}–{high})."
            )
        return value

    @field_validator("longitude")
    @classmethod
    def _longitude_within_skane(cls, value: float) -> float:
        low, high = _SKANE_LONGITUDE_RANGE
        if not (low <= value <= high):
            raise ValueError(
                f"Longitud {value} ligger utanför Skåne-regionen ({low}–{high})."
            )
        return value


class CommercialProperty(BaseModel):
    """En kommersiell fastighet vi vill poängsätta och/eller värdera."""

    id: UUID = Field(default_factory=uuid4)
    address: str = Field(..., min_length=1, description="Gatuadress.")
    city: City
    coordinates: Coordinates
    property_type: PropertyType
    area_sqm: float | None = Field(
        default=None,
        gt=0,
        description="Uthyrningsbar area i kvadratmeter, om känd.",
    )


class TransitStop(BaseModel):
    """En station eller hållplats i kollektivtrafiken."""

    name: str = Field(..., min_length=1)
    city: City
    stop_type: str = Field(..., description="T.ex. 'rail' eller 'tram'.")
    coordinates: Coordinates


class LocationScoreComponents(BaseModel):
    """Delpoäng (0–100) per faktor som bygger upp location score."""

    transit_score: float = Field(
        ..., ge=0, le=100, description="Närhet till kollektivtrafik."
    )
    employment_score: float = Field(
        ..., ge=0, le=100, description="Närhet till arbetsplatskoncentrationer."
    )
    commercial_density_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Täthet av kommersiell verksamhet i närområdet.",
    )


class LocationScore(BaseModel):
    """Totalt location score för en fastighet, med spårbar uppdelning."""

    property_id: UUID
    components: LocationScoreComponents
    total_score: float = Field(
        ..., ge=0, le=100, description="Sammanvägt totalpoäng 0–100."
    )
    computed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
