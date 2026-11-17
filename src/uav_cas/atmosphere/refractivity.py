"""ITU-R P.453-14 radio refractivity for a specified local state."""

from __future__ import annotations

from dataclasses import dataclass

from uav_cas.units import pa_to_hpa
from uav_cas.validation import finite_number, positive

from .humidity import HumidityState, humidity_from_relative_humidity


@dataclass(frozen=True)
class RefractivityResult:
    radio_refractivity_n_units: float
    refractive_index: float
    dry_component_n_units: float
    wet_component_n_units: float
    vapour_pressure_hpa: float
    humidity_basis: str
    source: str = "ITU-R P.453-14 (2019), radio refractive index formula"
    model_version: str = "P.453-14 coefficients: 77.6, 72, 3.75e5"
    assumptions: tuple[str, ...] = ()


def radio_refractivity(
    temperature_k: float,
    total_pressure_pa: float,
    *,
    vapour_pressure_hpa: float = 0.0,
    humidity_basis: str = "dry-air reference (e=0, not a measurement)",
) -> RefractivityResult:
    temperature = positive(temperature_k, "temperature_k")
    pressure_hpa = pa_to_hpa(total_pressure_pa)
    vapour = finite_number(vapour_pressure_hpa, "vapour_pressure_hpa")
    if vapour < 0.0 or vapour >= pressure_hpa:
        raise ValueError("vapour pressure must satisfy 0 <= e < total pressure")
    if not isinstance(humidity_basis, str) or not humidity_basis.strip():
        raise ValueError("humidity_basis is required")
    dry_pressure = pressure_hpa - vapour
    dry = 77.6 * dry_pressure / temperature
    wet = 72.0 * vapour / temperature + 3.75e5 * vapour / temperature**2
    refractivity = dry + wet
    assumptions = (
        "Pressures converted from Pa to hPa at the P.453 boundary",
        "N is dimensionless by convention and expressed in N-units",
    )
    return RefractivityResult(
        radio_refractivity_n_units=refractivity,
        refractive_index=1.0 + refractivity * 1.0e-6,
        dry_component_n_units=dry,
        wet_component_n_units=wet,
        vapour_pressure_hpa=vapour,
        humidity_basis=humidity_basis.strip(),
        assumptions=assumptions,
    )


def refractivity_from_relative_humidity(
    temperature_k: float,
    total_pressure_pa: float,
    relative_humidity_fraction: float,
) -> tuple[RefractivityResult, HumidityState]:
    """Calculate one local humid state; never construct a vertical profile."""

    humidity = humidity_from_relative_humidity(
        temperature_k, total_pressure_pa, relative_humidity_fraction
    )
    result = radio_refractivity(
        temperature_k,
        total_pressure_pa,
        vapour_pressure_hpa=humidity.vapour_pressure_hpa,
        humidity_basis="local measured/specified RH using P.453 liquid-water saturation",
    )
    return result, humidity

