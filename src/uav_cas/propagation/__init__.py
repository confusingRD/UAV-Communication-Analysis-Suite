"""Independent analytical references and the Phase 2A ray adapter."""

from .contracts import PropagationMethod, PropagationRequest, PropagationResult
from .eer_reference import EffectiveEarthRadiusReference, derive_effective_earth_k
from .geometric_reference import GeometricLosReference
from .ray_tracing import to_neutral_profile, trace_uav_path

__all__ = [
    "EffectiveEarthRadiusReference",
    "GeometricLosReference",
    "PropagationMethod",
    "PropagationRequest",
    "PropagationResult",
    "derive_effective_earth_k",
    "to_neutral_profile",
    "trace_uav_path",
]

