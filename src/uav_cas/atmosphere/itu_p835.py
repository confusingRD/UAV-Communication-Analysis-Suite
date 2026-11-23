"""ITU-R P.835-7 low-latitude reference atmosphere.

The reporting build uses the annual low-latitude reference expressions over
0--20 km geometric height.  These climatological reference profiles are not
local weather observations.  Pressure is returned as total pressure; moist
air density is calculated from dry-air and water-vapour partial pressures.
"""

from __future__ import annotations

from math import exp, sqrt

from uav_cas.validation import finite_number

from .isa import (
    AltitudeKind,
    AtmosphereState,
    GAMMA_DRY_AIR,
    R_DRY_AIR_J_KG_K,
    SUTHERLAND_BETA_KG_M_S_SQRT_K,
    SUTHERLAND_S_K,
    geometric_to_geopotential,
)

MAX_GEOMETRIC_HEIGHT_M = 20_000.0
R_WATER_VAPOUR_J_KG_K = 461.5


def low_latitude_reference_atmosphere(
    altitude_m: float,
    kind: AltitudeKind | str = AltitudeKind.GEOMETRIC,
) -> AtmosphereState:
    """Return the P.835-7 annual low-latitude reference state.

    P.835 supplies temperature in kelvin, total pressure in hPa, and water
    vapour density in g/m3 as functions of geometric height in kilometres.
    The reporting build intentionally restricts this implementation to
    geometric MSL heights from 0 through 20 km.
    """

    try:
        altitude_kind = AltitudeKind(kind)
    except (TypeError, ValueError) as exc:
        raise ValueError("P.835 reporting profile requires geometric MSL height") from exc
    if altitude_kind is not AltitudeKind.GEOMETRIC:
        raise ValueError("P.835 reporting profile accepts geometric MSL height only")
    height_m = finite_number(altitude_m, "altitude_m")
    if not 0.0 <= height_m <= MAX_GEOMETRIC_HEIGHT_M:
        raise ValueError("P.835 low-latitude reporting profile is limited to 0--20 km")
    height_km = height_m / 1_000.0

    if height_km < 17.0:
        temperature_k = (
            300.4222 - 6.3533 * height_km + 0.005886 * height_km**2
        )
    else:
        temperature_k = 194.0 + 2.533 * (height_km - 17.0)

    if height_km <= 10.0:
        pressure_hpa = (
            1012.0306 - 109.0338 * height_km + 3.6316 * height_km**2
        )
    else:
        pressure_at_10_hpa = 1012.0306 - 109.0338 * 10.0 + 3.6316 * 10.0**2
        pressure_hpa = pressure_at_10_hpa * exp(-0.147 * (height_km - 10.0))

    water_vapour_density_g_m3 = 19.6542 * exp(
        -0.2313 * height_km
        - 0.1122 * height_km**2
        + 0.01351 * height_km**3
        - 0.0005923 * height_km**4
    )
    vapour_pressure_hpa = water_vapour_density_g_m3 * temperature_k / 216.7
    vapour_pressure_pa = vapour_pressure_hpa * 100.0
    pressure_pa = pressure_hpa * 100.0
    dry_pressure_pa = pressure_pa - vapour_pressure_pa
    if dry_pressure_pa <= 0.0:
        raise ValueError("P.835 state produced nonpositive dry-air pressure")

    density_kg_m3 = (
        dry_pressure_pa / (R_DRY_AIR_J_KG_K * temperature_k)
        + vapour_pressure_pa / (R_WATER_VAPOUR_J_KG_K * temperature_k)
    )
    dynamic_viscosity_pa_s = (
        SUTHERLAND_BETA_KG_M_S_SQRT_K
        * temperature_k**1.5
        / (temperature_k + SUTHERLAND_S_K)
    )
    speed_of_sound_m_s = sqrt(GAMMA_DRY_AIR * R_DRY_AIR_J_KG_K * temperature_k)
    return AtmosphereState(
        geometric_altitude_m=height_m,
        geopotential_altitude_m=geometric_to_geopotential(height_m),
        temperature_k=temperature_k,
        pressure_pa=pressure_pa,
        density_kg_m3=density_kg_m3,
        dynamic_viscosity_pa_s=dynamic_viscosity_pa_s,
        speed_of_sound_m_s=speed_of_sound_m_s,
        water_vapour_density_g_m3=water_vapour_density_g_m3,
        vapour_pressure_pa=vapour_pressure_pa,
        model="ITU-R P.835-7 annual low-latitude reference atmosphere",
        model_version="ITU-R P.835-7 low-latitude equations; UAV-CAS 0--20 km subset",
        humidity_basis="P.835-7 low-latitude reference water-vapour-density profile",
    )
