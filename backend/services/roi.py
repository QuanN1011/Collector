"""Proxy financial savings from offsetting potable water with harvested rainwater."""

# water_price is USD per 1,000 gallons (common in utility rate summaries).


def annual_water_savings_usd(rainwater_gallons_annual: float, water_price_per_1000_gal_usd: float) -> float:
    return (rainwater_gallons_annual / 1000.0) * water_price_per_1000_gal_usd
