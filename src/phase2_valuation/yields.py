"""Steg 4: från location score till yield-krav.

Yield = basyield(typ, stad) + lägesjustering(location score)

Lägesjusteringen är en asymmetrisk S-kurva runt ett "normalt" läge:
bättre lägen sänker yielden mot ett golv (prime yield), sämre lägen höjer
den mer, eftersom svaga lägen kan bli svårsålda.
"""

from math import tanh

from src.phase1_location_scoring.models import City, PropertyType

# EXEMPELVÄRDEN för övning, inte aktuella marknadsdata.
# Ersätt med siffror från rådgivningsfirmornas marknadsrapporter.
BASE_YIELDS: dict[PropertyType, dict[City, float]] = {
    PropertyType.OFFICE: {City.MALMO: 0.0525, City.LUND: 0.0550, City.HELSINGBORG: 0.0575},
    PropertyType.RETAIL_LOCAL: {City.MALMO: 0.0575, City.LUND: 0.0600, City.HELSINGBORG: 0.0625},
    PropertyType.RETAIL_EXTERNAL: {City.MALMO: 0.0625, City.LUND: 0.0650, City.HELSINGBORG: 0.0650},
    PropertyType.LOGISTICS: {City.MALMO: 0.0550, City.LUND: 0.0575, City.HELSINGBORG: 0.0550},
    PropertyType.MIXED_USE: {City.MALMO: 0.0575, City.LUND: 0.0600, City.HELSINGBORG: 0.0625},
}

NORMAL_LOCATION_SCORE = 60
CURVE_SOFTNESS = 25
MAX_YIELD_DECREASE = 0.0050  # bästa lägen, i decimalform (0,50 procentenheter)
MAX_YIELD_INCREASE = 0.0100  # sämsta lägen (1,00 procentenhet)


def location_yield_adjustment(location_score: float) -> float:
    """Hur mycket yielden ändras för läget. Negativt = lägre yield = högre värde."""
    t = tanh((location_score - NORMAL_LOCATION_SCORE) / CURVE_SOFTNESS)
    max_change = MAX_YIELD_INCREASE if t < 0 else MAX_YIELD_DECREASE
    return -max_change * t


def required_yield(property_type: PropertyType, city: City, location_score: float) -> float:
    return BASE_YIELDS[property_type][city] + location_yield_adjustment(location_score)


def discount_rate(required_yield_: float, indexation: float) -> float:
    """Total avkastning investeraren kräver: yield plus förväntad tillväxt."""
    return required_yield_ + indexation
