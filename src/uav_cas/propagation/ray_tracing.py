"""UAV request adapter for the additive ``cubesat_link`` spherical BVP."""

from __future__ import annotations

from math import cos, sin

from cubesat_link import NeutralProfile, RaySolverSettings, SphericalRayResult
from cubesat_link import trace_spherical_between

from uav_cas.atmosphere.profiles import RefractivityProfile

from .contracts import PropagationRequest


def to_neutral_profile(profile: RefractivityProfile) -> NeutralProfile:
    """Adapt a bounded UAV-CAS n(h) profile without extrapolation."""

    return NeutralProfile(
        height_m=profile.geometric_heights_m,
        refractive_index=profile.refractive_indices,
        source=(
            f"{profile.source}; {profile.model_version}; profile_sha256={profile.profile_hash}"
        ),
        frequency_range_hz=(1.0, 1.0e15),
        outside="unavailable",
    )


def trace_uav_path(
    request: PropagationRequest,
    profile: RefractivityProfile,
    *,
    solver_settings: RaySolverSettings | None = None,
) -> SphericalRayResult:
    """Trace a short-arc path between request endpoints over the MSL sphere.

    The request's physical Earth radius is also the smooth MSL surface radius;
    endpoint MSL heights are added to it.  EER options are intentionally absent.
    """

    central_angle = request.surface_distance_m / request.earth_radius_m
    source_radius = request.earth_radius_m + request.source_height_msl_m
    receiver_radius = request.earth_radius_m + request.receiver_height_msl_m
    source = (source_radius, 0.0, 0.0)
    receiver = (
        receiver_radius * cos(central_angle),
        receiver_radius * sin(central_angle),
        0.0,
    )
    settings = solver_settings or RaySolverSettings(
        angular_tolerance_rad=max(
            1.0e-12,
            request.settings.absolute_tolerance_m / request.earth_radius_m,
        ),
        endpoint_tolerance_m=request.settings.absolute_tolerance_m,
        maximum_iterations=request.settings.maximum_iterations,
    )
    return trace_spherical_between(
        source,
        receiver,
        request.frequency_hz,
        to_neutral_profile(profile),
        request.earth_radius_m,
        request.earth_radius_m,
        settings,
    )

