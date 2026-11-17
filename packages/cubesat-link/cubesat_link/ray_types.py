"""Immutable contracts for the additive spherical endpoint ray solver.

The legacy :mod:`cubesat_link.neutral` contracts remain unchanged.  These
types deliberately distinguish a solved physical ray from blockage,
unsupported physics, missing profile data, and numerical failure.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite


class RaySolveStatus(str, Enum):
    SOLVED = "solved"
    BLOCKED_WITHIN_MODEL = "blocked_within_model"
    UNSUPPORTED_MODEL = "unsupported_model"
    UNSUPPORTED_BRANCH = "unsupported_branch"
    MISSING_DATA = "missing_data"
    NUMERICAL_FAILURE = "numerical_failure"
    INVALID_INPUT = "invalid_input"


class RayBranch(str, Enum):
    RADIAL = "radial"
    RADIAL_MONOTONIC = "radial_monotonic"
    SINGLE_MINIMUM = "single_minimum"


@dataclass(frozen=True)
class RaySolverSettings:
    """Numerical controls kept separate from path-plot sampling."""

    angular_tolerance_rad: float = 1.0e-10
    endpoint_tolerance_m: float = 0.1
    quadrature_angle_tolerance_rad: float = 2.0e-12
    quadrature_length_tolerance_m: float = 2.0e-5
    quadrature_refractivity_tolerance_m: float = 2.0e-8
    maximum_iterations: int = 80
    maximum_quadrature_depth: int = 20
    path_sample_count: int = 401
    grazing_tolerance_m: float = 0.05
    maximum_central_angle_rad: float = 0.35

    def __post_init__(self) -> None:
        for name in (
            "angular_tolerance_rad",
            "endpoint_tolerance_m",
            "quadrature_angle_tolerance_rad",
            "quadrature_length_tolerance_m",
            "quadrature_refractivity_tolerance_m",
            "grazing_tolerance_m",
            "maximum_central_angle_rad",
        ):
            value = getattr(self, name)
            if type(value) not in (int, float) or not isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be a positive finite number")
        for name in ("maximum_iterations", "maximum_quadrature_depth", "path_sample_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.path_sample_count < 5:
            raise ValueError("path_sample_count must be at least 5")
        if self.maximum_central_angle_rad >= 3.141592653589793:
            raise ValueError("maximum_central_angle_rad must be less than pi")


@dataclass(frozen=True)
class RayPath:
    arc_length_m: tuple[float, ...]
    position_m: tuple[tuple[float, float, float], ...]
    radial_height_m: tuple[float, ...]
    source_tangent: tuple[float, float, float]
    receiver_incident_tangent: tuple[float, float, float]
    source_elevation_deg: float
    receiver_incident_elevation_deg: float
    receiver_look_elevation_deg: float

    def __post_init__(self) -> None:
        count = len(self.arc_length_m)
        if count < 2 or len(self.position_m) != count or len(self.radial_height_m) != count:
            raise ValueError("ray path arrays must have equal length >= 2")
        if any(b < a for a, b in zip(self.arc_length_m, self.arc_length_m[1:])):
            raise ValueError("ray path arc length must be nondecreasing")


@dataclass(frozen=True)
class RayDiagnostics:
    branch: RayBranch | None
    root_iterations: int
    root_parameter_name: str | None
    root_bracket: tuple[float, float] | None
    angular_endpoint_residual_rad: float | None
    cartesian_endpoint_error_m: float | None
    invariant_max_relative_error: float | None
    quadrature_evaluations: int
    quadrature_error_estimate: tuple[float, float, float] | None
    minimum_clearance_m: float | None
    clearance_uncertainty_m: float | None
    q_derivative_minimum: float | None
    path_sample_count: int
    supported_family: str


@dataclass(frozen=True)
class SphericalRayResult:
    status: RaySolveStatus
    reason_code: str
    reason: str
    source_position_m: tuple[float, float, float]
    receiver_position_m: tuple[float, float, float]
    earth_radius_m: float
    surface_radius_m: float
    frequency_hz: float
    central_angle_rad: float | None
    endpoint_chord_m: float | None
    invariant_b_m: float | None
    geometric_length_m: float | None
    refractivity_excess_m: float | None
    optical_path_length_m: float | None
    vacuum_travel_time_s: float | None
    travel_time_s: float | None
    excess_delay_s: float | None
    ground_clear: bool | None
    path: RayPath | None
    diagnostics: RayDiagnostics
    assumptions: tuple[str, ...]

