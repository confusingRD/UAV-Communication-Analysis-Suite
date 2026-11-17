"""Headless, reproducible Phase 2A spherical-ray figures."""

from __future__ import annotations

from math import atan2, cos, hypot, sin
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from cubesat_link import SphericalRayResult


def save_ray_path_figure(
    result: SphericalRayResult,
    output_path: Path,
    *,
    profile_label: str,
) -> Path:
    """Plot a physical equal-scale section plus a height-resolving diagnostic."""

    if result.path is None or result.central_angle_rad is None:
        raise ValueError("a computed path is required for the Phase 2A ray figure")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    radius = result.surface_radius_m
    source = result.source_position_m
    receiver = result.receiver_position_m
    path = result.path.position_m
    count = 501
    angles = [result.central_angle_rad * index / (count - 1) for index in range(count)]
    surface = [(radius * cos(angle), radius * sin(angle)) for angle in angles]
    straight = [
        (
            source[0] + (receiver[0] - source[0]) * index / (count - 1),
            source[1] + (receiver[1] - source[1]) * index / (count - 1),
        )
        for index in range(count)
    ]

    def physical_xy(points):
        return (
            [point[1] / 1_000.0 for point in points],
            [(point[0] - radius) / 1_000.0 for point in points],
        )

    def height_xy(points):
        return (
            [radius * atan2(point[1], point[0]) / 1_000.0 for point in points],
            [hypot(point[0], point[1]) - radius for point in points],
        )

    figure, (physical, detail) = plt.subplots(1, 2, figsize=(13.0, 5.8), dpi=150)
    sx, sz = physical_xy(surface)
    gx, gz = physical_xy(straight)
    rx, rz = physical_xy(path)
    physical.plot(sx, sz, color="black", linewidth=2.0, label="Earth surface")
    physical.plot(
        gx, gz, color="0.45", linestyle="--", linewidth=1.6, label="Geometric straight chord"
    )
    physical.plot(rx, rz, color="#0068b5", linewidth=2.1, label="Refracted ray")
    physical.scatter(
        [source[1] / 1_000.0],
        [(source[0] - radius) / 1_000.0],
        marker="^",
        s=70,
        color="#c43c35",
        zorder=5,
        label="Ground station",
    )
    physical.scatter(
        [receiver[1] / 1_000.0],
        [(receiver[0] - radius) / 1_000.0],
        marker="o",
        s=58,
        color="#ef8a17",
        zorder=5,
        label="UAV",
    )
    physical.set_xlabel("Local horizontal coordinate (km)")
    physical.set_ylabel("Local vertical coordinate relative to source surface tangent (km)")
    physical.set_title("Physical spherical cross-section (equal scale)")
    # Preserve one kilometre per kilometre without collapsing the axes box;
    # Matplotlib expands the visible vertical limits to the panel's shape.
    physical.set_aspect("equal", adjustable="datalim")
    physical.grid(True, alpha=0.25)
    physical.legend(loc="lower left", fontsize=8)

    sx, sh = height_xy(surface)
    gx, gh = height_xy(straight)
    rx, rh = height_xy(path)
    detail.plot(sx, sh, color="black", linewidth=2.0, label="Smooth spherical surface")
    detail.plot(
        gx, gh, color="0.45", linestyle="--", linewidth=1.6, label="Geometric straight chord"
    )
    detail.plot(rx, rh, color="#0068b5", linewidth=2.1, label="Computed refracted ray")
    detail.scatter(
        [0.0],
        [hypot(source[0], source[1]) - radius],
        marker="^",
        s=70,
        color="#c43c35",
        zorder=5,
    )
    detail.scatter(
        [radius * result.central_angle_rad / 1_000.0],
        [hypot(receiver[0], receiver[1]) - radius],
        marker="o",
        s=58,
        color="#ef8a17",
        zorder=5,
    )
    detail.axhline(0.0, color="black", linewidth=0.8)
    detail.set_xlabel("Ground arc distance (km)")
    detail.set_ylabel("Radial height above MSL sphere (m)")
    detail.set_title("Clearance diagnostic (vertical scale expanded)")
    detail.grid(True, alpha=0.25)
    detail.legend(loc="upper left", fontsize=8)

    clearance = result.diagnostics.minimum_clearance_m
    branch = result.diagnostics.branch.value if result.diagnostics.branch else "unavailable"
    figure.suptitle(
        "UAV-CAS Phase 2A: spherical atmospheric ray vs geometric chord\n"
        f"branch={branch}; minimum smooth-surface clearance={clearance:.3f} m; {profile_label}",
        fontsize=12,
    )
    figure.text(
        0.5,
        0.012,
        "Assumptions: spherical Earth, horizontally homogeneous bounded n(h), smooth absorbing surface; "
        "no EER correction, terrain, diffraction, reflection, ducting, or multipath. Right panel is vertically expanded.",
        ha="center",
        va="bottom",
        fontsize=8,
    )
    figure.tight_layout(rect=(0.0, 0.055, 1.0, 0.91), w_pad=3.0)
    figure.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(figure)
    return output_path

