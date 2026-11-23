"""Phase 2B independent references, robustness, and export regression tests."""

from __future__ import annotations

import csv
import json
from math import cos, sin

import pytest

from uav_cas.atmosphere.profiles import RefractivityProfile
from uav_cas.phase2b_demo import run_demo
from uav_cas.propagation import (
    PropagationRequest,
    RaySolverSettings,
    RaySolveStatus,
    trace_spherical_between,
    trace_uav_path,
)
from uav_cas.verification import trace_cartesian_fermat


RADIUS_M = 6_371_000.0


def _endpoint(height_m: float, distance_m: float) -> tuple[float, float, float]:
    angle = distance_m / RADIUS_M
    radius = RADIUS_M + height_m
    return (radius * cos(angle), radius * sin(angle), 0.0)


def test_independent_cartesian_fermat_reference_agrees_without_production_integrals() -> None:
    profile = RefractivityProfile.from_dry_isa(0.0, 5_000.0, 25.0)
    request = PropagationRequest("ground", "uav", 10.0, 1_000.0, 50_000.0)
    production = trace_uav_path(
        request,
        profile,
        solver_settings=RaySolverSettings(
            angular_tolerance_rad=1e-11,
            endpoint_tolerance_m=0.02,
            path_sample_count=101,
        ),
    )
    reference = trace_cartesian_fermat(
        request, profile, step_m=20.0, endpoint_tolerance_m=0.02
    )
    assert production.status is RaySolveStatus.SOLVED
    assert reference.status == "solved"
    assert reference.endpoint_error_m < 0.02
    assert reference.launch_elevation_deg == pytest.approx(
        production.path.source_elevation_deg, abs=1e-5
    )
    assert reference.geometric_length_m == pytest.approx(
        production.geometric_length_m, abs=5e-4
    )
    assert reference.refractivity_excess_m == pytest.approx(
        production.refractivity_excess_m, abs=5e-5
    )


def test_failure_taxonomy_keeps_physical_and_numerical_failures_distinct() -> None:
    profile = RefractivityProfile.from_dry_isa(0.0, 5_000.0, 25.0)
    request = PropagationRequest("ground", "uav", 10.0, 1_000.0, 130_000.0)
    exhausted = trace_uav_path(
        request,
        profile,
        solver_settings=RaySolverSettings(
            quadrature_angle_tolerance_rad=1e-16,
            quadrature_length_tolerance_m=1e-12,
            quadrature_refractivity_tolerance_m=1e-15,
            maximum_quadrature_depth=1,
        ),
    )
    assert exhausted.status is RaySolveStatus.NUMERICAL_FAILURE
    assert exhausted.reason_code == "quadrature_limit"

    blocked = trace_uav_path(
        PropagationRequest("ground", "uav", 10.0, 1_000.0, 140_000.0), profile
    )
    assert blocked.status is RaySolveStatus.BLOCKED_WITHIN_MODEL
    assert blocked.reason_code == "ground_intersection"

    ground_level = trace_uav_path(
        PropagationRequest("surface", "uav", 0.0, 1_000.0, 10_000.0), profile
    )
    assert ground_level.status is RaySolveStatus.BLOCKED_WITHIN_MODEL
    assert ground_level.reason_code == "ground_grazing"

    coincident = trace_spherical_between(
        (RADIUS_M + 10.0, 0.0, 0.0),
        (RADIUS_M + 10.0, 0.0, 0.0),
        2.4e9,
        RefractivityProfile.from_samples(
            (0.0, 5_000.0),
            (1.0, 1.0),
            source="constant",
            model_version="test constant-index profile",
            humidity_basis="specified constant refractive index",
        ),
        RADIUS_M,
        RADIUS_M,
    )
    assert coincident.status is RaySolveStatus.INVALID_INPUT
    assert coincident.reason_code == "coincident_endpoints"


def test_phase2b_demo_exports_complete_reproducible_bundle(tmp_path) -> None:
    summary = run_demo(tmp_path)
    expected = {
        "phase2b_profile_convergence.csv",
        "phase2b_integration_convergence.csv",
        "phase2b_shooting_convergence.csv",
        "phase2b_path_sampling_convergence.csv",
        "phase2b_benchmark_matrix.csv",
        "phase2b_near_horizon_sensitivity.csv",
        "phase2b_eer_comparison.csv",
        "phase2b_independent_reference.csv",
        "phase2b_ray_reference_comparison.png",
        "phase2b_profile_convergence.png",
        "phase2b_numerical_convergence.png",
        "phase2b_horizon_transition.png",
        "phase2b_eer_benchmark.png",
        "phase2b_refractivity_sensitivity.png",
        "phase2b_summary.json",
    }
    assert expected == {path.name for path in tmp_path.iterdir()}
    baseline = summary["regenerated_130km_case"]
    assert baseline["status"] == "solved"
    assert baseline["minimum_clearance_m"] == pytest.approx(6.868749, abs=2e-5)
    assert baseline["endpoint_error_m"] < 0.01
    assert summary["eer_metadata"]["derived_k"]["k_factor"] == pytest.approx(1.1914, rel=1e-3)
    with (tmp_path / "phase2b_benchmark_matrix.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 8
    assert {row["status"] for row in rows} >= {"solved", "blocked_within_model"}
    with (tmp_path / "phase2b_summary.json").open(encoding="utf-8") as handle:
        reloaded = json.load(handle)
    assert reloaded["baseline_profile"]["profile_hash"] == summary["baseline_profile"]["profile_hash"]
    assert all((tmp_path / name).stat().st_size > 50_000 for name in expected if name.endswith(".png"))
