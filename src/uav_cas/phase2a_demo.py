"""Reproducible Phase 2A UAV spherical ray demonstration and exports."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import json
from math import atan2, cos, hypot, sin
from pathlib import Path

from cubesat_link import NeutralProfile, RaySolveStatus, trace_spherical_between

from .atmosphere.profiles import RefractivityProfile
from .propagation import PropagationRequest, trace_uav_path
from .visualization.ray_path import save_ray_path_figure


EARTH_RADIUS_M = 6_371_000.0
FREQUENCY_HZ = 2.4e9
SOURCE_HEIGHT_M = 10.0
UAV_HEIGHT_M = 1_000.0
SURFACE_DISTANCE_M = 130_000.0
PROFILE_TOP_M = 5_000.0
PROFILE_SPACING_M = 25.0


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _path_rows(result) -> list[dict[str, object]]:
    assert result.path is not None
    rows = []
    for index, (arc, position, height) in enumerate(
        zip(result.path.arc_length_m, result.path.position_m, result.path.radial_height_m)
    ):
        angle = atan2(position[1], position[0])
        rows.append(
            {
                "sample_index": index,
                "arc_length_m": arc,
                "x_ecef_m": position[0],
                "y_ecef_m": position[1],
                "z_ecef_m": position[2],
                "central_angle_rad": angle,
                "ground_arc_m": EARTH_RADIUS_M * angle,
                "radial_height_above_earth_m": height,
                "surface_clearance_m": hypot(position[0], position[1]) - EARTH_RADIUS_M,
            }
        )
    return rows


def _constant_index_cases() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, source_height, receiver_height, distance in (
        (1.0, 10.0, 1_000.0, 50_000.0),
        (1.0003, 1_000.0, 1_000.0, 50_000.0),
    ):
        profile = NeutralProfile(
            (0.0, PROFILE_TOP_M),
            (index, index),
            f"constant index verification n={index}",
            (1.0e8, 12.0e9),
            outside="unavailable",
        )
        angle = distance / EARTH_RADIUS_M
        source = (EARTH_RADIUS_M + source_height, 0.0, 0.0)
        receiver_radius = EARTH_RADIUS_M + receiver_height
        receiver = (receiver_radius * cos(angle), receiver_radius * sin(angle), 0.0)
        result = trace_spherical_between(
            source,
            receiver,
            FREQUENCY_HZ,
            profile,
            EARTH_RADIUS_M,
            EARTH_RADIUS_M,
        )
        rows.append(
            {
                "case": f"constant_n_{index:g}_{source_height:g}_to_{receiver_height:g}_m",
                "status": result.status.value,
                "branch": result.diagnostics.branch.value if result.diagnostics.branch else None,
                "refractive_index": index,
                "surface_distance_m": distance,
                "endpoint_chord_m": result.endpoint_chord_m,
                "geometric_length_m": result.geometric_length_m,
                "straight_limit_error_m": result.geometric_length_m - result.endpoint_chord_m,
                "optical_path_length_m": result.optical_path_length_m,
                "expected_optical_path_length_m": index * result.endpoint_chord_m,
                "angular_endpoint_residual_rad": result.diagnostics.angular_endpoint_residual_rad,
                "cartesian_endpoint_error_m": result.diagnostics.cartesian_endpoint_error_m,
            }
        )
    return rows


def _convergence_rows(request: PropagationRequest) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for spacing in (200.0, 100.0, 50.0, 25.0):
        profile = RefractivityProfile.from_dry_isa(0.0, PROFILE_TOP_M, spacing)
        result = trace_uav_path(request, profile)
        rows.append(
            {
                "profile_spacing_m": spacing,
                "status": result.status.value,
                "branch": result.diagnostics.branch.value if result.diagnostics.branch else None,
                "source_elevation_deg": None
                if result.path is None
                else result.path.source_elevation_deg,
                "geometric_length_m": result.geometric_length_m,
                "refractivity_excess_m": result.refractivity_excess_m,
                "minimum_clearance_m": result.diagnostics.minimum_clearance_m,
                "angular_endpoint_residual_rad": result.diagnostics.angular_endpoint_residual_rad,
                "cartesian_endpoint_error_m": result.diagnostics.cartesian_endpoint_error_m,
                "invariant_max_relative_error": result.diagnostics.invariant_max_relative_error,
                "quadrature_evaluations": result.diagnostics.quadrature_evaluations,
            }
        )
    return rows


def run_demo(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    profile = RefractivityProfile.from_dry_isa(0.0, PROFILE_TOP_M, PROFILE_SPACING_M)
    request = PropagationRequest(
        "ground_station",
        "uav",
        SOURCE_HEIGHT_M,
        UAV_HEIGHT_M,
        SURFACE_DISTANCE_M,
        earth_radius_m=EARTH_RADIUS_M,
        frequency_hz=FREQUENCY_HZ,
    )
    result = trace_uav_path(request, profile)
    if result.status is not RaySolveStatus.SOLVED or result.path is None:
        raise RuntimeError(f"Phase 2A demonstration ray failed: {result.status}: {result.reason}")

    path_file = output_dir / "phase2a_ray_path.csv"
    convergence_file = output_dir / "phase2a_profile_convergence.csv"
    verification_file = output_dir / "phase2a_constant_index_verification.csv"
    figure_file = output_dir / "phase2a_uav_ray_cross_section.png"
    _write_csv(path_file, _path_rows(result))
    convergence_rows = _convergence_rows(request)
    _write_csv(convergence_file, convergence_rows)
    constant_rows = _constant_index_cases()
    _write_csv(verification_file, constant_rows)
    save_ray_path_figure(
        result,
        figure_file,
        profile_label="dry ISA-1976 / ITU-R P.453-14, 25 m profile grid",
    )

    summary: dict[str, object] = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "milestone": "Phase 2A - UAV Ray-Tracing Solver Foundation",
        "scenario": asdict(request),
        "atmosphere": {
            "source": profile.source,
            "model_version": profile.model_version,
            "humidity_basis": profile.humidity_basis,
            "height_bounds_m": [profile.minimum_height_m, profile.maximum_height_m],
            "spacing_m": PROFILE_SPACING_M,
            "profile_sha256": profile.profile_hash,
            "boundary_policy": profile.boundary_policy,
        },
        "ray_result": asdict(result),
        "constant_index_verification": constant_rows,
        "profile_convergence": convergence_rows,
        "method_separation": {
            "primary": "trace_spherical_between physical refracted ray",
            "geometric_straight_path": "independent vacuum chord shown for comparison",
            "effective_earth_radius": "independent reference only; not called and never used as fallback",
        },
        "scope_limits": [
            "strictly increasing q(r)=n(r)r only",
            "short-arc radial-monotonic and single-minimum direct families only",
            "smooth spherical ground; no terrain, diffraction, reflection, ducting, multipath, or coverage search",
            "numerical/software verification is not experimental field validation",
        ],
        "files": [
            path_file.name,
            convergence_file.name,
            verification_file.name,
            figure_file.name,
            "phase2a_summary.json",
        ],
    }
    summary_file = output_dir / "phase2a_summary.json"
    with summary_file.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate reproducible Phase 2A UAV spherical-ray outputs"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/phase2a"),
        help="output directory (default: outputs/phase2a)",
    )
    arguments = parser.parse_args(argv)
    summary = run_demo(arguments.output_dir)
    result = summary["ray_result"]
    print(f"Generated Phase 2A outputs in {arguments.output_dir.resolve()}")
    print(
        f"status={result['status']}; branch={result['diagnostics']['branch']}; "
        f"endpoint_error_m={result['diagnostics']['cartesian_endpoint_error_m']:.6g}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

