"""Effective-Earth-radius horizon reference, isolated from ray tracing."""

from __future__ import annotations

from dataclasses import dataclass

from uav_cas.models import ModelProvenance, SolverStatus
from uav_cas.validation import finite_number, nonnegative, positive

from .contracts import PropagationRequest, PropagationResult
from .geometry import endpoint_chord_m, two_endpoint_horizon_surface_distance_m


@dataclass(frozen=True)
class DerivedEffectiveEarthRadius:
    k_factor: float
    gradient_dn_dh_per_m: float
    reference_refractive_index: float
    minimum_height_m: float
    maximum_height_m: float
    maximum_relative_gradient_variation: float
    applicability: str


def derive_effective_earth_k(
    gradient_dn_dh_per_m: float,
    *,
    reference_refractive_index: float,
    minimum_height_m: float,
    maximum_height_m: float,
    maximum_relative_gradient_variation: float,
    earth_radius_m: float = 6_371_000.0,
) -> DerivedEffectiveEarthRadius:
    """Derive k for an approximately constant vertical gradient.

    k = 1 / (1 + R/n * dn/dh). It is a local near-horizontal curvature
    approximation, not a fit to or replacement for a traced ray.
    """

    gradient = finite_number(gradient_dn_dh_per_m, "gradient_dn_dh_per_m")
    refractive_index = positive(reference_refractive_index, "reference_refractive_index")
    lower = nonnegative(minimum_height_m, "minimum_height_m")
    upper = nonnegative(maximum_height_m, "maximum_height_m")
    variation = nonnegative(
        maximum_relative_gradient_variation, "maximum_relative_gradient_variation"
    )
    radius = positive(earth_radius_m, "earth_radius_m")
    if upper <= lower:
        raise ValueError("derived-k interval must have positive height span")
    if upper - lower > 2_000.0:
        raise ValueError("derived-k Phase 1 domain is limited to a <=2 km vertical interval")
    if variation > 0.10:
        raise ValueError("gradient is not sufficiently constant for the derived-k reference")
    denominator = 1.0 + radius * gradient / refractive_index
    if denominator <= 0.0:
        raise ValueError("gradient produces a nonphysical/infinite effective radius")
    return DerivedEffectiveEarthRadius(
        k_factor=1.0 / denominator,
        gradient_dn_dh_per_m=gradient,
        reference_refractive_index=refractive_index,
        minimum_height_m=lower,
        maximum_height_m=upper,
        maximum_relative_gradient_variation=variation,
        applicability=(
            "Near-horizontal analytical reference within the declared height interval; "
            "requires an approximately constant gradient and is not ray tracing"
        ),
    )


class EffectiveEarthRadiusReference:
    method_id = "effective-earth-radius-reference"

    def __init__(
        self,
        k_factor: float = 4.0 / 3.0,
        *,
        derived: DerivedEffectiveEarthRadius | None = None,
    ) -> None:
        k = positive(k_factor, "k_factor")
        if derived is not None and abs(k - derived.k_factor) > 1.0e-12:
            raise ValueError("k_factor must agree with the supplied derived-k metadata")
        self.k_factor = k
        self.derived = derived

    def solve(self, request: PropagationRequest) -> PropagationResult:
        if self.derived is not None:
            if (
                request.source_height_msl_m < self.derived.minimum_height_m
                or request.source_height_msl_m > self.derived.maximum_height_m
                or request.receiver_height_msl_m < self.derived.minimum_height_m
                or request.receiver_height_msl_m > self.derived.maximum_height_m
            ):
                return PropagationResult(
                    method_id=self.method_id,
                    status=SolverStatus.UNSUPPORTED_MODEL,
                    reason_code="derived_k_outside_height_domain",
                    is_visible=None,
                    maximum_surface_distance_m=None,
                    endpoint_chord_m=None,
                    provenance=self._provenance(),
                    assumptions=(self.derived.applicability,),
                )
        effective_radius = self.k_factor * request.earth_radius_m
        maximum = two_endpoint_horizon_surface_distance_m(
            request.source_height_msl_m,
            request.receiver_height_msl_m,
            earth_radius_m=effective_radius,
        )
        visible = request.surface_distance_m <= maximum
        return PropagationResult(
            method_id=self.method_id,
            status=SolverStatus.SOLVED if visible else SolverStatus.BLOCKED_WITHIN_MODEL,
            reason_code="eer_visible" if visible else "eer_horizon_exceeded",
            is_visible=visible,
            maximum_surface_distance_m=maximum,
            endpoint_chord_m=endpoint_chord_m(
                request.source_height_msl_m,
                request.receiver_height_msl_m,
                request.surface_distance_m,
                earth_radius_m=request.earth_radius_m,
            ),
            provenance=self._provenance(),
            assumptions=(
                f"effective radius kR with k={self.k_factor:.12g}",
                "smooth spherical reference geometry",
                "no physical ray coordinates, optical path, delay, or attenuation",
                "analytical reference; not a ray-tracing prediction",
            ),
        )

    def _provenance(self) -> ModelProvenance:
        source = (
            self.derived.applicability
            if self.derived is not None
            else "Declared conventional constant-k effective-Earth-radius approximation"
        )
        return ModelProvenance("effective-earth-radius", "Phase1-v1", source)

