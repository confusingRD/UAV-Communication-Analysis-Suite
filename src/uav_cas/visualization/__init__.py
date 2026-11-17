"""Headless figure builders for scientific outputs."""

from .atmosphere import save_atmosphere_figures, save_horizon_reference_figure
from .ray_path import save_ray_path_figure

__all__ = [
    "save_atmosphere_figures",
    "save_horizon_reference_figure",
    "save_ray_path_figure",
]

