"""Steg 3b: kassaflöde kontrakt för kontrakt.

Varje hyreskontrakt betalar sin kontraktshyra till och med `expiry_year`.
Därefter står lokalen tom i `void_years_after_expiry` år, och sedan hyrs den
ut (till samma eller ny hyresgäst) till marknadshyra. Alla hyror och
kostnader räknas upp med KPI från år 1.

År räknas från 1. "Löper ut år 2" betyder i slutet av år 2.
"""

from pydantic import BaseModel, Field

from .dcf import DcfResult, discounted_cash_flow


class Lease(BaseModel):
    tenant: str
    area_sqm: float = Field(..., gt=0)
    contract_rent_per_sqm: float = Field(..., ge=0, description="Kontraktshyra år 1, kr/kvm.")
    expiry_year: int = Field(..., ge=1, description="Sista året kontraktshyran betalas.")
    void_years_after_expiry: int = Field(
        default=0, ge=0, description="År utan hyra innan lokalen hyrs ut till marknadshyra."
    )

    @property
    def annual_rent_year_1(self) -> float:
        return self.area_sqm * self.contract_rent_per_sqm


class PropertyCashFlowAssumptions(BaseModel):
    leases: list[Lease] = Field(..., min_length=1)
    market_rent_per_sqm: float = Field(..., gt=0, description="Marknadshyra år 1, kr/kvm.")
    indexation: float = Field(..., ge=-0.1, le=0.5, description="KPI per år, t.ex. 0.02.")
    opex_per_sqm: float = Field(..., ge=0, description="Drift + underhåll år 1, kr/kvm.")
    property_tax: float = Field(..., ge=0, description="Fastighetsskatt år 1, kr.")

    @property
    def total_area_sqm(self) -> float:
        return sum(lease.area_sqm for lease in self.leases)


def _index(indexation: float, year: int) -> float:
    return (1 + indexation) ** (year - 1)


def market_rent_per_sqm(a: PropertyCashFlowAssumptions, year: int) -> float:
    return a.market_rent_per_sqm * _index(a.indexation, year)


def _is_void(lease: Lease, year: int) -> bool:
    return lease.expiry_year < year <= lease.expiry_year + lease.void_years_after_expiry


def lease_rent(lease: Lease, a: PropertyCashFlowAssumptions, year: int) -> float:
    """Hyra från ett kontrakt under ett visst år."""
    if year <= lease.expiry_year:
        return lease.annual_rent_year_1 * _index(a.indexation, year)
    if _is_void(lease, year):
        return 0.0
    return lease.area_sqm * market_rent_per_sqm(a, year)


def costs(a: PropertyCashFlowAssumptions, year: int) -> float:
    """Opex och fastighetsskatt. Betalas för hela arean, även när lokaler står tomma."""
    return (a.opex_per_sqm * a.total_area_sqm + a.property_tax) * _index(a.indexation, year)


def noi(a: PropertyCashFlowAssumptions, year: int) -> float:
    return sum(lease_rent(lease, a, year) for lease in a.leases) - costs(a, year)


def wault(leases: list[Lease]) -> float:
    """Weighted Average Unexpired Lease Term idag, viktat med årshyran år 1."""
    total_rent = sum(lease.annual_rent_year_1 for lease in leases)
    return sum(lease.expiry_year * lease.annual_rent_year_1 for lease in leases) / total_rent


def value_with_leases(
    a: PropertyCashFlowAssumptions,
    holding_period_years: int,
    discount_rate: float,
    exit_yield: float,
) -> DcfResult:
    """DCF där NOI räknas fram kontrakt för kontrakt."""
    noi_by_year = [noi(a, year) for year in range(1, holding_period_years + 1)]
    exit_noi, void_deduction = stabilised_exit(a, holding_period_years)
    return discounted_cash_flow(
        noi_by_year, exit_noi, discount_rate, exit_yield, exit_deduction=void_deduction
    )


def stabilised_exit(a: PropertyCashFlowAssumptions, holding_period_years: int) -> tuple[float, float]:
    """NOI för exit-året som om alla lokaler vore uthyrda, och förlorad hyra att dra av.

    Lokaler som står tomma vid eller efter exit räknas som uthyrda till marknadshyra
    i exit-NOI. Hyran de går miste om under tomställningen dras istället av från
    exit value (void deduction), eftersom köparen tar den förlusten.
    """
    exit_year = holding_period_years + 1
    rent = sum(
        lease.area_sqm * market_rent_per_sqm(a, exit_year)
        if _is_void(lease, exit_year)
        else lease_rent(lease, a, exit_year)
        for lease in a.leases
    )
    void_deduction = sum(
        lease.area_sqm * market_rent_per_sqm(a, year)
        for lease in a.leases
        for year in range(
            max(exit_year, lease.expiry_year + 1),
            lease.expiry_year + lease.void_years_after_expiry + 1,
        )
    )
    return rent - costs(a, exit_year), void_deduction
