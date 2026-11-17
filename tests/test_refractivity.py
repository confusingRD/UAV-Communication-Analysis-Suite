import pytest

from uav_cas.atmosphere.humidity import humidity_from_relative_humidity
from uav_cas.atmosphere.refractivity import (
    radio_refractivity,
    refractivity_from_relative_humidity,
)


def test_dry_refractivity_manual_value():
    result = radio_refractivity(288.15, 101325.0)
    expected = 77.6 * 1013.25 / 288.15
    assert result.radio_refractivity_n_units == pytest.approx(expected, abs=1e-12)
    assert result.refractive_index == pytest.approx(1.0 + expected * 1e-6, abs=1e-15)
    assert result.wet_component_n_units == 0.0


def test_humid_refractivity_manual_components():
    result = radio_refractivity(
        293.15, 100000.0, vapour_pressure_hpa=10.0,
        humidity_basis="specified local vapour pressure",
    )
    dry = 77.6 * 990.0 / 293.15
    wet = 72.0 * 10.0 / 293.15 + 3.75e5 * 10.0 / 293.15**2
    assert result.dry_component_n_units == pytest.approx(dry)
    assert result.wet_component_n_units == pytest.approx(wet)
    assert result.radio_refractivity_n_units == pytest.approx(dry + wet)


def test_relative_humidity_is_only_a_local_state():
    result, humidity = refractivity_from_relative_humidity(293.15, 101325.0, 0.5)
    assert humidity.vapour_pressure_hpa == pytest.approx(
        0.5 * humidity.saturation_vapour_pressure_hpa
    )
    assert result.wet_component_n_units > 0.0
    assert "local" in result.humidity_basis


def test_humidity_domain_and_invalid_pressures():
    with pytest.raises(ValueError):
        humidity_from_relative_humidity(263.15, 101325.0, 0.5)
    with pytest.raises(ValueError):
        humidity_from_relative_humidity(293.15, 101325.0, 1.01)
    with pytest.raises(ValueError):
        radio_refractivity(293.15, 1000.0, vapour_pressure_hpa=10.0)

