"""Command-line reporting workflow for reproducible PNG/CSV/JSON outputs."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import json
from pathlib import Path

from .reporting import (
    AtmosphereModel,
    ReportingInputs,
    altitude_coverage_curve,
    analyze_reporting_case,
    estimate_maximum_connection,
)
from .visualization.reporting import (
    atmosphere_profile_figure,
    communication_performance_figure,
    maximum_connection_region_figure,
    ray_cross_section_figure,
    save_figure,
)


def _altitudes(inputs: ReportingInputs) -> list[float]:
    candidates = {
        100.0,
        250.0,
        500.0,
        1_000.0,
        2_000.0,
        3_000.0,
        5_000.0,
        inputs.uav_altitude_msl_m,
    }
    return sorted(value for value in candidates if value > inputs.ground_station_height_msl_m)


def generate_reporting_outputs(inputs: ReportingInputs, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    result = analyze_reporting_case(inputs)
    maximum = estimate_maximum_connection(inputs)
    coverage = altitude_coverage_curve(inputs, _altitudes(inputs))

    atmosphere_csv = output_dir / "atmosphere_profile.csv"
    with atmosphere_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "geometric_height_msl_m",
                "temperature_k",
                "pressure_pa",
                "density_kg_m3",
                "radio_refractivity_n_units",
                "refractive_index",
            ]
        )
        for height, state, refractivity, index in zip(
            result.profile.geometric_heights_m,
            result.profile.thermodynamic_states,
            result.profile.radio_refractivities_n_units,
            result.profile.refractive_indices,
        ):
            writer.writerow(
                [height, state.temperature_k, state.pressure_pa, state.density_kg_m3,
                 refractivity, index]
            )

    sweep_csv = output_dir / "maximum_connection_sweep.csv"
    with sweep_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=asdict(maximum.points[0]).keys())
        writer.writeheader()
        writer.writerows(asdict(point) for point in maximum.points)

    coverage_csv = output_dir / "altitude_maximum_connection.csv"
    with coverage_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["uav_altitude_msl_m", "maximum_surface_distance_km", "limiting_condition",
             "limiting_reason", "resolution_km"]
        )
        for altitude, item in coverage:
            writer.writerow(
                [altitude, item.maximum_surface_distance_km, item.limiting_condition,
                 item.limiting_reason, item.resolution_km]
            )

    figures = {
        "atmosphere_profile": save_figure(
            atmosphere_profile_figure(result.profile), output_dir / "atmosphere_profile.png"
        ),
        "ray_cross_section": save_figure(
            ray_cross_section_figure(result), output_dir / "ray_cross_section.png"
        ),
        "communication_performance": save_figure(
            communication_performance_figure(
                maximum.points,
                requested_distance_km=inputs.surface_distance_km,
                maximum=maximum,
                requested_result=result,
            ),
            output_dir / "communication_performance.png",
        ),
        "maximum_connection_region": save_figure(
            maximum_connection_region_figure(coverage),
            output_dir / "maximum_connection_region.png",
        ),
    }
    summary = {
        "application": "UAV Communication Analysis Suite",
        "reference_location": {
            "name": "Ho Chi Minh City",
            "latitude_deg_n": 10.82,
            "longitude_deg_e": 106.63,
        },
        "inputs": asdict(inputs),
        "atmospheric_outputs_at_uav": asdict(result.atmosphere),
        "ray_outputs": asdict(result.ray_outputs),
        "link_outputs": asdict(result.link_outputs),
        "maximum_connection": {
            key: value for key, value in asdict(maximum).items() if key != "points"
        },
        "profile": {
            "source": result.profile.source,
            "model_version": result.profile.model_version,
            "profile_sha256": result.profile.profile_hash,
            "spacing_m": 25.0,
        },
        "assumptions_and_limitations": [
            "smooth spherical MSL Earth and horizontally homogeneous reference atmosphere",
            "verified nonducting direct-ray family only; no EER fallback",
            "endpoint-chord ITU-R P.525 free-space spreading approximation",
            "no terrain, clutter, diffraction, reflection, multipath, gas loss, rain, interference, or fading statistics",
            "deterministic reporting estimate, not real-world validation or guaranteed operational range",
        ],
        "files": {
            "atmosphere_csv": atmosphere_csv.name,
            "sweep_csv": sweep_csv.name,
            "coverage_csv": coverage_csv.name,
            **{key: value.name for key, value in figures.items()},
        },
    }
    summary_path = output_dir / "reporting_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate UAV communication simulation reporting outputs"
    )
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/reporting"))
    parser.add_argument("--atmosphere", choices=("ITU", "ISA"), default="ITU")
    parser.add_argument("--ground-height-m", type=float, default=10.0)
    parser.add_argument("--uav-altitude-m", type=float, default=1_000.0)
    parser.add_argument("--distance-km", type=float, default=50.0)
    parser.add_argument("--frequency-mhz", type=float, default=2_400.0)
    parser.add_argument("--tx-power-dbm", type=float, default=30.0)
    parser.add_argument("--tx-gain-dbi", type=float, default=2.0)
    parser.add_argument("--rx-gain-dbi", type=float, default=2.0)
    parser.add_argument("--tx-loss-db", type=float, default=1.0)
    parser.add_argument("--rx-loss-db", type=float, default=1.0)
    parser.add_argument("--sensitivity-dbm", type=float, default=-100.0)
    parser.add_argument("--required-margin-db", type=float, default=0.0)
    parser.add_argument("--sweep-max-km", type=float, default=500.0)
    parser.add_argument("--sweep-step-km", type=float, default=5.0)
    args = parser.parse_args(argv)
    inputs = ReportingInputs(
        ground_station_height_msl_m=args.ground_height_m,
        uav_altitude_msl_m=args.uav_altitude_m,
        surface_distance_km=args.distance_km,
        frequency_mhz=args.frequency_mhz,
        transmit_power_dbm=args.tx_power_dbm,
        transmitter_gain_dbi=args.tx_gain_dbi,
        receiver_gain_dbi=args.rx_gain_dbi,
        tx_loss_db=args.tx_loss_db,
        rx_loss_db=args.rx_loss_db,
        receiver_sensitivity_dbm=args.sensitivity_dbm,
        required_margin_db=args.required_margin_db,
        atmosphere_model=AtmosphereModel(args.atmosphere),
        sweep_max_km=args.sweep_max_km,
        sweep_step_km=args.sweep_step_km,
    )
    summary = generate_reporting_outputs(inputs, args.output_dir)
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
