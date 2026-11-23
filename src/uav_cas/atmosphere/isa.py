"""1976 U.S. Standard Atmosphere compatible lower-atmosphere equations.

The implementation covers geopotential altitude 0--20 km: the tropospheric
lapse layer through 11 km and the isothermal layer through 20 km.  Geometric
MSL height is converted with the standard-atmosphere effective radius, not the
radio-geometry Earth radius.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import exp, sqrt

from uav_cas.validation import finite_number

T0_K = 288.15
P0_PA = 101_325.0
G0_M_S2 = 9.80665
R_DRY_AIR_J_KG_K = 287.05287
GAMMA_DRY_AIR = 1.4
TROPOSPHERIC_LAPSE_K_M = 0.0065
TROPOPAUSE_GEOPOTENTIAL_M = 11_000.0
MAX_GEOPOTENTIAL_M = 20_000.0
ATMOSPHERE_EFFECTIVE_RADIUS_M = 6_356_766.0
SUTHERLAND_BETA_KG_M_S_SQRT_K = 1.458e-6
SUTHERLAND_S_K = 110.4


class AltitudeKind(str, Enum):
    GEOMETRIC = "geometric_msl"
    GEOPOTENTIAL = "geopotential"


@dataclass(frozen=True)
class AtmosphereState:
    geometric_altitude_m: float
    geopotential_altitude_m: float
    temperature_k: float
    pressure_pa: float
    density_kg_m3: float
    dynamic_viscosity_pa_s: float
    speed_of_sound_m_s: float
    water_vapour_density_g_m3: float = 0.0
    vapour_pressure_pa: float = 0.0
    model: str = "U.S. Standard Atmosphere 1976 lower atmosphere"
    model_version: str = "UAV-CAS ISA-1976-v1"
    humidity_basis: str = "dry air"

    @property
    def temperature_c(self) -> float:
        return self.temperature_k - 273.15


def geometric_to_geopotential(geometric_altitude_m: float) -> float:
    z = finite_number(geometric_altitude_m, "geometric_altitude_m")
    if z < 0.0:
        raise ValueError("geometric altitude must be at or above MSL")
    return ATMOSPHERE_EFFECTIVE_RADIUS_M * z / (ATMOSPHERE_EFFECTIVE_RADIUS_M + z)


def geopotential_to_geometric(geopotential_altitude_m: float) -> float:
    h = finite_number(geopotential_altitude_m, "geopotential_altitude_m")
    if h < 0.0 or h >= ATMOSPHERE_EFFECTIVE_RADIUS_M:
        raise ValueError("geopotential altitude is outside the conversion domain")
    return ATMOSPHERE_EFFECTIVE_RADIUS_M * h / (ATMOSPHERE_EFFECTIVE_RADIUS_M - h)


def _validated_altitudes(altitude_m: float, kind: AltitudeKind | str) -> tuple[float, float]:
    try:
        altitude_kind = AltitudeKind(kind)
    except (TypeError, ValueError) as exc:
        raise ValueError("altitude kind must be 'geometric_msl' or 'geopotential'") from exc
    altitude = finite_number(altitude_m, "altitude_m")
    if altitude < 0.0:
        raise ValueError("altitude must be at or above MSL")
    if altitude_kind is AltitudeKind.GEOMETRIC:
        z = altitude
        h = geometric_to_geopotential(z)
    else:
        h = altitude
        z = geopotential_to_geometric(h)
    if h > MAX_GEOPOTENTIAL_M:
        raise ValueError("ISA lower-atmosphere model is valid only through 20 km geopotential altitude")
    return z, h


def standard_atmosphere(
    altitude_m: float,
    kind: AltitudeKind | str = AltitudeKind.GEOMETRIC,
) -> AtmosphereState:
    """Return a dry-air state for a geometric or geopotential altitude.

    Pressure and density are layer-continuous. Dynamic viscosity uses
    Sutherland's law and sound speed uses the dry ideal-gas approximation.
    """

    z, h = _validated_altitudes(altitude_m, kind)
    exponent = G0_M_S2 / (R_DRY_AIR_J_KG_K * TROPOSPHERIC_LAPSE_K_M)
    if h <= TROPOPAUSE_GEOPOTENTIAL_M:
        temperature = T0_K - TROPOSPHERIC_LAPSE_K_M * h
        pressure = P0_PA * (temperature / T0_K) ** exponent
    else:
        temperature = T0_K - TROPOSPHERIC_LAPSE_K_M * TROPOPAUSE_GEOPOTENTIAL_M
        p11 = P0_PA * (temperature / T0_K) ** exponent
        pressure = p11 * exp(
            -G0_M_S2 * (h - TROPOPAUSE_GEOPOTENTIAL_M)
            / (R_DRY_AIR_J_KG_K * temperature)
        )
    density = pressure / (R_DRY_AIR_J_KG_K * temperature)
    viscosity = (
        SUTHERLAND_BETA_KG_M_S_SQRT_K
        * temperature ** 1.5
        / (temperature + SUTHERLAND_S_K)
    )
    sound_speed = sqrt(GAMMA_DRY_AIR * R_DRY_AIR_J_KG_K * temperature)
    return AtmosphereState(
        geometric_altitude_m=z,
        geopotential_altitude_m=h,
        temperature_k=temperature,
        pressure_pa=pressure,
        density_kg_m3=density,
        dynamic_viscosity_pa_s=viscosity,
        speed_of_sound_m_s=sound_speed,
    )

