"""Deterministic Phase 2B numerical verification and benchmark workflow."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, replace
from math import atan2, cos, degrees, hypot, sin, sqrt
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from cubesat_link import RaySolverSettings, RaySolveStatus

from uav_cas.atmosphere.profiles import RefractivityProfile
from uav_cas.propagation import (
    EffectiveEarthRadiusReference,
    GeometricLosReference,
    PropagationRequest,
    derive_effective_earth_k,
    trace_uav_path,
)
from uav_cas.verification import trace_cartesian_fermat


EARTH_RADIUS_M = 6_371_000.0
FREQUENCY_HZ = 2.4e9
PROFILE_TOP_M = 5_000.0
BASE_REQUEST = PropagationRequest(
    "ground_station", "uav", 10.0, 1_000.0, 130_000.0,
    earth_radius_m=EARTH_RADIUS_M, frequency_hz=FREQUENCY_HZ,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty verification table: {path.name}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _result_fields(result) -> dict[str, object]:
    diagnostics = result.diagnostics
    return {
        "status": result.status.value,
        "reason_code": result.reason_code,
        "branch": None if diagnostics.branch is None else diagnostics.branch.value,
        "source_elevation_deg": None if result.path is None else result.path.source_elevation_deg,
        "arrival_elevation_deg": None
        if result.path is None else result.path.receiver_incident_elevation_deg,
        "endpoint_error_m": diagnostics.cartesian_endpoint_error_m,
        "angular_residual_rad": diagnostics.angular_endpoint_residual_rad,
        "minimum_clearance_m": diagnostics.minimum_clearance_m,
        "clearance_uncertainty_m": diagnostics.clearance_uncertainty_m,
        "invariant_relative_error": diagnostics.invariant_max_relative_error,
        "geometric_length_m": result.geometric_length_m,
        "optical_path_length_m": result.optical_path_length_m,
        "refractivity_excess_m": result.refractivity_excess_m,
        "excess_delay_ns": None if result.excess_delay_s is None else result.excess_delay_s * 1e9,
        "root_iterations": diagnostics.root_iterations,
        "quadrature_evaluations": diagnostics.quadrature_evaluations,
    }


def _settings_fields(settings: RaySolverSettings) -> dict[str, object]:
    return {
        "angular_tolerance_rad": settings.angular_tolerance_rad,
        "endpoint_tolerance_m": settings.endpoint_tolerance_m,
        "quadrature_angle_tolerance_rad": settings.quadrature_angle_tolerance_rad,
        "quadrature_length_tolerance_m": settings.quadrature_length_tolerance_m,
        "quadrature_refractivity_tolerance_m": settings.quadrature_refractivity_tolerance_m,
        "maximum_iterations": settings.maximum_iterations,
        "maximum_quadrature_depth": settings.maximum_quadrature_depth,
        "path_sample_count": settings.path_sample_count,
    }


def _constant_profile(index: float) -> RefractivityProfile:
    return RefractivityProfile.from_samples(
        (0.0, PROFILE_TOP_M),
        (index, index),
        source=f"analytical constant refractive index n={index:.7f}",
        model_version="Phase2B analytical constant-index control",
        humidity_basis="not applicable; mathematical reference",
    )


def _gradient_scaled_profile(base: RefractivityProfile, scale: float) -> RefractivityProfile:
    surface_n = base.refractive_indices[0]
    indices = tuple(surface_n + scale * (value - surface_n) for value in base.refractive_indices)
    return RefractivityProfile.from_samples(
        base.geometric_heights_m,
        indices,
        source=(
            "Synthetic gradient sensitivity derived from dry ISA/P.453; "
            f"vertical N departure from surface scaled by {scale:.3g}"
        ),
        model_version="Phase2B gradient-sensitivity profile v1",
        humidity_basis="dry reference perturbation; not observed weather",
    )


def _trace(request: PropagationRequest, profile: RefractivityProfile, settings=None):
    return trace_uav_path(request, profile, solver_settings=settings)


def _profile_convergence() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    # Tight shooting and quadrature controls keep endpoint-work error below the
    # atmospheric-grid differences being measured in this campaign.
    settings = RaySolverSettings(
        angular_tolerance_rad=1e-12,
        endpoint_tolerance_m=0.005,
        quadrature_angle_tolerance_rad=5e-13,
        quadrature_length_tolerance_m=5e-6,
        quadrature_refractivity_tolerance_m=5e-9,
        maximum_iterations=100,
        path_sample_count=101,
    )
    for spacing in (200.0, 100.0, 50.0, 25.0, 12.5):
        result = _trace(
            BASE_REQUEST,
            RefractivityProfile.from_dry_isa(0.0, PROFILE_TOP_M, spacing),
            settings,
        )
        rows.append({"profile_spacing_m": spacing, **_settings_fields(settings), **_result_fields(result)})
    reference = rows[-1]
    for row in rows:
        for field in (
            "source_elevation_deg", "minimum_clearance_m", "geometric_length_m",
            "optical_path_length_m", "refractivity_excess_m",
        ):
            row[f"delta_{field}_vs_12p5m"] = (
                None if row[field] is None else row[field] - reference[field]
            )
    return rows


def _integration_convergence(profile: RefractivityProfile) -> list[dict[str, object]]:
    tight = RaySolverSettings(
        angular_tolerance_rad=1e-11,
        endpoint_tolerance_m=0.05,
        quadrature_angle_tolerance_rad=2e-12,
        quadrature_length_tolerance_m=2e-5,
        quadrature_refractivity_tolerance_m=2e-8,
        path_sample_count=101,
    )
    campaigns = {
        "angular_integral": ("quadrature_angle_tolerance_rad", (2e-9, 2e-10, 2e-11, 2e-12)),
        "path_length_integral": ("quadrature_length_tolerance_m", (2e-2, 2e-3, 2e-4, 2e-5)),
        "refractivity_integral": (
            "quadrature_refractivity_tolerance_m", (2e-5, 2e-6, 2e-7, 2e-8)
        ),
    }
    rows: list[dict[str, object]] = []
    for campaign, (field, values) in campaigns.items():
        campaign_rows = []
        for value in values:
            settings = replace(tight, **{field: value})
            result = _trace(BASE_REQUEST, profile, settings)
            campaign_rows.append(
                {"campaign": campaign, "varied_setting": field, "setting_value": value,
                 **_settings_fields(settings), **_result_fields(result)}
            )
        reference = campaign_rows[-1]
        for row in campaign_rows:
            for metric in ("geometric_length_m", "refractivity_excess_m", "optical_path_length_m"):
                row[f"delta_{metric}_vs_tight"] = (
                    None if row[metric] is None else row[metric] - reference[metric]
                )
        rows.extend(campaign_rows)
    return rows


def _shooting_convergence(profile: RefractivityProfile) -> list[dict[str, object]]:
    rows = []
    for maximum_iterations in (8, 16, 24, 40, 80):
        settings = RaySolverSettings(
            angular_tolerance_rad=1e-11,
            endpoint_tolerance_m=0.05,
            maximum_iterations=maximum_iterations,
            path_sample_count=101,
        )
        result = _trace(BASE_REQUEST, profile, settings)
        rows.append({**_settings_fields(settings), **_result_fields(result)})
    return rows


def _path_sampling_convergence(profile: RefractivityProfile) -> list[dict[str, object]]:
    rows = []
    for count in (21, 51, 101, 201, 401, 801):
        settings = RaySolverSettings(path_sample_count=count)
        result = _trace(BASE_REQUEST, profile, settings)
        sampled_minimum = None if result.path is None else min(result.path.radial_height_m)
        rows.append(
            {
                "path_sample_count": count,
                "sampled_minimum_height_m": sampled_minimum,
                "sampled_minimum_minus_solver_clearance_m": None
                if sampled_minimum is None or result.diagnostics.minimum_clearance_m is None
                else sampled_minimum - result.diagnostics.minimum_clearance_m,
                **_result_fields(result),
            }
        )
    return rows


def _benchmark_matrix(dry_profile: RefractivityProfile) -> list[dict[str, object]]:
    cases = (
        ("constant_unequal_50km", 10.0, 1_000.0, 50_000.0, _constant_profile(1.0003)),
        ("constant_equal_50km", 1_000.0, 1_000.0, 50_000.0, _constant_profile(1.0)),
        ("dry_radial", 10.0, 1_000.0, 0.0, dry_profile),
        ("dry_short_10km", 10.0, 120.0, 10_000.0, dry_profile),
        ("dry_intermediate_75km", 10.0, 1_000.0, 75_000.0, dry_profile),
        ("dry_near_horizon_130km", 10.0, 1_000.0, 130_000.0, dry_profile),
        ("dry_ground_grazing_135p85km", 10.0, 1_000.0, 135_850.0, dry_profile),
        ("dry_blocked_140km", 10.0, 1_000.0, 140_000.0, dry_profile),
    )
    # These are the request-derived controls used by the Phase 2A UAV adapter;
    # retaining them here independently regenerates the previously reported
    # 130 km demonstration under the same numerical contract.
    settings = RaySolverSettings(
        angular_tolerance_rad=max(1e-12, 0.01 / EARTH_RADIUS_M),
        endpoint_tolerance_m=0.01,
        maximum_iterations=100,
    )
    rows = []
    for identifier, source_h, receiver_h, distance, profile in cases:
        request = PropagationRequest(
            f"source_{identifier}", f"receiver_{identifier}", source_h, receiver_h, distance,
            earth_radius_m=EARTH_RADIUS_M, frequency_hz=FREQUENCY_HZ,
        )
        result = _trace(request, profile, settings)
        rows.append(
            {
                "case_id": identifier,
                "source_height_msl_m": source_h,
                "receiver_height_msl_m": receiver_h,
                "surface_distance_m": distance,
                "profile_model": profile.model_version,
                "profile_hash": profile.profile_hash,
                **_settings_fields(settings),
                **_result_fields(result),
            }
        )
    return rows


def _near_horizon_sensitivity(base: RefractivityProfile) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    def record(category: str, value: float | str, request: PropagationRequest,
               profile: RefractivityProfile, settings: RaySolverSettings | None = None) -> None:
        result = _trace(request, profile, settings)
        rows.append(
            {
                "sensitivity_category": category,
                "sensitivity_value": value,
                "source_height_msl_m": request.source_height_msl_m,
                "receiver_height_msl_m": request.receiver_height_msl_m,
                "surface_distance_m": request.surface_distance_m,
                "profile_hash": profile.profile_hash,
                **_result_fields(result),
            }
        )

    for spacing in (200.0, 100.0, 50.0, 25.0, 12.5):
        record(
            "profile_spacing_m", spacing, BASE_REQUEST,
            RefractivityProfile.from_dry_isa(0.0, PROFILE_TOP_M, spacing),
        )
    for scale in (0.8, 0.9, 1.0, 1.1, 1.2):
        record("refractivity_gradient_scale", scale, BASE_REQUEST,
               _gradient_scaled_profile(base, scale))
    for height in (5.0, 10.0, 15.0):
        record("ground_height_m", height, replace(BASE_REQUEST, source_height_msl_m=height), base)
    for height in (900.0, 1_000.0, 1_100.0):
        record("uav_height_m", height, replace(BASE_REQUEST, receiver_height_msl_m=height), base)
    for distance in range(134_000, 136_001, 250):
        record("surface_distance_m", float(distance), replace(BASE_REQUEST, surface_distance_m=distance), base)
    tolerance_settings = {
        "loose": RaySolverSettings(
            angular_tolerance_rad=1e-8, endpoint_tolerance_m=0.1,
            quadrature_angle_tolerance_rad=1e-9, quadrature_length_tolerance_m=1e-3,
            quadrature_refractivity_tolerance_m=1e-5, path_sample_count=101,
        ),
        "default": RaySolverSettings(path_sample_count=101),
        "tight": RaySolverSettings(
            angular_tolerance_rad=1e-11, endpoint_tolerance_m=0.02,
            quadrature_angle_tolerance_rad=5e-13, quadrature_length_tolerance_m=5e-6,
            quadrature_refractivity_tolerance_m=5e-9, path_sample_count=101,
        ),
    }
    for name, settings in tolerance_settings.items():
        record("solver_tolerance_set", name, BASE_REQUEST, base, settings)
    return rows


def _eer_comparison(profile: RefractivityProfile) -> tuple[list[dict[str, object]], dict[str, object]]:
    gradients = [profile.gradient_at(height) for height in (0.0, 250.0, 500.0, 750.0, 1_000.0)]
    gradient_values = [value for value in gradients if value is not None]
    mean_gradient = sum(gradient_values) / len(gradient_values)
    variation = max(abs(value - mean_gradient) for value in gradient_values) / abs(mean_gradient)
    mid_index = profile.evaluate(500.0).refractive_index
    assert mid_index is not None
    derived = derive_effective_earth_k(
        mean_gradient,
        reference_refractive_index=mid_index,
        minimum_height_m=0.0,
        maximum_height_m=1_000.0,
        maximum_relative_gradient_variation=variation,
        earth_radius_m=EARTH_RADIUS_M,
    )
    methods = (
        ("geometric_k1", GeometricLosReference()),
        ("standard_k4_over_3", EffectiveEarthRadiusReference(4.0 / 3.0)),
        ("gradient_derived_k", EffectiveEarthRadiusReference(derived.k_factor, derived=derived)),
    )
    rows = []
    for uav_height in (100.0, 500.0, 1_000.0):
        for distance in (50_000.0, 100_000.0, 130_000.0, 140_000.0):
            request = replace(
                BASE_REQUEST,
                receiver_height_msl_m=uav_height,
                surface_distance_m=distance,
            )
            ray = _trace(request, profile)
            for method_name, method in methods:
                reference = method.solve(request)
                rows.append(
                    {
                        "method": method_name,
                        "k_factor": 1.0 if method_name == "geometric_k1" else method.k_factor,
                        "ground_height_msl_m": request.source_height_msl_m,
                        "uav_height_msl_m": uav_height,
                        "surface_distance_m": distance,
                        "reference_visible": reference.is_visible,
                        "reference_status": reference.status.value,
                        "reference_horizon_m": reference.maximum_surface_distance_m,
                        "ray_status": ray.status.value,
                        "ray_reason_code": ray.reason_code,
                        "ray_minimum_clearance_m": ray.diagnostics.minimum_clearance_m,
                        "ray_source_elevation_deg": None
                        if ray.path is None else ray.path.source_elevation_deg,
                    }
                )
    metadata = {
        "derived_k": asdict(derived),
        "sampled_gradient_N_per_km": [value * 1e9 for value in gradient_values],
        "interpretation": (
            "The derived k is a local near-horizontal approximation over 0-1000 m; "
            "it is not fitted to ray results and is not used inside the ray tracer."
        ),
    }
    return rows, metadata


def _independent_reference(profile: RefractivityProfile) -> list[dict[str, object]]:
    rows = []
    for distance in (50_000.0, 100_000.0):
        request = replace(BASE_REQUEST, surface_distance_m=distance)
        production = _trace(request, profile, RaySolverSettings(path_sample_count=101))
        for step_m in (20.0, 10.0):
            reference = trace_cartesian_fermat(
                request, profile, step_m=step_m, endpoint_tolerance_m=0.02
            )
            rows.append(
                {
                    "surface_distance_m": distance,
                    "reference_step_m": step_m,
                    "reference_status": reference.status,
                    "reference_endpoint_error_m": reference.endpoint_error_m,
                    "reference_launch_elevation_deg": reference.launch_elevation_deg,
                    "reference_geometric_length_m": reference.geometric_length_m,
                    "reference_refractivity_excess_m": reference.refractivity_excess_m,
                    "reference_optical_path_length_m": reference.optical_path_length_m,
                    "reference_shooting_iterations": reference.shooting_iterations,
                    "reference_integration_steps": reference.integration_steps,
                    "production_launch_elevation_deg": production.path.source_elevation_deg,
                    "production_geometric_length_m": production.geometric_length_m,
                    "production_refractivity_excess_m": production.refractivity_excess_m,
                    "production_optical_path_length_m": production.optical_path_length_m,
                    "delta_launch_elevation_deg": reference.launch_elevation_deg
                    - production.path.source_elevation_deg,
                    "delta_geometric_length_m": reference.geometric_length_m
                    - production.geometric_length_m,
                    "delta_refractivity_excess_m": reference.refractivity_excess_m
                    - production.refractivity_excess_m,
                }
            )
    return rows


def _analytical_and_reciprocity(profile: RefractivityProfile) -> dict[str, object]:
    constant = _constant_profile(1.0003)
    request = replace(BASE_REQUEST, surface_distance_m=50_000.0)
    verification_settings = RaySolverSettings(
        angular_tolerance_rad=1e-12,
        endpoint_tolerance_m=0.005,
        quadrature_angle_tolerance_rad=5e-13,
        quadrature_length_tolerance_m=5e-6,
        quadrature_refractivity_tolerance_m=5e-9,
        maximum_iterations=100,
        path_sample_count=101,
    )
    result = _trace(request, constant, verification_settings)
    r1 = EARTH_RADIUS_M + request.source_height_msl_m
    r2 = EARTH_RADIUS_M + request.receiver_height_msl_m
    phi = request.surface_distance_m / EARTH_RADIUS_M
    chord = sqrt(r1 * r1 + r2 * r2 - 2.0 * r1 * r2 * cos(phi))
    radial_component = r2 * cos(phi) - r1
    tangential_component = r2 * sin(phi)
    analytical_elevation = degrees(atan2(radial_component, tangential_component))

    reverse_request = PropagationRequest(
        "uav", "ground_station", 1_000.0, 10.0, 50_000.0,
        earth_radius_m=EARTH_RADIUS_M, frequency_hz=FREQUENCY_HZ,
    )
    forward = _trace(request, profile)
    reverse = _trace(reverse_request, profile)
    return {
        "constant_index": {
            "index": 1.0003,
            "central_angle_rad": phi,
            "surface_arc_m": request.surface_distance_m,
            "endpoint_chord_m": chord,
            "analytical_source_elevation_deg": analytical_elevation,
            "numerical_source_elevation_deg": result.path.source_elevation_deg,
            "geometric_length_error_m": result.geometric_length_m - chord,
            "optical_path_error_m": result.optical_path_length_m - 1.0003 * chord,
            "analytical_travel_time_s": 1.0003 * chord / 299_792_458.0,
            "numerical_travel_time_s": result.travel_time_s,
        },
        "reversibility": {
            "forward_status": forward.status.value,
            "reverse_status": reverse.status.value,
            "geometric_length_difference_m": forward.geometric_length_m - reverse.geometric_length_m,
            "optical_path_difference_m": forward.optical_path_length_m - reverse.optical_path_length_m,
            "clearance_difference_m": (
                forward.diagnostics.minimum_clearance_m - reverse.diagnostics.minimum_clearance_m
            ),
            "forward_launch_deg": forward.path.source_elevation_deg,
            "reverse_arrival_look_deg": reverse.path.receiver_look_elevation_deg,
        },
    }


def _save_figures(
    output_dir: Path,
    profile_rows: list[dict[str, object]],
    integration_rows: list[dict[str, object]],
    horizon_rows: list[dict[str, object]],
    eer_rows: list[dict[str, object]],
    independent_rows: list[dict[str, object]],
    production,
    reference,
) -> list[str]:
    figure_names: list[str] = []

    # Physical paths shown in radial height coordinates; vertical expansion is explicit.
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    px = [EARTH_RADIUS_M * atan2(y, x) / 1_000.0 for x, y, _ in production.path.position_m]
    ph = [hypot(x, y) - EARTH_RADIUS_M for x, y, _ in production.path.position_m]
    rx = [EARTH_RADIUS_M * atan2(y, x) / 1_000.0 for x, y in reference.position_m]
    rh = [hypot(x, y) - EARTH_RADIUS_M for x, y in reference.position_m]
    source, receiver = production.source_position_m, production.receiver_position_m
    chord = [
        tuple(source[i] + fraction * (receiver[i] - source[i]) for i in range(3))
        for fraction in (index / 400 for index in range(401))
    ]
    cx = [EARTH_RADIUS_M * atan2(y, x) / 1_000.0 for x, y, _ in chord]
    ch = [hypot(x, y) - EARTH_RADIUS_M for x, y, _ in chord]
    ax.plot(px, ph, label="Production spherical BVP", linewidth=2.1)
    ax.plot(rx, rh, "--", label=f"Independent Cartesian Fermat RK4 ({reference.step_m:g} m)")
    ax.plot(cx, ch, ":", color="0.35", label="Geometric straight chord")
    ax.axhline(0.0, color="black", linewidth=1.0, label="Smooth MSL sphere")
    ax.set(xlabel="Surface arc coordinate (km)", ylabel="Radial height above MSL sphere (m)",
           title="Independent ray-geometry comparison (vertical scale expanded)")
    ax.grid(alpha=0.25); ax.legend(fontsize=8); fig.tight_layout()
    name = "phase2b_ray_reference_comparison.png"; fig.savefig(output_dir / name, dpi=300); plt.close(fig)
    figure_names.append(name)

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6))
    spacing = [row["profile_spacing_m"] for row in profile_rows]
    axes[0].loglog(spacing[:-1], [abs(row["delta_optical_path_length_m_vs_12p5m"]) for row in profile_rows[:-1]], "o-")
    axes[0].invert_xaxis(); axes[0].set(xlabel="Profile spacing (m)", ylabel="|OPL - 12.5 m-grid OPL| (m)", title="Atmospheric-grid convergence")
    axes[1].semilogx(spacing, [row["minimum_clearance_m"] for row in profile_rows], "o-")
    axes[1].invert_xaxis(); axes[1].set(xlabel="Profile spacing (m)", ylabel="Minimum clearance (m)", title="Near-horizon clearance convergence")
    for axis in axes: axis.grid(alpha=0.25)
    fig.tight_layout(); name = "phase2b_profile_convergence.png"; fig.savefig(output_dir / name, dpi=300); plt.close(fig); figure_names.append(name)

    fig, ax1 = plt.subplots(figsize=(8.0, 4.8)); ax2 = ax1.twinx()
    for campaign, marker in (("angular_integral", "o"), ("path_length_integral", "s"), ("refractivity_integral", "^")):
        data = [row for row in integration_rows if row["campaign"] == campaign]
        ax1.loglog([row["setting_value"] for row in data], [max(abs(row["delta_optical_path_length_m_vs_tight"]), 1e-14) for row in data], marker + "-", label=campaign)
    data = [row for row in integration_rows if row["campaign"] == "path_length_integral"]
    ax2.semilogx([row["setting_value"] for row in data], [row["quadrature_evaluations"] for row in data], "k.--", label="evaluations")
    ax1.set(xlabel="Varied absolute quadrature tolerance (native units)", ylabel="|OPL delta vs tight row| (m)", title="Independent quadrature-tolerance campaigns")
    ax2.set_ylabel("Cumulative integrand evaluations")
    ax1.grid(alpha=0.25); ax1.legend(fontsize=8, loc="upper left"); fig.tight_layout()
    name = "phase2b_numerical_convergence.png"; fig.savefig(output_dir / name, dpi=300); plt.close(fig); figure_names.append(name)

    distance_rows = [row for row in horizon_rows if row["sensitivity_category"] == "surface_distance_m"]
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    colors = ["#187b2d" if row["status"] == "solved" else "#b21f2d" for row in distance_rows]
    ax.scatter([row["surface_distance_m"] / 1_000.0 for row in distance_rows], [row["minimum_clearance_m"] for row in distance_rows], c=colors)
    ax.axhspan(0.0, 0.05, color="#e6a700", alpha=0.25, label="declared grazing band (0-0.05 m)")
    ax.set(xlabel="Surface separation (km)", ylabel="Minimum smooth-surface clearance (m)", title="Near-horizon visibility transition: 10 m / 1000 m endpoints")
    ax.grid(alpha=0.25); ax.legend(fontsize=8); fig.tight_layout()
    name = "phase2b_horizon_transition.png"; fig.savefig(output_dir / name, dpi=300); plt.close(fig); figure_names.append(name)

    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    for method in ("geometric_k1", "gradient_derived_k", "standard_k4_over_3"):
        data = [row for row in eer_rows if row["method"] == method and row["surface_distance_m"] == 50_000.0]
        ax.plot([row["uav_height_msl_m"] for row in data], [row["reference_horizon_m"] / 1_000.0 for row in data], "o-", label=method)
    ax.set(xlabel="UAV altitude MSL (m)", ylabel="Analytical horizon surface distance (km)", title="Independent EER horizon benchmarks (ground antenna 10 m MSL)")
    ax.grid(alpha=0.25); ax.legend(fontsize=8); fig.tight_layout()
    name = "phase2b_eer_benchmark.png"; fig.savefig(output_dir / name, dpi=300); plt.close(fig); figure_names.append(name)

    gradient_rows = [row for row in horizon_rows if row["sensitivity_category"] == "refractivity_gradient_scale"]
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    ax.plot([float(row["sensitivity_value"]) for row in gradient_rows], [row["minimum_clearance_m"] for row in gradient_rows], "o-")
    ax.set(xlabel="Synthetic vertical-gradient scale (dimensionless)", ylabel="Minimum clearance at 130 km (m)", title="Atmospheric-model sensitivity (not a weather uncertainty bound)")
    ax.grid(alpha=0.25); fig.tight_layout(); name = "phase2b_refractivity_sensitivity.png"; fig.savefig(output_dir / name, dpi=300); plt.close(fig); figure_names.append(name)
    return figure_names


def run_demo(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    dry_profile = RefractivityProfile.from_dry_isa(0.0, PROFILE_TOP_M, 25.0)
    profile_rows = _profile_convergence()
    integration_rows = _integration_convergence(dry_profile)
    shooting_rows = _shooting_convergence(dry_profile)
    sampling_rows = _path_sampling_convergence(dry_profile)
    benchmark_rows = _benchmark_matrix(dry_profile)
    horizon_rows = _near_horizon_sensitivity(dry_profile)
    eer_rows, eer_metadata = _eer_comparison(dry_profile)
    independent_rows = _independent_reference(dry_profile)
    analytical = _analytical_and_reciprocity(dry_profile)

    tables = {
        "phase2b_profile_convergence.csv": profile_rows,
        "phase2b_integration_convergence.csv": integration_rows,
        "phase2b_shooting_convergence.csv": shooting_rows,
        "phase2b_path_sampling_convergence.csv": sampling_rows,
        "phase2b_benchmark_matrix.csv": benchmark_rows,
        "phase2b_near_horizon_sensitivity.csv": horizon_rows,
        "phase2b_eer_comparison.csv": eer_rows,
        "phase2b_independent_reference.csv": independent_rows,
    }
    for name, rows in tables.items():
        _write_csv(output_dir / name, rows)

    figure_request = replace(BASE_REQUEST, surface_distance_m=50_000.0)
    production = _trace(figure_request, dry_profile)
    reference = trace_cartesian_fermat(
        figure_request, dry_profile, step_m=10.0, endpoint_tolerance_m=0.02
    )
    if production.status is not RaySolveStatus.SOLVED or reference.status != "solved":
        raise RuntimeError("Phase 2B independent figure reference did not converge")
    figures = _save_figures(
        output_dir, profile_rows, integration_rows, horizon_rows, eer_rows,
        independent_rows, production, reference,
    )

    baseline = next(row for row in benchmark_rows if row["case_id"] == "dry_near_horizon_130km")
    gradient_rows = [row for row in horizon_rows if row["sensitivity_category"] == "refractivity_gradient_scale"]
    summary: dict[str, object] = {
        "milestone": "Phase 2B - Scientific Verification and Benchmarking",
        "determinism": "No random inputs; fixed configurations, grids, tolerances, and plotting settings",
        "baseline_profile": {
            "source": dry_profile.source,
            "model_version": dry_profile.model_version,
            "profile_hash": dry_profile.profile_hash,
            "height_bounds_m": [dry_profile.minimum_height_m, dry_profile.maximum_height_m],
            "spacing_m": 25.0,
        },
        "regenerated_130km_case": baseline,
        "analytical_and_reciprocity": analytical,
        "eer_metadata": eer_metadata,
        "numerical_findings": {
            "profile_200m_to_12p5m_clearance_change_m": profile_rows[0]["minimum_clearance_m"] - profile_rows[-1]["minimum_clearance_m"],
            "profile_25m_to_12p5m_clearance_change_m": profile_rows[-2]["minimum_clearance_m"] - profile_rows[-1]["minimum_clearance_m"],
            "gradient_sensitivity_clearance_range_m": [
                min(row["minimum_clearance_m"] for row in gradient_rows),
                max(row["minimum_clearance_m"] for row in gradient_rows),
            ],
            "independent_reference_max_abs_length_delta_m": max(
                abs(row["delta_geometric_length_m"]) for row in independent_rows
            ),
            "independent_reference_max_abs_refractivity_delta_m": max(
                abs(row["delta_refractivity_excess_m"]) for row in independent_rows
            ),
        },
        "interpretation_limits": [
            "Numerical convergence verifies the stated scalar spherical equations; it is not field validation.",
            "The dry ISA/P.453 profile and synthetic gradient scaling do not quantify real weather uncertainty.",
            "A clear geometrical ray does not establish communications-link availability or margin.",
            "EER is an independent approximation benchmark and is never a solver fallback.",
        ],
        "files": [*tables, *figures, "phase2b_summary.json"],
    }
    with (output_dir / "phase2b_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic Phase 2B verification outputs")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/phase2b"))
    args = parser.parse_args(argv)
    summary = run_demo(args.output_dir)
    baseline = summary["regenerated_130km_case"]
    print(f"Generated Phase 2B outputs in {args.output_dir.resolve()}")
    print(
        f"130km status={baseline['status']}; clearance_m={baseline['minimum_clearance_m']:.9g}; "
        f"endpoint_error_m={baseline['endpoint_error_m']:.6g}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
