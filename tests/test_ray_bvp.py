"""Phase 2A numerical verification of the additive spherical ray BVP."""

from __future__ import annotations

from bisect import bisect_right
from math import acos, ceil, cos, sin, sqrt

import pytest

from uav_cas.atmosphere.profiles import RefractivityProfile
from uav_cas.propagation import (
    RayBranch,
    RaySolverSettings,
    RaySolveStatus,
    trace_spherical_between,
)
from uav_cas.propagation import PropagationRequest, trace_uav_path


R = 6_371_000.0
FREQUENCY = 2.4e9


def _endpoint(height_m: float, surface_distance_m: float) -> tuple[float, float, float]:
    angle = surface_distance_m / R
    radius = R + height_m
    return (radius * cos(angle), radius * sin(angle), 0.0)


def _constant_profile(
    index: float = 1.0,
    minimum_m: float = 0.0,
) -> RefractivityProfile:
    return RefractivityProfile.from_samples(
        (minimum_m, 5_000.0),
        (index, index),
        source=f"constant n={index}",
        model_version="test constant-index profile",
        humidity_basis="specified constant refractive index",
    )


def _trace(
    source_height_m: float,
    receiver_height_m: float,
    surface_distance_m: float,
    profile: RefractivityProfile | None = None,
    settings: RaySolverSettings = RaySolverSettings(),
):
    return trace_spherical_between(
        (R + source_height_m, 0.0, 0.0),
        _endpoint(receiver_height_m, surface_distance_m),
        FREQUENCY,
        profile or _constant_profile(),
        R,
        R,
        settings,
    )


def _independent_fermat_endpoint(
    profile: RefractivityProfile,
    source: tuple[float, float, float],
    tangent: tuple[float, float, float],
    path_length_m: float,
    maximum_step_m: float,
) -> tuple[float, float, float, float, float]:
    """Independent Cartesian RK4, not the production invariant integrals."""

    heights = profile.geometric_heights_m
    indices = profile.refractive_indices

    def rhs(values: tuple[float, float, float, float, float]):
        x, y, ux, uy, optical_excess = values
        radius = sqrt(x * x + y * y)
        height = radius - R
        interval = max(0, min(len(heights) - 2, bisect_right(heights, height) - 1))
        slope = (indices[interval + 1] - indices[interval]) / (
            heights[interval + 1] - heights[interval]
        )
        n_value = indices[interval] + slope * (height - heights[interval])
        gradient_x = slope * x / radius
        gradient_y = slope * y / radius
        projection = ux * gradient_x + uy * gradient_y
        return (
            ux,
            uy,
            (gradient_x - ux * projection) / n_value,
            (gradient_y - uy * projection) / n_value,
            n_value - 1.0,
        )

    def advance(values, derivative, scale):
        return tuple(value + scale * delta for value, delta in zip(values, derivative))

    step_count = ceil(path_length_m / maximum_step_m)
    step = path_length_m / step_count
    values = (source[0], source[1], tangent[0], tangent[1], 0.0)
    for _ in range(step_count):
        first = rhs(values)
        second = rhs(advance(values, first, step / 2.0))
        third = rhs(advance(values, second, step / 2.0))
        fourth = rhs(advance(values, third, step))
        values = tuple(
            value
            + step * (a + 2.0 * b + 2.0 * c + d) / 6.0
            for value, a, b, c, d in zip(values, first, second, third, fourth)
        )
    return values


def test_constant_index_recovers_exact_straight_chord_and_optical_length() -> None:
    index = 1.0003
    result = _trace(10.0, 1_000.0, 50_000.0, _constant_profile(index))
    assert result.status is RaySolveStatus.SOLVED
    assert result.diagnostics.branch is RayBranch.RADIAL_MONOTONIC
    assert result.geometric_length_m == pytest.approx(result.endpoint_chord_m, abs=2.0e-4)
    assert result.refractivity_excess_m == pytest.approx(
        (index - 1.0) * result.endpoint_chord_m, abs=2.0e-6
    )
    assert result.optical_path_length_m == pytest.approx(
        index * result.endpoint_chord_m, abs=2.0e-4
    )
    assert abs(result.diagnostics.angular_endpoint_residual_rad) < 1.0e-10
    assert result.diagnostics.cartesian_endpoint_error_m < 0.1


