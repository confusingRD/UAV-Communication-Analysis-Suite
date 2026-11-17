import math

import pytest

from uav_cas.models import (
    AltitudeSpec, GroundStationGeometry, HeightReference, LinkConfiguration,
    LinkDirection, NumericalSettings, RadioEndpoint,
)
from uav_cas.units import (
    celsius_to_kelvin, gigahertz_to_hertz, hpa_to_pa, kelvin_to_celsius,
    pa_to_hpa, watts_to_dbm,
)


def radio(identifier):
    return RadioEndpoint(identifier, 20.0, 2.0, 1.0, 3.0, 1.5, -95.0, "mode", "datasheet")


def test_agl_and_msl_are_explicit():
    agl = AltitudeSpec(120.0, HeightReference.AGL, ground_elevation_msl_m=35.0)
    msl = AltitudeSpec(155.0, HeightReference.MSL)
    assert agl.msl_m == pytest.approx(msl.msl_m)
    ground = GroundStationGeometry("station", 35.0, 10.0)
    assert ground.antenna_altitude_msl_m == 45.0
    with pytest.raises(ValueError):
        AltitudeSpec(120.0, HeightReference.AGL)


def test_units_and_invalid_values():
    assert watts_to_dbm(1.0) == pytest.approx(30.0)
    assert gigahertz_to_hertz(2.4) == pytest.approx(2.4e9)
    assert hpa_to_pa(pa_to_hpa(101325.0)) == pytest.approx(101325.0)
    assert kelvin_to_celsius(celsius_to_kelvin(20.0)) == pytest.approx(20.0)
    for value in (0.0, -1.0, math.nan, math.inf, True):
        with pytest.raises(ValueError):
            watts_to_dbm(value)


def test_directional_contract_and_numerical_settings():
    ground = radio("ground")
    uav = radio("uav")
    uplink = LinkConfiguration(LinkDirection.UPLINK, 2.4e9, ground, uav)
    downlink = LinkConfiguration(LinkDirection.DOWNLINK, 2.4e9, ground, uav)
    assert uplink.transmitter is ground and uplink.receiver is uav
    assert downlink.transmitter is uav and downlink.receiver is ground
    assert NumericalSettings().maximum_iterations == 100
    with pytest.raises(ValueError):
        NumericalSettings(maximum_iterations=True)

