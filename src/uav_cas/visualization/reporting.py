"""Reporting-ready figures for the UAV communication dashboard."""

from __future__ import annotations

from math import atan2, hypot
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from uav_cas.atmosphere.profiles import RefractivityProfile
from uav_cas.reporting import MaximumConnectionResult, ReportingResult, SweepPoint


def atmosphere_profile_figure(profile: RefractivityProfile):
    """Create a compact five-panel thermodynamic/refractivity profile."""

    if not profile.thermodynamic_states:
        raise ValueError("thermodynamic states are required for the atmosphere figure")
    heights_km = [value / 1_000.0 for value in profile.geometric_heights_m]
    states = profile.thermodynamic_states
    series = (
        ([item.temperature_k for item in states], "Temperature (K)", "Temperature"),
        ([item.pressure_pa / 100.0 for item in states], "Pressure (hPa)", "Pressure"),
        ([item.density_kg_m3 for item in states], "Density (kg/m³)", "Density"),
        (list(profile.radio_refractivities_n_units), "N-units", "Radio refractivity N"),
        (
            [(value - 1.0) * 1.0e6 for value in profile.refractive_indices],
            "(n − 1) × 10⁶",
            "Refractive-index excess",
        ),
    )
    figure, axes_grid = plt.subplots(2, 3, figsize=(12.0, 7.2), sharey=True)
    axes = list(axes_grid.flat)
    colours = ("#c43c39", "#3569a8", "#3a8f5b", "#7952a2", "#b06a19")
    for axis, (values, label, title), colour in zip(axes, series, colours):
        axis.plot(values, heights_km, color=colour, linewidth=2.0)
        axis.set_xlabel(label)
        axis.set_title(title, fontsize=10)
        axis.grid(True, color="0.88", linewidth=0.7)
    axes[0].set_ylabel("Geometric height above MSL (km)")
    axes[3].set_ylabel("Geometric height above MSL (km)")
    figure.delaxes(axes[-1])
    figure.suptitle(f"Atmospheric profile\n{profile.source}", fontsize=12)
    figure.text(
        0.5,
        0.012,
        "Reference profile only; horizontally homogeneous; not local measured weather.",
        ha="center",
        fontsize=8,
    )
    figure.tight_layout(rect=(0.0, 0.045, 1.0, 0.90))
    return figure


def ray_cross_section_figure(result: ReportingResult):
    """Create a ground-arc versus radial-height ray cross-section."""

    ray = result.ray
    figure, axis = plt.subplots(figsize=(9.0, 5.2))
    maximum_km = result.inputs.surface_distance_km
    axis.plot(
        [0.0, maximum_km],
        [0.0, 0.0],
        color="black",
        linewidth=2.0,
        label="Smooth spherical MSL surface",
    )
    if ray.path is not None:
        distances_km = [
            ray.surface_radius_m * atan2(point[1], point[0]) / 1_000.0
            for point in ray.path.position_m
        ]
        heights_m = [
            hypot(point[0], point[1]) - ray.surface_radius_m
            for point in ray.path.position_m
        ]
        axis.plot(
            distances_km,
            heights_m,
            color="#0068b5",
            linewidth=2.2,
            label="Computed refracted direct ray",
        )
    axis.scatter(
        [0.0],
        [result.inputs.ground_station_height_msl_m],
        marker="^",
        s=75,
        color="#c43c35",
        zorder=5,
        label="Ground station",
    )
    axis.scatter(
        [maximum_km],
        [result.inputs.uav_altitude_msl_m],
        marker="o",
        s=60,
        color="#ef8a17",
        zorder=5,
        label="UAV",
    )
    axis.set_xlabel("Surface distance (km)")
    axis.set_ylabel("Radial height above smooth MSL sphere (m)")
    axis.set_title(
        "Direct-ray cross-section\n"
        f"status={result.ray_outputs.solver_status}; reason={result.ray_outputs.reason_code}; "
        f"branch={result.ray_outputs.ray_branch or 'unavailable'}"
    )
    axis.grid(True, color="0.88", linewidth=0.7)
    axis.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        fontsize=8,
        ncols=2,
        framealpha=0.95,
    )
    clearance = result.ray_outputs.minimum_clearance_m
    if clearance is not None:
        axis.text(
            0.98,
            0.04,
            f"Minimum smooth-surface clearance: {clearance:.3f} m",
            transform=axis.transAxes,
            ha="right",
            va="bottom",
            fontsize=8,
            bbox={"facecolor": "white", "edgecolor": "0.75", "alpha": 0.9},
        )
    if ray.path is None:
        axis.text(
            0.5,
            0.5,
            "No physical path samples are available for this solver outcome.",
            transform=axis.transAxes,
            ha="center",
            bbox={"facecolor": "white", "edgecolor": "0.7"},
        )
    figure.text(
        0.5,
        0.012,
        "Smooth spherical Earth; no terrain, diffraction, reflection, ducting, or multipath. Vertical scale expanded.",
        ha="center",
        fontsize=8,
    )
    figure.tight_layout(rect=(0.0, 0.08, 1.0, 1.0))
    return figure