def test_equal_height_single_minimum_matches_spherical_straight_geometry() -> None:
    height = 1_000.0
    distance = 50_000.0
    result = _trace(height, height, distance)
    angle = distance / R
    expected_minimum_radius = (R + height) * cos(angle / 2.0)
    assert result.status is RaySolveStatus.SOLVED
    assert result.diagnostics.branch is RayBranch.SINGLE_MINIMUM
    assert result.geometric_length_m == pytest.approx(result.endpoint_chord_m, abs=2.0e-4)
    assert result.diagnostics.minimum_clearance_m == pytest.approx(
        expected_minimum_radius - R, abs=2.0e-4
    )
    assert result.path.source_elevation_deg < 0.0
    assert result.path.receiver_incident_elevation_deg > 0.0


def test_reversed_configuration_is_reciprocal_for_static_scalar_index() -> None:
    profile = RefractivityProfile.from_dry_isa(0.0, 5_000.0, 25.0)
    forward = _trace(10.0, 1_000.0, 50_000.0, profile)
    reverse = trace_spherical_between(
        _endpoint(1_000.0, 50_000.0),
        (R + 10.0, 0.0, 0.0),
        FREQUENCY,
        profile,
        R,
        R,
    )
    assert forward.status is reverse.status is RaySolveStatus.SOLVED
    assert forward.geometric_length_m == pytest.approx(reverse.geometric_length_m, abs=1.0e-7)
    assert forward.optical_path_length_m == pytest.approx(reverse.optical_path_length_m, abs=1.0e-7)
    assert forward.invariant_b_m == pytest.approx(reverse.invariant_b_m, rel=2.0e-12)
    assert reverse.path.source_elevation_deg < 0.0
    assert forward.path.receiver_look_elevation_deg < 0.0
    for reverse_launch, forward_incident in zip(
        reverse.path.source_tangent, forward.path.receiver_incident_tangent
    ):
        assert reverse_launch == pytest.approx(-forward_incident, abs=2.0e-9)


def test_dry_profile_matches_independent_cartesian_fermat_integration() -> None:
    profile = RefractivityProfile.from_dry_isa(0.0, 5_000.0, 25.0)
    result = _trace(10.0, 1_000.0, 50_000.0, profile)
    assert result.status is RaySolveStatus.SOLVED
    coarse = _independent_fermat_endpoint(
        profile,
        result.source_position_m,
        result.path.source_tangent,
        result.geometric_length_m,
        20.0,
    )
    fine = _independent_fermat_endpoint(
        profile,
        result.source_position_m,
        result.path.source_tangent,
        result.geometric_length_m,
        10.0,
    )
    coarse_fine = sqrt(sum((a - b) ** 2 for a, b in zip(coarse[:2], fine[:2])))
    endpoint_error = sqrt(
        sum((actual - target) ** 2 for actual, target in zip(fine[:2], result.receiver_position_m[:2]))
    )
    assert coarse_fine < 0.02
    assert endpoint_error < 0.05
    assert fine[4] == pytest.approx(result.refractivity_excess_m, abs=2.0e-4)
    assert result.diagnostics.invariant_max_relative_error < 5.0e-9


def test_profile_and_path_sampling_refinement_converge_separately() -> None:
    request = PropagationRequest("ground", "uav", 10.0, 1_000.0, 100_000.0)
    launch_angles = []
    for spacing in (200.0, 100.0, 50.0, 25.0):
        result = trace_uav_path(
            request,
            RefractivityProfile.from_dry_isa(0.0, 5_000.0, spacing),
        )
        assert result.status is RaySolveStatus.SOLVED
        launch_angles.append(result.path.source_elevation_deg)
    differences = [
        abs(after - before) for before, after in zip(launch_angles, launch_angles[1:])
    ]
    assert differences[2] < differences[1] < differences[0]

    profile = RefractivityProfile.from_dry_isa(0.0, 5_000.0, 25.0)
    sampling_errors = []
    for count in (21, 51, 101, 201):
        result = _trace(
            1_000.0,
            1_000.0,
            100_000.0,
            profile,
            RaySolverSettings(path_sample_count=count),
        )
        sampling_errors.append(result.diagnostics.invariant_max_relative_error)
    assert all(after < before for before, after in zip(sampling_errors, sampling_errors[1:]))

    loose = RaySolverSettings(
        angular_tolerance_rad=1.0e-8,
        quadrature_angle_tolerance_rad=1.0e-9,
        quadrature_length_tolerance_m=1.0e-3,
        quadrature_refractivity_tolerance_m=1.0e-5,
        path_sample_count=101,
    )
    tight = RaySolverSettings(
        angular_tolerance_rad=1.0e-11,
        quadrature_angle_tolerance_rad=5.0e-13,
        quadrature_length_tolerance_m=5.0e-6,
        quadrature_refractivity_tolerance_m=5.0e-9,
        path_sample_count=101,
    )
    loose_result = _trace(10.0, 1_000.0, 130_000.0, profile, loose)
    default_result = _trace(
        10.0, 1_000.0, 130_000.0, profile, RaySolverSettings(path_sample_count=101)
    )
    tight_result = _trace(10.0, 1_000.0, 130_000.0, profile, tight)
    assert abs(default_result.geometric_length_m - tight_result.geometric_length_m) < abs(
        loose_result.geometric_length_m - default_result.geometric_length_m
    )
    assert abs(default_result.refractivity_excess_m - tight_result.refractivity_excess_m) < abs(
        loose_result.refractivity_excess_m - default_result.refractivity_excess_m
    )


