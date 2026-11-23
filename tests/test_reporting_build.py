from dataclasses import replace

import pytest
from matplotlib.collections import PolyCollection

from uav_cas.atmosphere.itu_p835 import low_latitude_reference_atmosphere
from uav_cas.atmosphere.profiles import RefractivityProfile
from uav_cas.reporting import (
    AtmosphereModel,
    MaximumConnectionResult,
    ReportingInputs,
    SweepPoint,
    analyze_reporting_case,
    dashboard_state,
    estimate_maximum_connection,
)
from uav_cas.visualization.reporting import (
    atmosphere_profile_figure,
    communication_performance_figure,
    maximum_connection_region_figure,
    ray_cross_section_figure,
)


def test_p835_low_latitude_surface_reference_and_profile_provenance() -> None:
    state = low_latitude_reference_atmosphere(0.0)
    assert state.temperature_k == pytest.approx(300.4222, abs=1.0e-10)
    assert state.pressure_pa == pytest.approx(101_203.06, abs=1.0e-8)
    assert state.water_vapour_density_g_m3 == pytest.approx(19.6542, abs=1.0e-10)
    assert state.vapour_pressure_pa == pytest.approx(
        19.6542 * 300.4222 / 216.7 * 100.0, rel=1.0e-12
    )
    profile = RefractivityProfile.from_itu_p835_low_latitude(0.0, 1_000.0, 100.0)
    assert "P.835-7" in profile.source
    assert "P.453-14" in profile.source
    assert profile.refractive_indices[0] > profile.refractive_indices[-1]
    assert len(profile.thermodynamic_states) == 11


def test_reporting_default_is_itu_and_isa_remains_optional() -> None:
    inputs = ReportingInputs(surface_distance_km=20.0)
    itu = analyze_reporting_case(inputs)
    isa = analyze_reporting_case(replace(inputs, atmosphere_model=AtmosphereModel.ISA))
    assert inputs.atmosphere_model is AtmosphereModel.ITU
    assert "P.835-7" in itu.profile.source
    assert "ISA-1976" in isa.profile.source
    assert itu.atmosphere.temperature_k != pytest.approx(isa.atmosphere.temperature_k)
    assert itu.ray_outputs.solver_status == "solved"
    assert itu.ray_outputs.ray_branch == "radial_monotonic"
    assert itu.ray_outputs.minimum_clearance_m == pytest.approx(10.0, abs=1.0e-6)


def test_visibility_and_communication_feasibility_are_separate() -> None:
    result = analyze_reporting_case(ReportingInputs(surface_distance_km=50.0))
    assert result.ray_outputs.geometric_visibility is True
    assert result.ray_outputs.ray_visibility is True
    assert result.link_outputs.communication_feasible is False
    assert result.link_outputs.link_margin_db < 0.0
    assert result.link_outputs.received_power_dbm is not None
    assert result.link_outputs.total_losses_db == pytest.approx(
        result.link_outputs.free_space_path_loss_db + 2.0
    )


def test_dashboard_state_keeps_available_unavailable_and_unresolved_distinct() -> None:
    available = dashboard_state(
        analyze_reporting_case(ReportingInputs(surface_distance_km=20.0))
    )
    power_limited = dashboard_state(
        analyze_reporting_case(ReportingInputs(surface_distance_km=50.0))
    )
    blocked = dashboard_state(
        analyze_reporting_case(
            ReportingInputs(surface_distance_km=200.0, transmit_power_dbm=200.0)
        )
    )
    unresolved = dashboard_state(
        analyze_reporting_case(ReportingInputs(surface_distance_km=2_300.0))
    )
    assert available.status_label == "LINK AVAILABLE"
    assert power_limited.status_label == "LINK UNAVAILABLE"
    assert power_limited.ray_visibility_label == "Clear"
    assert blocked.status_label == "LINK UNAVAILABLE"
    assert blocked.ray_visibility_label in {"Blocked", "Grazing"}
    assert unresolved.status_label == "LINK STATUS UNRESOLVED"
    assert unresolved.status_kind == "unresolved"


