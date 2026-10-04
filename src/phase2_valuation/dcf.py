"""Steg 3: Discounted Cash Flow (DCF).

Marknadsvärde = summan av PV(NOI år 1..n) + PV(exit value)
där exit value = NOI år n+1 / exit yield, och säljs i slutet av år n.

Kassaflöden antas komma i slutet av varje år.
Procentsatser anges som decimaltal: 7,25 % = 0.0725.
"""

from pydantic import BaseModel


class DcfYear(BaseModel):
    year: int
    noi: float
    discount_factor: float
    present_value: float


class DcfResult(BaseModel):
    years: list[DcfYear]
    exit_noi: float
    exit_value: float
    pv_exit_value: float
    market_value: float

    @property
    def exit_share_of_value(self) -> float:
        """Hur stor del av marknadsvärdet som kommer från exit value."""
        return self.pv_exit_value / self.market_value


def discount_factor(rate: float, year: int) -> float:
    """Vad 1 kr om `year` år är värd idag."""
    return 1 / (1 + rate) ** year


def growing_noi(noi_year_1: float, growth_rate: float, years: int) -> list[float]:
    """NOI som växer med en fast takt (t.ex. KPI) varje år."""
    return [noi_year_1 * (1 + growth_rate) ** (year - 1) for year in range(1, years + 1)]


def discounted_cash_flow(
    noi_by_year: list[float],
    exit_noi: float,
    discount_rate: float,
    exit_yield: float,
) -> DcfResult:
    """DCF på en given serie NOI.

    `noi_by_year` är NOI för år 1..n under kalkylperioden.
    `exit_noi` är NOI för år n+1, som köparen betalar för vid exit.
    """
    if not noi_by_year:
        raise ValueError("Kalkylperioden måste vara minst ett år.")
    if discount_rate <= 0 or exit_yield <= 0:
        raise ValueError("Discount rate och exit yield måste vara större än 0.")

    years = [
        DcfYear(
            year=year,
            noi=noi,
            discount_factor=discount_factor(discount_rate, year),
            present_value=noi * discount_factor(discount_rate, year),
        )
        for year, noi in enumerate(noi_by_year, start=1)
    ]
    holding_period = len(noi_by_year)
    exit_value = exit_noi / exit_yield
    pv_exit_value = exit_value * discount_factor(discount_rate, holding_period)

    return DcfResult(
        years=years,
        exit_noi=exit_noi,
        exit_value=exit_value,
        pv_exit_value=pv_exit_value,
        market_value=sum(y.present_value for y in years) + pv_exit_value,
    )