def test_radial_limit_and_bounded_profile_are_explicit() -> None:
    radial = trace_spherical_between(
        (R + 10.0, 0.0, 0.0),
        (R + 1_000.0, 0.0, 0.0),
        FREQUENCY,
        _constant_profile(1.0003),
        R,
        R,
    )
    assert radial.status is RaySolveStatus.SOLVED
    assert radial.diagnostics.branch is RayBranch.RADIAL
    assert radial.geometric_length_m == pytest.approx(990.0, abs=1.0e-8)
    assert radial.refractivity_excess_m == pytest.approx(0.297, abs=1.0e-8)

    missing = _trace(10.0, 6_000.0, 10_000.0)
    assert missing.status is RaySolveStatus.MISSING_DATA
    assert missing.reason_code == "endpoint_outside_profile"


def test_ground_grazing_and_ground_intersection_are_not_forced_solutions() -> None:
    source_radius = R + 10.0
    receiver_radius = R + 1_000.0
    grazing_angle = acos(R / source_radius) + acos(R / receiver_radius)
    grazing = _trace(10.0, 1_000.0, R * grazing_angle)
    assert grazing.status is RaySolveStatus.BLOCKED_WITHIN_MODEL
    assert grazing.reason_code == "ground_grazing"
    assert grazing.path is not None
    assert grazing.diagnostics.minimum_clearance_m == pytest.approx(0.0, abs=1.0e-9)
    assert grazing.diagnostics.clearance_uncertainty_m >= 0.05

    intersecting = _trace(10.0, 1_000.0, R * (grazing_angle + 1.0e-5))
    assert intersecting.status is RaySolveStatus.BLOCKED_WITHIN_MODEL
    assert intersecting.reason_code == "ground_intersection"
    assert intersecting.path is None


def test_unsupported_branch_and_solver_exhaustion_have_distinct_statuses() -> None:
    nonmonotonic = RefractivityProfile.from_samples(
        (0.0, 1_000.0, 5_000.0),
        (1.001, 1.0, 1.0),
        source="synthetic nonmonotonic q",
        model_version="test nonmonotonic profile",
        humidity_basis="specified synthetic refractive index",
    )
    unsupported = _trace(10.0, 1_000.0, 20_000.0, nonmonotonic)
    assert unsupported.status is RaySolveStatus.UNSUPPORTED_BRANCH
    assert unsupported.reason_code == "nonmonotonic_q"

    exhausted = _trace(
        10.0,
        1_000.0,
        50_000.0,
        settings=RaySolverSettings(
            angular_tolerance_rad=1.0e-14,
            endpoint_tolerance_m=1.0e-8,
            maximum_iterations=1,
        ),
    )
    assert exhausted.status is RaySolveStatus.NUMERICAL_FAILURE
    assert exhausted.reason_code == "endpoint_residual"


def test_missing_clearance_profile_and_local_domain_limit_are_reported() -> None:
    raised_profile = _constant_profile(1.0, minimum_m=100.0)
    missing = _trace(1_000.0, 1_000.0, 50_000.0, raised_profile)
    assert missing.status is RaySolveStatus.MISSING_DATA
    assert missing.reason_code == "profile_missing_clearance_domain"

    outside_domain = _trace(1_000.0, 1_000.0, R * 0.36)
    assert outside_domain.status is RaySolveStatus.UNSUPPORTED_MODEL
    assert outside_domain.reason_code == "local_domain_exceeded"

