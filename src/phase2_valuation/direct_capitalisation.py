"""Steg 1–2 i värderingen: från hyra till NOI och marknadsvärde.

Kedjan:  hyresvärde -> hyresintäkt (efter vacancy) -> NOI -> värde = NOI / yield

Alla belopp är i kr per år, hyror och opex i kr/kvm/år.
Procentsatser anges som decimaltal: 8 % = 0.08, 5,25 % = 0.0525.
"""

from pydantic import BaseModel, Field


class OperatingAssumptions(BaseModel):
    """Antaganden om en fastighets intäkter och kostnader under ett år."""

    area_sqm: float = Field(..., gt=0, description="Uthyrningsbar area, kvm.")
    market_rent_per_sqm: float = Field(..., gt=0, description="Marknadshyra, kr/kvm/år.")
    vacancy_rate: float = Field(..., ge=0, lt=1, description="Vakansgrad, t.ex. 0.08.")
    operating_cost_per_sqm: float = Field(..., ge=0, description="Opex drift, kr/kvm/år.")
    maintenance_per_sqm: float = Field(..., ge=0, description="Opex underhåll, kr/kvm/år.")
    property_tax: float = Field(..., ge=0, description="Fastighetsskatt, kr/år.")


def gross_potential_rent(a: OperatingAssumptions) -> float:
    """Hyresvärde: hyran om hela arean vore uthyrd."""
    return a.area_sqm * a.market_rent_per_sqm


def rental_income(a: OperatingAssumptions) -> float:
    """Hyresintäkt efter vacancy."""
    return gross_potential_rent(a) * (1 - a.vacancy_rate)


def opex(a: OperatingAssumptions) -> float:
    """Drift och underhåll, kr/år."""
    return a.area_sqm * (a.operating_cost_per_sqm + a.maintenance_per_sqm)


def noi(a: OperatingAssumptions) -> float:
    """Net Operating Income (driftnetto)."""
    return rental_income(a) - opex(a) - a.property_tax


def direct_capitalisation_value(net_operating_income: float, required_yield: float) -> float:
    """Marknadsvärde med direct capitalisation: NOI / yield-krav."""
    if required_yield <= 0:
        raise ValueError("Yield-kravet måste vara större än 0.")
    return net_operating_income / required_yield
