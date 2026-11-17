"""Explicit unit conversions used at UAV-CAS input boundaries."""

from __future__ import annotations

from math import log10

from .validation import finite_number, positive


def celsius_to_kelvin(value_c: float) -> float:
    value = finite_number(value_c, "temperature_c") + 273.15
    if value <= 0.0:
        raise ValueError("temperature must be above absolute zero")
    return value


def kelvin_to_celsius(value_k: float) -> float:
    value = positive(value_k, "temperature_k")
    return value - 273.15


def pa_to_hpa(value_pa: float) -> float:
    return positive(value_pa, "pressure_pa") / 100.0


def hpa_to_pa(value_hpa: float) -> float:
    return positive(value_hpa, "pressure_hpa") * 100.0


def watts_to_dbm(value_w: float) -> float:
    return 10.0 * log10(positive(value_w, "power_w")) + 30.0


def metres_to_kilometres(value_m: float) -> float:
    return finite_number(value_m, "distance_m") / 1000.0


def kilometres_to_metres(value_km: float) -> float:
    return finite_number(value_km, "distance_km") * 1000.0


def megahertz_to_hertz(value_mhz: float) -> float:
    return positive(value_mhz, "frequency_mhz") * 1.0e6


def gigahertz_to_hertz(value_ghz: float) -> float:
    return positive(value_ghz, "frequency_ghz") * 1.0e9

