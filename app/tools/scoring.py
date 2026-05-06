"""Neighborhood scoring + rental yield estimation. Wire as supplementary tool."""


def neighborhood_score(metrics: dict) -> int:
    return 0


def rental_yield_estimate(price: float, monthly_rent: float, charges_monthly: float = 0.0) -> float:
    if price <= 0:
        return 0.0
    annual_net = (monthly_rent - charges_monthly) * 12
    return round(annual_net / price * 100, 2)
