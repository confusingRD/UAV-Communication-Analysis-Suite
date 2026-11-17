"""Immutable, bounded, piecewise-linear refractivity profiles."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from math import isfinite
from typing import Iterable, Sequence

from uav_cas.validation import finite_number, positive

from .isa import AltitudeKind, AtmosphereState, standard_atmosphere
from .refractivity import radio_refractivity


class ProfileStatus(str, Enum):
    AVAILABLE = "available"
    MISSING_DATA = "missing_data"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class ProfileEvaluation:
    status: ProfileStatus
    height_m: float
    refractive_index: float | None
    radio_refractivity_n_units: float | None
    reason: str


@dataclass(frozen=True)
class RefractivityProfile:
    geometric_heights_m: tuple[float, ...]
    refractive_indices: tuple[float, ...]
    radio_refractivities_n_units: tuple[float, ...]
    source: str
    model_version: str
    humidity_basis: str
    interpolation: str = "piecewise-linear"
    boundary_policy: str = "unavailable"
    horizontal_assumption: str = "horizontally homogeneous"
    thermodynamic_states: tuple[AtmosphereState, ...] = ()

    def __post_init__(self) -> None:
        heights = tuple(finite_number(v, "geometric_height_m") for v in self.geometric_heights_m)
        indices = tuple(positive(v, "refractive_index") for v in self.refractive_indices)
        n_units = tuple(finite_number(v, "radio_refractivity_n_units") for v in self.radio_refractivities_n_units)
        if len(heights) < 2 or len(indices) != len(heights) or len(n_units) != len(heights):
            raise ValueError("profile requires at least two equally sized height, n, and N arrays")
        if any(b <= a for a, b in zip(heights, heights[1:])):
            raise ValueError("profile heights must be strictly increasing")
        if self.interpolation != "piecewise-linear" or self.boundary_policy != "unavailable":
            raise ValueError("Phase 1 supports piecewise-linear interpolation with unavailable boundaries")
        if any(abs((1.0 + n_value * 1e-6) - index) > 5e-13 for index, n_value in zip(indices, n_units)):
            raise ValueError("refractive index and N arrays are inconsistent")
        if self.thermodynamic_states and len(self.thermodynamic_states) != len(heights):
            raise ValueError("thermodynamic states must be empty or aligned with profile samples")
        if not self.source.strip() or not self.model_version.strip() or not self.humidity_basis.strip():
            raise ValueError("profile provenance and humidity basis are required")
        object.__setattr__(self, "geometric_heights_m", heights)
        object.__setattr__(self, "refractive_indices", indices)
        object.__setattr__(self, "radio_refractivities_n_units", n_units)

    @classmethod
    def from_dry_isa(
        cls,
        minimum_geometric_m: float,
        maximum_geometric_m: float,
        spacing_m: float,
    ) -> "RefractivityProfile":
        lower = finite_number(minimum_geometric_m, "minimum_geometric_m")
        upper = finite_number(maximum_geometric_m, "maximum_geometric_m")
        spacing = positive(spacing_m, "spacing_m")
        if lower < 0.0 or upper <= lower:
            raise ValueError("profile bounds must satisfy 0 <= minimum < maximum")
        heights: list[float] = []
        current = lower
        while current < upper:
            heights.append(current)
            current += spacing
        heights.append(upper)
        states = tuple(standard_atmosphere(height, AltitudeKind.GEOMETRIC) for height in heights)
        refractivity = tuple(
            radio_refractivity(state.temperature_k, state.pressure_pa) for state in states
        )
        return cls(
            geometric_heights_m=tuple(heights),
            refractive_indices=tuple(item.refractive_index for item in refractivity),
            radio_refractivities_n_units=tuple(
                item.radio_refractivity_n_units for item in refractivity
            ),
            source="Dry ISA-1976 thermodynamic states with ITU-R P.453-14 refractivity",
            model_version="UAV-CAS dry-ISA/P.453 profile v1",
            humidity_basis="dry-air reference; e=0 is an assumption, not a measurement",
            thermodynamic_states=states,
        )

    @classmethod
    def from_samples(
        cls,
        geometric_heights_m: Sequence[float],
        refractive_indices: Sequence[float],
        *,
        source: str,
        model_version: str,
        humidity_basis: str,
    ) -> "RefractivityProfile":
        indices = tuple(refractive_indices)
        return cls(
            geometric_heights_m=tuple(geometric_heights_m),
            refractive_indices=indices,
            radio_refractivities_n_units=tuple((value - 1.0) * 1.0e6 for value in indices),
            source=source,
            model_version=model_version,
            humidity_basis=humidity_basis,
        )

    @property
    def minimum_height_m(self) -> float:
        return self.geometric_heights_m[0]

    @property
    def maximum_height_m(self) -> float:
        return self.geometric_heights_m[-1]

    @property
    def profile_hash(self) -> str:
        payload = {
            "heights_m": self.geometric_heights_m,
            "n": self.refractive_indices,
            "source": self.source,
            "model_version": self.model_version,
            "humidity_basis": self.humidity_basis,
            "interpolation": self.interpolation,
            "boundary_policy": self.boundary_policy,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return sha256(encoded).hexdigest()

    def _interval(self, height_m: float, side: str = "right") -> int | None:
        height = finite_number(height_m, "height_m")
        if height < self.minimum_height_m or height > self.maximum_height_m:
            return None
        if side not in ("left", "right"):
            raise ValueError("gradient side must be 'left' or 'right'")
        heights = self.geometric_heights_m
        if height == heights[-1]:
            return len(heights) - 2
        for index, (lower, upper) in enumerate(zip(heights, heights[1:])):
            if lower < height < upper:
                return index
            if height == lower:
                return max(0, index - 1) if side == "left" and index > 0 else index
        return len(heights) - 2

    def evaluate(self, height_m: float) -> ProfileEvaluation:
        height = finite_number(height_m, "height_m")
        interval = self._interval(height)
        if interval is None:
            return ProfileEvaluation(
                ProfileStatus.MISSING_DATA,
                height,
                None,
                None,
                f"height outside bounded profile [{self.minimum_height_m}, {self.maximum_height_m}] m",
            )
        h0 = self.geometric_heights_m[interval]
        h1 = self.geometric_heights_m[interval + 1]
        fraction = (height - h0) / (h1 - h0)
        n0 = self.refractive_indices[interval]
        n1 = self.refractive_indices[interval + 1]
        n_value = n0 + fraction * (n1 - n0)
        return ProfileEvaluation(
            ProfileStatus.AVAILABLE,
            height,
            n_value,
            (n_value - 1.0) * 1.0e6,
            "bounded piecewise-linear interpolation",
        )

    def gradient_at(self, height_m: float, *, side: str = "right") -> float | None:
        """Return dn/dh in 1/m, or None outside the bounded profile."""

        interval = self._interval(height_m, side)
        if interval is None:
            return None
        return (
            self.refractive_indices[interval + 1] - self.refractive_indices[interval]
        ) / (
            self.geometric_heights_m[interval + 1] - self.geometric_heights_m[interval]
        )

