"""Reproducible Phase 1 UAV atmospheric-analysis demonstration."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path

from .atmosphere.isa import AltitudeKind, standard_atmosphere
from .atmosphere.profiles import RefractivityProfile
from .atmosphere.refractivity import radio_refractivity
from .models import LinkConfiguration, LinkDirection, RadioEndpoint
from .link_budget import calculate_reference_link_budget
from .propagation.eer_reference import derive_effective_earth_k
from .propagation.geometry import RADIO_EARTH_RADIUS_M
from .visualization.atmosphere import (
    save_atmosphere_figures,
    save_horizon_reference_figure,
)

DEFAULT_MAXIMUM_ALTITUDE_M = 5_000.0
DEFAULT_SAMPLE_SPACING_M = 10.0
SELECTED_UAV_ALTITUDES_M = (0.0, 100.0, 250.0, 500.0, 1_000.0, 2_000.0, 3_000.0, 5_000.0)


def _row(height_m: float) -> dict[str, float]:
    state = standard_atmosphere(height_m, AltitudeKind.GEOMETRIC)
    refractivity = radio_refractivity(state.temperature_k, state.pressure_pa)
    return {
        "geometric_altitude_m": state.geometric_altitude_m,
        "geopotential_altitude_m": state.geopotential_altitude_m,
        "temperature_k": state.temperature_k,
        "temperature_c": state.temperature_c,
        "pressure_pa": state.pressure_pa,
        "density_kg_m3": state.density_kg_m3,
        "dynamic_viscosity_pa_s": state.dynamic_viscosity_pa_s,
        "speed_of_sound_m_s": state.speed_of_sound_m_s,
        "radio_refractivity_n_units": refractivity.radio_refractivity_n_units,
        "refractive_index": refractivity.refractive_index,
    }


def _write_csv(path: Path, rows: list[dict[str, float]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _reference_link_budgets() -> dict[str, dict[str, object]]:
    ground = RadioEndpoint(
        "ground",
        tx_power_dbm=30.0,
        tx_gain_dbi=8.0,
        tx_feeder_loss_db=2.0,
        rx_gain_dbi=8.0,
        rx_feeder_loss_db=2.0,
        receiver_sensitivity_dbm=-100.0,
        receiver_mode="example telemetry receiver",
        sensitivity_source="illustrative declared threshold",
    )
    uav = RadioEndpoint(
        "uav",
        tx_power_dbm=20.0,
        tx_gain_dbi=3.0,
        tx_feeder_loss_db=1.0,
        rx_gain_dbi=3.0,
        rx_feeder_loss_db=1.0,
        receiver_sensitivity_dbm=-90.0,
        receiver_mode="example command receiver",
        sensitivity_source="illustrative declared threshold",
    )
    results: dict[str, dict[str, object]] = {}
    for direction in (LinkDirection.UPLINK, LinkDirection.DOWNLINK):
        configuration = LinkConfiguration(
            direction,
            2.4e9,
            ground,
            uav,
            required_fade_margin_db=10.0,
        )
        results[direction.value] = asdict(
            calculate_reference_link_budget(configuration, 1_000.0)
        )
    return results


def run_demo(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    count = int(DEFAULT_MAXIMUM_ALTITUDE_M / DEFAULT_SAMPLE_SPACING_M)
    heights = [index * DEFAULT_SAMPLE_SPACING_M for index in range(count + 1)]
    rows = [_row(height) for height in heights]
    selected_rows = [_row(height) for height in SELECTED_UAV_ALTITUDES_M]
    profile = RefractivityProfile.from_dry_isa(
        0.0, DEFAULT_MAXIMUM_ALTITUDE_M, DEFAULT_SAMPLE_SPACING_M
    )
    profile_path = output_dir / "uav_atmosphere_profile.csv"
    selected_path = output_dir / "selected_uav_altitudes.csv"
    _write_csv(profile_path, rows)
    _write_csv(selected_path, selected_rows)
    figure_paths = save_atmosphere_figures(rows, output_dir)

    near_surface = RefractivityProfile.from_dry_isa(0.0, 1_000.0, 100.0)
    gradients = [
        (near_surface.refractive_indices[index + 1] - near_surface.refractive_indices[index])
        / (
            near_surface.geometric_heights_m[index + 1]
            - near_surface.geometric_heights_m[index]
        )
        for index in range(len(near_surface.geometric_heights_m) - 1)
    ]
    mean_gradient = sum(gradients) / len(gradients)
    relative_variation = max(abs(value - mean_gradient) for value in gradients) / abs(
        mean_gradient
    )
    derived = derive_effective_earth_k(
        mean_gradient,
        reference_refractive_index=near_surface.refractive_indices[0],
        minimum_height_m=0.0,
        maximum_height_m=1_000.0,
        maximum_relative_gradient_variation=relative_variation,
    )
    horizon_altitudes = [10.0 + index * 10.0 for index in range(100)]
    horizon_path = save_horizon_reference_figure(
        horizon_altitudes,
        ground_antenna_height_m=10.0,
        earth_radius_m=RADIO_EARTH_RADIUS_M,
        derived_k=derived.k_factor,
        derived_k_interval_m=(derived.minimum_height_m, derived.maximum_height_m),
        output_path=output_dir / "analytical_horizon_references.png",
    )
    figure_paths.append(horizon_path)

    summary: dict[str, object] = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scenario": {
            "name": "UAV dry standard-atmosphere Phase 1 demonstration",
            "geometric_altitude_range_m": [0.0, DEFAULT_MAXIMUM_ALTITUDE_M],
            "profile_spacing_m": DEFAULT_SAMPLE_SPACING_M,
            "selected_uav_altitudes_m": SELECTED_UAV_ALTITUDES_M,
            "earth_radius_for_radio_geometry_m": RADIO_EARTH_RADIUS_M,
        },
        "models": {
            "thermodynamics": "U.S. Standard Atmosphere 1976 compatible lower atmosphere",
            "refractivity": "ITU-R P.453-14 dry-air formula",
            "humidity": "e=0 dry reference; not a humidity measurement",
            "altitude_conversion": "geometric to geopotential using 6,356,766 m",
            "profile_interpolation": profile.interpolation,
            "profile_boundary_policy": profile.boundary_policy,
        },
        "profile_sha256": profile.profile_hash,
        "selected_conditions": selected_rows,
        "analytical_horizon_reference": {
            "labels": "geometric/EER analytical references, not ray-tracing predictions",
            "ground_antenna_height_m": 10.0,
            "k_values": [1.0, 4.0 / 3.0, derived.k_factor],
            "derived_k_gradient_dn_dh_per_m": mean_gradient,
            "derived_k_gradient_n_units_per_km": mean_gradient * 1.0e9,
            "derived_k_relative_gradient_variation": relative_variation,
            "derived_k_height_domain_m": [0.0, 1_000.0],
            "derived_k_applicability": derived.applicability,
        },
        "reference_link_budgets": _reference_link_budgets(),
        "limitations": [
            "Numerical verification is not experimental validation.",
            "The dry ISA profile is not measured weather and contains no vertical humidity profile.",
            "No atmospheric absorption model is included.",
            "Horizon curves are analytical geometric/EER references, not ray-tracing predictions.",
            "The FSPL budgets are illustrative conditional arithmetic, not coverage results.",
            "No Phase 2 ray-tracing BVP, terrain, diffraction, multipath, or field validation is present.",
        ],
        "files": [path.name for path in [profile_path, selected_path, *figure_paths]],
    }
    summary_path = output_dir / "phase1_summary.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate the reproducible UAV-CAS Phase 1 atmospheric demonstration"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/phase1"),
        help="output directory (default: outputs/phase1)",
    )
    arguments = parser.parse_args(argv)
    summary = run_demo(arguments.output_dir)
    print(f"Generated {len(summary['files']) + 1} Phase 1 files in {arguments.output_dir.resolve()}")
    print(f"Profile SHA-256: {summary['profile_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

