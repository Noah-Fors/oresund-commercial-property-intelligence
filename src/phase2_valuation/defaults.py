"""Utgångsvärden för värderingsfliken när riktiga kontraktsdata saknas.

EXEMPELVÄRDEN, inte marknadsdata. Användaren ändrar dem i appen.
"""

from src.phase1_location_scoring.models import PropertyType

from .leases import Lease

DEFAULT_AREA_SQM = 2_000
DEFAULT_LEASE_YEARS = 5
DEFAULT_HOLDING_PERIOD = 5
DEFAULT_INDEXATION = 0.02

# kr/kvm/år
DEFAULT_MARKET_RENT: dict[PropertyType, float] = {
    PropertyType.OFFICE: 1_800,
    PropertyType.RETAIL_LOCAL: 2_200,
    PropertyType.RETAIL_EXTERNAL: 1_700,
    PropertyType.LOGISTICS: 900,
    PropertyType.MIXED_USE: 1_600,
}
DEFAULT_OPEX: dict[PropertyType, float] = {
    PropertyType.OFFICE: 430,
    PropertyType.RETAIL_LOCAL: 400,
    PropertyType.RETAIL_EXTERNAL: 350,
    PropertyType.LOGISTICS: 150,
    PropertyType.MIXED_USE: 400,
}
# Fastighetsskatt per kvm. Industri/logistik har lägre skattesats än lokaler.
DEFAULT_PROPERTY_TAX_PER_SQM: dict[PropertyType, float] = {
    PropertyType.OFFICE: 90,
    PropertyType.RETAIL_LOCAL: 90,
    PropertyType.RETAIL_EXTERNAL: 90,
    PropertyType.LOGISTICS: 40,
    PropertyType.MIXED_USE: 90,
}

# Räkneexemplet från Fas 2, steg 3b.
KNOWN_LEASES: dict[str, list[Lease]] = {
    "Kronborgsvägen 20": [
        Lease(tenant="A", area_sqm=1_200, contract_rent_per_sqm=1_700, expiry_year=2, void_years_after_expiry=1),
        Lease(tenant="B", area_sqm=800, contract_rent_per_sqm=1_900, expiry_year=5),
    ],
}


def default_leases(address: str, property_type: PropertyType) -> list[Lease]:
    if address in KNOWN_LEASES:
        return KNOWN_LEASES[address]
    return [
        Lease(
            tenant="Hyresgäst 1",
            area_sqm=DEFAULT_AREA_SQM,
            contract_rent_per_sqm=DEFAULT_MARKET_RENT[property_type],
            expiry_year=DEFAULT_LEASE_YEARS,
        )
    ]
