"""Analytical references and the native UAV-CAS spherical ray solver."""

from .contracts import PropagationMethod, PropagationRequest, PropagationResult
from .eer_reference import EffectiveEarthRadiusReference, derive_effective_earth_k
from .geometric_reference import GeometricLosReference
from .ray_solver import trace_spherical_between, trace_uav_path
from .ray_types import (
    RayBranch,
    RayDiagnostics,
    RayPath,
    RaySolverSettings,
    RaySolveStatus,
    SphericalRayResult,
)

__all__ = [
    "EffectiveEarthRadiusReference",
    "GeometricLosReference",
    "PropagationMethod",
    "PropagationRequest",
    "PropagationResult",
    "RayBranch",
    "RayDiagnostics",
    "RayPath",
    "RaySolverSettings",
    "RaySolveStatus",
    "SphericalRayResult",
    "derive_effective_earth_k",
    "trace_spherical_between",
    "trace_uav_path",
]