def communication_performance_figure(
    points: tuple[SweepPoint, ...],
    *,
    requested_distance_km: float,
    maximum: MaximumConnectionResult,
    requested_result: ReportingResult | None = None,
):
    """Plot only computed sweep margins and preserve gaps for unavailable values."""

    plotted_points = list(points)
    if requested_result is not None and not any(
        abs(point.surface_distance_km - requested_distance_km) < 1.0e-12
        for point in plotted_points
    ):
        plotted_points.append(
            SweepPoint(
                surface_distance_km=requested_distance_km,
                ray_status=requested_result.ray_outputs.solver_status,
                ray_visible=requested_result.ray_outputs.ray_visibility,
                link_margin_db=requested_result.link_outputs.link_margin_db,
                feasible=requested_result.link_outputs.communication_feasible,
            )
        )
    ordered = sorted(plotted_points, key=lambda item: item.surface_distance_km)
    figure, axis = plt.subplots(figsize=(9.2, 5.0))
    segments: list[list[SweepPoint]] = []
    current: list[SweepPoint] = []
    for point in ordered:
        if point.link_margin_db is None:
            if current:
                segments.append(current)
                current = []
        else:
            current.append(point)
    if current:
        segments.append(current)
    for index, segment in enumerate(segments):
        axis.plot(
            [point.surface_distance_km for point in segment],
            [point.link_margin_db for point in segment],
            color="#5f6b73",
            linewidth=1.5,
            label="Computed margin samples" if index == 0 else None,
        )
    feasible = [point for point in ordered if point.link_margin_db is not None and point.feasible]
    infeasible = [
        point for point in ordered if point.link_margin_db is not None and not point.feasible
    ]
    if feasible:
        axis.scatter(
            [point.surface_distance_km for point in feasible],
            [point.link_margin_db for point in feasible],
            color="#16835f",
            s=34,
            zorder=4,
            label="Feasible sample",
        )
    if infeasible:
        axis.scatter(
            [point.surface_distance_km for point in infeasible],
            [point.link_margin_db for point in infeasible],
            color="#d97706",
            s=34,
            zorder=4,
            label="Insufficient-margin sample",
        )
    axis.axhline(0.0, color="#b42318", linewidth=1.2, linestyle="--", label="0 dB threshold")
    axis.axvline(
        requested_distance_km,
        color="#7c3aed",
        linewidth=1.2,
        linestyle=":",
        label="Requested distance",
    )
    if maximum.maximum_surface_distance_km is not None:
        if maximum.limiting_condition == "sweep limit reached":
            boundary_label = "Farthest demonstrated (sweep limit)"
        elif maximum.limiting_condition == "unresolved ray status":
            boundary_label = "Farthest demonstrated (boundary unresolved)"
        else:
            boundary_label = "Estimated feasible boundary"
        axis.axvline(
            maximum.maximum_surface_distance_km,
            color="#0068b5",
            linewidth=1.4,
            linestyle="-.",
            label=boundary_label,
        )
    missing = [point for point in ordered if point.link_margin_db is None]
    if missing:
        lower, upper = axis.get_ylim()
        marker_height = lower + 0.06 * (upper - lower)
        axis.scatter(
            [point.surface_distance_km for point in missing],
            [marker_height] * len(missing),
            marker="x",
            color="#6b21a8",
            s=55,
            zorder=5,
            label="Ray status only; margin unavailable",
        )
    axis.set_xlabel("Surface distance (km)")
    axis.set_ylabel("Link margin after required fade margin (dB)")
    axis.set_title("Communication performance versus distance")
    axis.grid(True, color="0.88", linewidth=0.7)
    axis.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        fontsize=8,
        ncols=3,
        framealpha=0.95,
    )
    figure.text(
        0.5,
        0.012,
        "Lines connect computed margins only; missing or unresolved margins are never replaced with zero.",
        ha="center",
        fontsize=8,
    )
    figure.tight_layout(rect=(0.0, 0.08, 1.0, 1.0))
    return figure


