from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class MoneyAssumptions:
    origin_point_id: str
    market_city: str
    trips_per_year: float
    rub_per_hour: float
    capital_cost_rub: float = 0
    annual_operating_cost_rub: float = 0


@dataclass(frozen=True)
class MoneyEffect:
    before_hours: float
    after_hours: float
    hours_saved_per_trip: float
    annual_hours_saved: float
    annual_gross_rub: float
    annual_net_rub: float
    simple_payback_years: float | None
    assumptions: MoneyAssumptions
    method: str = "conditional_time_savings"


def time_savings(before: float, after: float, assumptions: MoneyAssumptions) -> MoneyEffect | None:
    if not isfinite(before) or not isfinite(after):
        return None
    saved = max(0.0, before - after)
    hours = saved * assumptions.trips_per_year
    gross = hours * assumptions.rub_per_hour
    net = gross - assumptions.annual_operating_cost_rub
    payback = (
        assumptions.capital_cost_rub / net if net > 0 and assumptions.capital_cost_rub > 0 else None
    )
    return MoneyEffect(before, after, saved, hours, gross, net, payback, assumptions)
