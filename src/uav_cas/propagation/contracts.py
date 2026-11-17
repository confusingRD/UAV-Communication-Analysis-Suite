"""Common immutable contracts for independent propagation methods."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from uav_cas.models import ModelProvenance, NumericalSettings, SolverStatus
from uav_cas.validation import nonempty, nonnegative, positive


@dataclass(frozen=True)
class PropagationRequest:
    source_id: str
    receiver_id: str
    source_height_msl_m: float
    receiver_height_msl_m: float
    surface_distance_m: float
    earth_radius_m: float = 6_371_000.0
    frequency_hz: float = 2.4e9
    settings: NumericalSettings = NumericalSettings()

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", nonempty(self.source_id, "source_id"))
        object.__setattr__(self, "receiver_id", nonempty(self.receiver_id, "receiver_id"))
        if self.source_id == self.receiver_id:
            raise ValueError("source and receiver identifiers must differ")
        for field_name in (
            "source_height_msl_m",
            "receiver_height_msl_m",
            "surface_distance_m",
        ):
            value = nonnegative(getattr(self, field_name), field_name)
            object.__setattr__(self, field_name, value)
        for field_name in ("earth_radius_m", "frequency_hz"):
            value = positive(getattr(self, field_name), field_name)
            object.__setattr__(self, field_name, value)
        if not isinstance(self.settings, NumericalSettings):
            raise ValueError("settings must be NumericalSettings")


@dataclass(frozen=True)
class PropagationResult:
    method_id: str
    status: SolverStatus
    reason_code: str
    is_visible: bool | None
    maximum_surface_distance_m: float | None
    endpoint_chord_m: float | None
    provenance: ModelProvenance
    assumptions: tuple[str, ...]
    physical_ray_path_available: bool = False
    optical_path_length_m: float | None = None
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "method_id", nonempty(self.method_id, "method_id"))
        object.__setattr__(self, "reason_code", nonempty(self.reason_code, "reason_code"))
        if not isinstance(self.status, SolverStatus):
            raise ValueError("status must be SolverStatus")
        if not isinstance(self.provenance, ModelProvenance):
            raise ValueError("provenance must be ModelProvenance")
        if self.physical_ray_path_available or self.optical_path_length_m is not None:
            raise ValueError("Phase 1 analytical references cannot claim a physical ray path or OPL")


@runtime_checkable
class PropagationMethod(Protocol):
    method_id: str

    def solve(self, request: PropagationRequest) -> PropagationResult: ...

