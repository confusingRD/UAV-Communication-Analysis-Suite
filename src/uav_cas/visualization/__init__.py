"""Headless figure builders for scientific outputs."""

from .atmosphere import save_atmosphere_figures, save_horizon_reference_figure
from .ray_path import save_ray_path_figure
from .reporting import (
    atmosphere_profile_figure,
    communication_performance_figure,
    maximum_connection_region_figure,
    ray_cross_section_figure,
    save_figure,
)

__all__ = [
    "save_atmosphere_figures",
    "save_horizon_reference_figure",
    "save_ray_path_figure",
    "atmosphere_profile_figure",
    "communication_performance_figure",
    "maximum_connection_region_figure",
    "ray_cross_section_figure",
    "save_figure",
]

