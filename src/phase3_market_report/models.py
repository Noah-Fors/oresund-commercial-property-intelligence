"""Datamodeller för Fas 3: marknadsnyckeltal från rapporter och kontorsannonser.

Två sorters data, med olika ursprung:

- MarketMetric: ett nyckeltal som en rådgivningsfirma har publicerat (prime rent,
  vacancy rate, prime yield ...). Det är någon annans mätning, så källan och
  publiceringsdatumet är obligatoriska.
- OfficeListing: en lokal som annonseras för uthyrning. Det är vår egen
  primärdata, och hyran är en asking rent, inte en avtalad hyra.
"""

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl, model_validator

from src.phase1_location_scoring.models import City, Coordinates


class Segment(str, Enum):
    """Marknadssegment som rapporterna delar in hyresmarknaden i."""

    OFFICE = "office"          # kontor
    RETAIL = "retail"          # butik
    INDUSTRIAL = "industrial"  # industri, lager och logistik


SEGMENT_LABELS = {"office": "Kontor", "retail": "Butik", "industrial": "Industri"}


class Metric(str, Enum):
    PRIME_RENT = "prime_rent"                  # kr/kvm/år, högsta hyran för de bästa lokalerna
    RENT_RANGE = "rent_range"                  # kr/kvm/år, normalt hyresintervall i ett delområde
    VACANCY_RATE = "vacancy_rate"              # %, andel lediga kvm av beståndet
    PRIME_YIELD = "prime_yield"                # %, direktavkastningskrav för de bästa fastigheterna
    TAKE_UP = "take_up"                        # kvm, uthyrd yta under perioden
    TRANSACTION_VOLUME = "transaction_volume"  # Mkr, köp och försäljningar under perioden


METRIC_UNITS: dict[Metric, str] = {
    Metric.PRIME_RENT: "kr/kvm/år",
    Metric.RENT_RANGE: "kr/kvm/år",
    Metric.VACANCY_RATE: "%",
    Metric.PRIME_YIELD: "%",
    Metric.TAKE_UP: "kvm",
    Metric.TRANSACTION_VOLUME: "Mkr",
}

# Rimliga värden för kontor i Skåne. Ett värde utanför intervallet är nästan
# alltid ett inmatningsfel: fel nyckeltal i rullistan, procent som decimaltal,
# hyra per månad i stället för per år, eller miljoner skrivna som kronor.
PLAUSIBLE_RANGES: dict[Metric, tuple[float, float]] = {
    Metric.PRIME_RENT: (500, 10_000),
    Metric.RENT_RANGE: (300, 10_000),
    Metric.VACANCY_RATE: (0.5, 50),
    Metric.PRIME_YIELD: (1, 15),
    Metric.TAKE_UP: (100, 2_000_000),
    Metric.TRANSACTION_VOLUME: (1, 200_000),
}


class MarketMetric(BaseModel):
    """Ett nyckeltal ur en marknadsrapport. Ett enskilt värde har low == high."""

    city: City
    submarket: str = Field(..., min_length=1, description="T.ex. 'CBD', 'Lägesklass A', 'Hela staden'.")
    segment: Segment
    metric: Metric
    low: float = Field(..., ge=0)
    high: float | None = Field(default=None, ge=0, description="Tomt om rapporten anger ett enda värde.")
    source: str = Field(..., min_length=1, description="Vem som publicerat siffran.")
    published: date = Field(..., description="Rapportens datum eller kvartalets sista dag.")
    url: HttpUrl | None = None

    @model_validator(mode="after")
    def _single_value_or_ordered_range(self) -> "MarketMetric":
        if self.high is None:
            self.high = self.low
        if self.high < self.low:
            raise ValueError(f"high ({self.high}) är lägre än low ({self.low}).")
        minimum, maximum = PLAUSIBLE_RANGES[self.metric]
        for value in (self.low, self.high):
            if not minimum <= value <= maximum:
                hint = " Skriv 4,85 i Excel, inte 4,85 % eller 0,0485." if self.unit == "%" else ""
                raise ValueError(
                    f"{value:g} {self.unit} är inte rimligt för {self.metric.value} "
                    f"(förväntat {minimum:g}–{maximum:g}). Har du valt rätt nyckeltal i listan?{hint}"
                )
        return self

    @property
    def unit(self) -> str:
        return METRIC_UNITS[self.metric]

    @property
    def midpoint(self) -> float:
        return (self.low + self.high) / 2


class OfficeListing(BaseModel):
    """En kontorslokal som annonseras för uthyrning."""

    address: str = Field(..., min_length=1)
    city: City
    district: str = Field(..., min_length=1, description="Stadsdel eller delområde, t.ex. 'Västra Hamnen'.")
    area_sqm: float = Field(..., gt=0, description="Lokalens area i kvm.")
    asking_rent_per_sqm: float | None = Field(
        default=None,
        gt=0,
        description="Begärd hyra i kr/kvm/år. Tomt om annonsen inte anger hyran.",
    )
    rent_terms: str | None = Field(
        default=None, description="Vad hyran inkluderar, t.ex. 'inkl. värme, tillägg för fastighetsskatt'."
    )
    coordinates: Coordinates | None = None
    source: str = Field(..., min_length=1, description="Annonssajt eller hyresvärd.")
    url: HttpUrl | None = None
    collected: date = Field(..., description="Datum du läste annonsen.")

    @model_validator(mode="after")
    def _plausible_office_rent(self) -> "OfficeListing":
        # Kontorshyror i Skåne ligger i praktiken mellan några hundra och några tusen kr/kvm/år.
        # Utanför det intervallet är det nästan alltid hyra per månad eller total hyra.
        rent = self.asking_rent_per_sqm
        if rent is not None and not 300 <= rent <= 6_000:
            raise ValueError(
                f"Hyran {rent:.0f} kr/kvm/år verkar orimlig. Är det hyra per månad eller total hyra? "
                "Räkna om till kr/kvm/år: månadshyra × 12 / kvm."
            )
        return self
