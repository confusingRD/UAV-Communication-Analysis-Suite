"""Unified, GUI-independent UAV communication analysis package."""

from .atmosphere.isa import AtmosphereState, AltitudeKind, standard_atmosphere
from .atmosphere.refractivity import RefractivityResult, radio_refractivity
from .link_budget import calculate_reference_link_budget, free_space_path_loss_db
from .propagation import (
    PropagationRequest,
    RayBranch,
    RaySolverSettings,
    RaySolveStatus,
    SphericalRayResult,
    trace_spherical_between,
    trace_uav_path,
)

__all__ = [
    "AltitudeKind",
    "AtmosphereState",
    "RefractivityResult",
    "PropagationRequest",
    "RayBranch",
    "RaySolverSettings",
    "RaySolveStatus",
    "SphericalRayResult",
    "calculate_reference_link_budget",
    "free_space_path_loss_db",
    "radio_refractivity",
    "standard_atmosphere",
    "trace_spherical_between",
    "trace_uav_path",
]

__version__ = "0.1.0"

