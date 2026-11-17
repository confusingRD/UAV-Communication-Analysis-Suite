import math

import pytest

from uav_cas.atmosphere.isa import (
    AltitudeKind,
    geometric_to_geopotential,
    geopotential_to_geometric,
    standard_atmosphere,
)


def test_sea_level_reference_values():
    state = standard_atmosphere(0.0)
    assert state.temperature_k == pytest.approx(288.15, abs=0.01)
    assert state.pressure_pa == pytest.approx(101325.0, abs=1.0)
    assert state.density_kg_m3 == pytest.approx(1.2250, abs=1e-4)
    assert state.dynamic_viscosity_pa_s == pytest.approx(1.7894e-5, rel=1e-3)
    assert state.speed_of_sound_m_s == pytest.approx(340.294, abs=0.05)


def test_11_km_geopotential_reference_values():
    state = standard_atmosphere(11_000.0, AltitudeKind.GEOPOTENTIAL)
    assert state.temperature_k == pytest.approx(216.65, abs=0.01)
    assert state.pressure_pa == pytest.approx(22632.1, abs=1.0)
    assert state.density_kg_m3 == pytest.approx(0.36392, abs=1e-4)


def test_isothermal_layer_and_altitude_round_trip():
    at_11 = standard_atmosphere(11_000.0, AltitudeKind.GEOPOTENTIAL)
    at_20 = standard_atmosphere(20_000.0, AltitudeKind.GEOPOTENTIAL)
    assert at_20.temperature_k == pytest.approx(at_11.temperature_k)
    assert at_20.pressure_pa == pytest.approx(5474.9, abs=1.0)
    geometric = 11_000.0
    geopotential = geometric_to_geopotential(geometric)
    assert geopotential < geometric
    assert geopotential_to_geometric(geopotential) == pytest.approx(geometric, abs=1e-9)


@pytest.mark.parametrize("value", [-1.0, math.inf, math.nan, True])
def test_invalid_altitudes(value):
    with pytest.raises(ValueError):
        standard_atmosphere(value)


def test_invalid_altitude_kind_and_range():
    with pytest.raises(ValueError):
        standard_atmosphere(0.0, "AGL")
    with pytest.raises(ValueError):
        standard_atmosphere(20_001.0, AltitudeKind.GEOPOTENTIAL)