def test_maximum_connection_reports_power_and_ray_limits() -> None:
    power_limited = estimate_maximum_connection(
        ReportingInputs(sweep_max_km=200.0, sweep_step_km=10.0)
    )
    assert power_limited.maximum_surface_distance_km == pytest.approx(39.375, abs=0.3)
    assert power_limited.limiting_condition == "insufficient link margin"

    ray_limited = estimate_maximum_connection(
        ReportingInputs(
            transmit_power_dbm=200.0,
            sweep_max_km=300.0,
            sweep_step_km=10.0,
        )
    )
    assert ray_limited.maximum_surface_distance_km is not None
    assert ray_limited.limiting_condition == "blocked ray"
    assert ray_limited.maximum_surface_distance_km < 300.0


def test_reporting_figures_build_for_calculated_results() -> None:
    result = analyze_reporting_case(ReportingInputs(surface_distance_km=50.0))
    maximum = estimate_maximum_connection(
        ReportingInputs(sweep_max_km=100.0, sweep_step_km=10.0)
    )
    figures = (
        atmosphere_profile_figure(result.profile),
        communication_performance_figure(
            maximum.points,
            requested_distance_km=result.inputs.surface_distance_km,
            maximum=maximum,
            requested_result=result,
        ),
        ray_cross_section_figure(result),
        maximum_connection_region_figure(((1_000.0, maximum),)),
    )
    try:
        assert all(figure.axes for figure in figures)
        infeasible_samples = next(
            collection
            for collection in figures[1].axes[0].collections
            if collection.get_label() == "Insufficient-margin sample"
        )
        assert 50.0 in {float(point[0]) for point in infeasible_samples.get_offsets()}
    finally:
        for figure in figures:
            figure.clear()


def test_performance_plot_does_not_fabricate_unresolved_margin() -> None:
    points = (
        SweepPoint(0.0, "solved", True, 8.0, True),
        SweepPoint(10.0, "numerical_failure", None, None, False),
        SweepPoint(20.0, "solved", True, -4.0, False),
    )
    maximum = MaximumConnectionResult(
        0.0,
        "unresolved ray status",
        "endpoint_residual",
        1.0,
        points,
    )
    figure = communication_performance_figure(
        points,
        requested_distance_km=10.0,
        maximum=maximum,
    )
    try:
        computed_lines = [
            line for line in figure.axes[0].lines if line.get_color() == "#5f6b73"
        ]
        plotted_distances = {
            float(value) for line in computed_lines for value in line.get_xdata()
        }
        assert plotted_distances == {0.0, 20.0}
        assert 10.0 not in plotted_distances
        assert any(
            collection.get_label() == "Ray status only; margin unavailable"
            for collection in figure.axes[0].collections
        )
    finally:
        figure.clear()


def test_coverage_region_leaves_unresolved_altitude_gap_unfilled() -> None:
    resolved = MaximumConnectionResult(
        40.0,
        "insufficient link margin",
        "clear direct ray but insufficient link margin",
        0.1,
        (),
    )
    unresolved = MaximumConnectionResult(
        39.0,
        "unresolved ray status",
        "quadrature_limit",
        0.1,
        (),
    )
    figure = maximum_connection_region_figure(
        (
            (100.0, resolved),
            (200.0, resolved),
            (300.0, unresolved),
            (400.0, resolved),
            (500.0, resolved),
        )
    )
    try:
        filled_regions = [
            collection
            for collection in figure.axes[0].collections
            if isinstance(collection, PolyCollection)
        ]
        assert len(filled_regions) == 2
        assert any(
            collection.get_label() == "Unresolved ray status"
            for collection in figure.axes[0].collections
        )
    finally:
        figure.clear()
