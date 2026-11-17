"""Geometric LOS on the physical spherical Earth (analytical reference)."""

from __future__ import annotations

from uav_cas.models import ModelProvenance, SolverStatus

from .contracts import PropagationRequest, PropagationResult
from .geometry import endpoint_chord_m, two_endpoint_horizon_surface_distance_m


class GeometricLosReference:
    method_id = "geometric-los-reference"

    def solve(self, request: PropagationRequest) -> PropagationResult:
        maximum = two_endpoint_horizon_surface_distance_m(
            request.source_height_msl_m,
            request.receiver_height_msl_m,
            earth_radius_m=request.earth_radius_m,
        )
        chord = endpoint_chord_m(
            request.source_height_msl_m,
            request.receiver_height_msl_m,
            request.surface_distance_m,
            earth_radius_m=request.earth_radius_m,
        )
        visible = request.surface_distance_m <= maximum
        return PropagationResult(
            method_id=self.method_id,
            status=SolverStatus.SOLVED if visible else SolverStatus.BLOCKED_WITHIN_MODEL,
            reason_code="geometric_los" if visible else "physical_sphere_intersection",
            is_visible=visible,
            maximum_surface_distance_m=maximum,
            endpoint_chord_m=chord,
            provenance=ModelProvenance(
                "spherical-geometric-los",
                "1.0",
                "Analytic tangent geometry on the declared physical sphere",
            ),
            assumptions=(
                "smooth spherical Earth",
                "heights are physical MSL heights above the declared sphere",
                "no terrain, obstacles, refraction, diffraction, or Fresnel clearance",
                "analytical reference; not a ray-tracing result",
            ),
        )

