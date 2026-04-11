"""Rainwater capture potential (DOE rainwater harvesting calculator form)."""

# gallons = roof_area_sqft * rainfall_inches * 0.623
RAINFALL_COEFFICIENT = 0.623


def annual_rainwater_gallons(roof_area_sqft: float, rainfall_inches_annual: float) -> float:
    return roof_area_sqft * rainfall_inches_annual * RAINFALL_COEFFICIENT
