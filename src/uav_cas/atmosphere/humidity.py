"""Local humidity helpers; no vertical humidity profile is inferred."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp

from uav_cas.units import pa_to_hpa
from uav_cas.validation import finite_number, positive

MIN_LIQUID_WATER_TEMPERATURE_C = 0.0
MAX_LIQUID_WATER_TEMPERATURE_C = 50.0


@dataclass(frozen=True)
class HumidityState:
    relative_humidity_fraction: float
    saturation_vapour_pressure_hpa: float
    vapour_pressure_hpa: float
    convention: str = "ITU-R P.453-14 Annex 1 liquid-water saturation expression"


def saturation_vapour_pressure_hpa(temperature_k: float, total_pressure_pa: float) -> float:
    """P.453-14 Annex 1 saturation pressure over liquid water.

    UAV-CAS conservatively exposes this branch only from 0 to 50 degrees C.
    Ice/supercooled-water conventions are not silently substituted.
    """

    temperature = positive(temperature_k, "temperature_k")
    pressure_hpa = pa_to_hpa(total_pressure_pa)
    temperature_c = temperature - 273.15
    if not MIN_LIQUID_WATER_TEMPERATURE_C <= temperature_c <= MAX_LIQUID_WATER_TEMPERATURE_C:
        raise ValueError("liquid-water humidity conversion is supported only from 0 to 50 deg C")
    enhancement = 1.0 + 1.0e-4 * (
        7.2 + pressure_hpa * (0.00320 + 5.9e-7 * temperature_c**2)
    )
    return enhancement * 6.1121 * exp(
        (18.678 - temperature_c / 234.5) * temperature_c / (temperature_c + 257.14)
    )


def humidity_from_relative_humidity(
    temperature_k: float,
    total_pressure_pa: float,
    relative_humidity_fraction: float,
) -> HumidityState:
    rh = finite_number(relative_humidity_fraction, "relative_humidity_fraction")
    if not 0.0 <= rh <= 1.0:
        raise ValueError("relative humidity must be a fraction in [0, 1]")
    saturation = saturation_vapour_pressure_hpa(temperature_k, total_pressure_pa)
    vapour = rh * saturation
    if vapour >= pa_to_hpa(total_pressure_pa):
        raise ValueError("vapour pressure must be lower than total pressure")
    return HumidityState(rh, saturation, vapour)

