"""Professional, headless Matplotlib figures for calculated Phase 1 data."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from uav_cas.propagation.geometry import two_endpoint_horizon_surface_distance_m


def _save_line_figure(
    x_values: Sequence[float],
    y_values: Sequence[float],
    *,
    xlabel: str,
    ylabel: str,
    title: str,
    output_path: Path,
    colour: str,
) -> None:
    figure, axis = plt.subplots(figsize=(7.2, 4.8), constrained_layout=True)
    axis.plot(x_values, y_values, color=colour, linewidth=2.0)
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.grid(True, which="both", color="0.85", linewidth=0.7)
    figure.savefig(output_path, dpi=300, metadata={"Creator": "UAV-CAS Phase 1"})
    plt.close(figure)


def save_atmosphere_figures(rows: Sequence[dict[str, float]], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    altitude_km = [row["geometric_altitude_m"] / 1000.0 for row in rows]
    definitions = (
        ("temperature_k", "Temperature (K)", "Standard-Atmosphere Temperature", "temperature_vs_altitude.png", "#c43c39"),
        ("pressure_pa", "Pressure (Pa)", "Standard-Atmosphere Pressure", "pressure_vs_altitude.png", "#3569a8"),
        ("density_kg_m3", "Density (kg m$^{-3}$)", "Standard-Atmosphere Density", "density_vs_altitude.png", "#3a8f5b"),
        ("radio_refractivity_n_units", "Radio refractivity, N (N-units)", "Dry-Air Radio Refractivity (ITU-R P.453-14)", "refractivity_N_vs_altitude.png", "#7952a2"),
        ("refractive_index", "Refractive index, n (dimensionless)", "Dry-Air Refractive Index", "refractive_index_vs_altitude.png", "#b06a19"),
    )
    outputs: list[Path] = []
    for key, ylabel, title, filename, colour in definitions:
        destination = output_dir / filename
        _save_line_figure(
            altitude_km,
            [row[key] for row in rows],
            xlabel="Geometric altitude above MSL (km)",
            ylabel=ylabel,
            title=title,
            output_path=destination,
            colour=colour,
        )
        outputs.append(destination)
    return outputs


def save_horizon_reference_figure(
    uav_altitudes_m: Sequence[float],
    *,
    ground_antenna_height_m: float,
    earth_radius_m: float,
    derived_k: float,
    derived_k_interval_m: tuple[float, float],
    output_path: Path,
) -> Path:
    altitude_values = list(uav_altitudes_m)
    figure, axis = plt.subplots(figsize=(7.6, 5.0), constrained_layout=True)
    for k_factor, label, style in (
        (1.0, "Geometric reference (k=1)", "-"),
        (4.0 / 3.0, "Conventional EER reference (k=4/3)", "--"),
        (derived_k, f"Gradient-derived EER reference (k={derived_k:.3f})", ":"),
    ):
        ranges_km = [
            two_endpoint_horizon_surface_distance_m(
                ground_antenna_height_m,
                altitude,
                earth_radius_m=k_factor * earth_radius_m,
            )
            / 1000.0
            for altitude in altitude_values
        ]
        axis.plot(
            [value / 1000.0 for value in altitude_values],
            ranges_km,
            linestyle=style,
            linewidth=2.0,
            label=label,
        )
    axis.set_xlabel("UAV height above spherical MSL (km)")
    axis.set_ylabel("Maximum analytical surface distance (km)")
    axis.set_title("Analytical Horizon References — Not Ray-Tracing Predictions")
    axis.grid(True, color="0.85", linewidth=0.7)
    axis.legend(loc="best")
    axis.text(
        0.02,
        0.02,
        (
            f"Ground antenna: {ground_antenna_height_m:g} m; derived-k domain: "
            f"{derived_k_interval_m[0]:g}–{derived_k_interval_m[1]:g} m"
        ),
        transform=axis.transAxes,
        fontsize=8,
        va="bottom",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=300, metadata={"Creator": "UAV-CAS Phase 1"})
    plt.close(figure)
    return output_path