def maximum_connection_region_figure(
    altitude_results: tuple[tuple[float, MaximumConnectionResult], ...]
):
    """Plot UAV altitude versus maximum feasible surface distance."""

    altitudes_km = [altitude / 1_000.0 for altitude, _ in altitude_results]
    figure, axis = plt.subplots(figsize=(8.2, 5.2))
    resolved_conditions = {"insufficient link margin", "blocked ray"}
    segment_altitudes: list[float] = []
    segment_distances: list[float] = []

    def finish_segment() -> None:
        if len(segment_altitudes) >= 2:
            axis.fill_betweenx(
                segment_altitudes,
                [0.0] * len(segment_altitudes),
                segment_distances,
                color="#9ecae1",
                alpha=0.35,
                label=(
                    "Resolved feasible direct-connection region"
                    if not axis.collections
                    else None
                ),
            )
        segment_altitudes.clear()
        segment_distances.clear()

    for altitude_km, (_, result) in zip(altitudes_km, altitude_results):
        if (
            result.maximum_surface_distance_km is not None
            and result.limiting_condition in resolved_conditions
        ):
            segment_altitudes.append(altitude_km)
            segment_distances.append(result.maximum_surface_distance_km)
        else:
            finish_segment()
    finish_segment()

    categories = (
        ("insufficient link margin", "#d97706", "o", "Power-limited boundary"),
        ("blocked ray", "#0068b5", "s", "Ray-limited boundary"),
        ("sweep limit reached", "#6b7280", "^", "Sweep-limited; boundary unresolved"),
        (
            "unresolved ray status",
            "#6b21a8",
            "x",
            "Farthest demonstrated; boundary unresolved",
        ),
    )
    for condition, colour, marker, label in categories:
        selected = [
            (altitude / 1_000.0, result.maximum_surface_distance_km)
            for altitude, result in altitude_results
            if result.limiting_condition == condition
            and result.maximum_surface_distance_km is not None
        ]
        if selected:
            axis.scatter(
                [distance for _, distance in selected],
                [altitude for altitude, _ in selected],
                color=colour,
                marker=marker,
                s=48,
                zorder=4,
                label=label,
            )
    no_feasible_link = [
        altitude / 1_000.0
        for altitude, result in altitude_results
        if result.maximum_surface_distance_km is None
        and result.limiting_condition in resolved_conditions
    ]
    if no_feasible_link:
        axis.scatter(
            [0.0] * len(no_feasible_link),
            no_feasible_link,
            color="#b42318",
            marker="D",
            s=48,
            zorder=4,
            label="No feasible link",
        )
    unresolved_without_range = [
        altitude / 1_000.0
        for altitude, result in altitude_results
        if result.maximum_surface_distance_km is None
        and result.limiting_condition not in resolved_conditions
    ]
    if unresolved_without_range:
        axis.scatter(
            [0.0] * len(unresolved_without_range),
            unresolved_without_range,
            color="#6b21a8",
            marker="x",
            s=55,
            zorder=4,
            label="Unresolved ray status",
        )
    axis.set_xlabel("Estimated maximum feasible surface distance (km)")
    axis.set_ylabel("UAV altitude above MSL (km)")
    axis.set_title("Maximum connection region: direct ray + conditional link margin")
    axis.grid(True, color="0.85", linewidth=0.7)
    axis.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        fontsize=8,
        ncols=2,
        framealpha=0.95,
    )
    figure.text(
        0.5,
        0.012,
        "Idealized smooth-Earth direct-ray coverage estimate; terrain, clutter, and fading are not modeled.",
        ha="center",
        fontsize=8,
    )
    figure.tight_layout(rect=(0.0, 0.08, 1.0, 1.0))
    return figure


def save_figure(figure, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
        metadata={"Creator": "UAV-CAS minimal reporting build"},
    )
    plt.close(figure)
    return output_path
