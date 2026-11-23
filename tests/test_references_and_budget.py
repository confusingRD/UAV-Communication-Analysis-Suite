import math

import pytest

from uav_cas.link_budget import (
    calculate_reference_link_budget,
    free_space_path_loss_db,
)
from uav_cas.models import LinkConfiguration, LinkDirection, RadioEndpoint, SolverStatus
from uav_cas.propagation.contracts import PropagationRequest
from uav_cas.propagation.eer_reference import EffectiveEarthRadiusReference, derive_effective_earth_k
from uav_cas.propagation.geometric_reference import GeometricLosReference
from uav_cas.propagation.geometry import endpoint_chord_m, two_endpoint_horizon_surface_distance_m


def endpoint(identifier, tx_power, tx_gain, tx_loss, rx_gain, rx_loss, sensitivity):
    return RadioEndpoint(
        identifier, tx_power, tx_gain, tx_loss, rx_gain, rx_loss, sensitivity,
        "declared mode", "test fixture",
    )


def test_geometric_reference_and_k1_agree():
    maximum = two_endpoint_horizon_surface_distance_m(10.0, 100.0)
    request = PropagationRequest("ground", "uav", 10.0, 100.0, maximum)
    geometric = GeometricLosReference().solve(request)
    k1 = EffectiveEarthRadiusReference(1.0).solve(request)
    assert geometric.status is SolverStatus.SOLVED
    assert geometric.maximum_surface_distance_m == pytest.approx(k1.maximum_surface_distance_m)
    assert geometric.endpoint_chord_m == pytest.approx(k1.endpoint_chord_m)
    assert not geometric.physical_ray_path_available


def test_eer_four_thirds_extends_reference_horizon():
    request = PropagationRequest("ground", "uav", 10.0, 100.0, 40_000.0)
    geometric = GeometricLosReference().solve(request)
    eer = EffectiveEarthRadiusReference(4.0 / 3.0).solve(request)
    assert eer.maximum_surface_distance_m > geometric.maximum_surface_distance_m
    assert eer.optical_path_length_m is None


def test_derived_k_domain_and_formula():
    derived = derive_effective_earth_k(
        -39.0e-9, reference_refractive_index=1.0003,
        minimum_height_m=0.0, maximum_height_m=1000.0,
        maximum_relative_gradient_variation=0.05,
    )
    expected = 1.0 / (1.0 + 6_371_000.0 * -39.0e-9 / 1.0003)
    assert derived.k_factor == pytest.approx(expected)
    outside = EffectiveEarthRadiusReference(derived.k_factor, derived=derived).solve(
        PropagationRequest("ground", "uav", 10.0, 1500.0, 1000.0)
    )
    assert outside.status is SolverStatus.UNSUPPORTED_MODEL
    assert outside.is_visible is None


def test_chord_geometry_is_symmetric():
    assert endpoint_chord_m(10.0, 100.0, 5_000.0) == pytest.approx(
        endpoint_chord_m(100.0, 10.0, 5_000.0)
    )


def test_surface_endpoint_and_zero_separation_are_valid():
    result = GeometricLosReference().solve(
        PropagationRequest("surface", "uav", 0.0, 100.0, 0.0)
    )
    assert result.status is SolverStatus.SOLVED
    assert result.endpoint_chord_m == pytest.approx(100.0)


def test_manual_directional_link_budget():
    ground = endpoint("ground", 30.0, 8.0, 2.0, 8.0, 2.0, -100.0)
    uav = endpoint("uav", 20.0, 3.0, 1.0, 3.0, 1.0, -90.0)
    uplink = calculate_reference_link_budget(
        LinkConfiguration(LinkDirection.UPLINK, 2.4e9, ground, uav, 10.0), 1000.0
    )
    downlink = calculate_reference_link_budget(
        LinkConfiguration(LinkDirection.DOWNLINK, 2.4e9, ground, uav, 10.0), 1000.0
    )
    expected_fspl = 20.0 * math.log10(4.0 * math.pi * 1000.0 * 2.4e9 / 299792458.0)
    assert uplink.free_space_path_loss_db == pytest.approx(expected_fspl, abs=1e-12)
    assert uplink.free_space_path_loss_db == pytest.approx(
        free_space_path_loss_db(1000.0, 2.4e9)
    )
    assert uplink.received_power_dbm == pytest.approx(30.0 - 2.0 + 8.0 + 3.0 - 1.0 - expected_fspl)
    assert downlink.received_power_dbm == pytest.approx(20.0 - 1.0 + 3.0 + 8.0 - 2.0 - expected_fspl)
    assert uplink.transmitter_id == "ground" and downlink.transmitter_id == "uav"
    assert uplink.received_power_dbm - downlink.received_power_dbm == pytest.approx(10.0)

