"""Validated, GUI-independent UAV engineering contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .validation import finite_number, nonempty, nonnegative, positive


class HeightReference(str, Enum):
    MSL = "MSL"
    AGL = "AGL"


class LinkDirection(str, Enum):
    UPLINK = "uplink"
    DOWNLINK = "downlink"


class SolverStatus(str, Enum):
    SOLVED = "solved"
    BLOCKED_WITHIN_MODEL = "blocked_within_model"
    UNSUPPORTED_MODEL = "unsupported_model"
    UNSUPPORTED_BRANCH = "unsupported_branch"
    MISSING_DATA = "missing_data"
    NUMERICAL_FAILURE = "numerical_failure"
    INVALID_INPUT = "invalid_input"


@dataclass(frozen=True)
class ModelProvenance:
    model_id: str
    model_version: str
    source: str
    assumptions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "model_id", nonempty(self.model_id, "model_id"))
        object.__setattr__(self, "model_version", nonempty(self.model_version, "model_version"))
        object.__setattr__(self, "source", nonempty(self.source, "source"))
        if any(not isinstance(item, str) or not item.strip() for item in self.assumptions):
            raise ValueError("assumptions must contain non-empty strings")


@dataclass(frozen=True)
class AltitudeSpec:
    value_m: float
    reference: HeightReference
    ground_elevation_msl_m: float | None = None

    def __post_init__(self) -> None:
        value = finite_number(self.value_m, "value_m")
        if value < 0.0:
            raise ValueError("altitude/height must be nonnegative")
        object.__setattr__(self, "value_m", value)
        try:
            reference = HeightReference(self.reference)
        except (TypeError, ValueError) as exc:
            raise ValueError("height reference must be MSL or AGL") from exc
        object.__setattr__(self, "reference", reference)
        if reference is HeightReference.AGL:
            if self.ground_elevation_msl_m is None:
                raise ValueError("AGL height requires local ground elevation MSL")
            object.__setattr__(
                self,
                "ground_elevation_msl_m",
                finite_number(self.ground_elevation_msl_m, "ground_elevation_msl_m"),
            )
        elif self.ground_elevation_msl_m is not None:
            object.__setattr__(
                self,
                "ground_elevation_msl_m",
                finite_number(self.ground_elevation_msl_m, "ground_elevation_msl_m"),
            )

    @property
    def msl_m(self) -> float:
        if self.reference is HeightReference.MSL:
            return self.value_m
        assert self.ground_elevation_msl_m is not None
        return self.ground_elevation_msl_m + self.value_m


@dataclass(frozen=True)
class GroundStationGeometry:
    identifier: str
    ground_elevation_msl_m: float
    antenna_height_agl_m: float
    latitude_deg: float | None = None
    longitude_deg: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "identifier", nonempty(self.identifier, "identifier"))
        object.__setattr__(
            self,
            "ground_elevation_msl_m",
            finite_number(self.ground_elevation_msl_m, "ground_elevation_msl_m"),
        )
        object.__setattr__(
            self,
            "antenna_height_agl_m",
            nonnegative(self.antenna_height_agl_m, "antenna_height_agl_m"),
        )
        if (self.latitude_deg is None) != (self.longitude_deg is None):
            raise ValueError("latitude and longitude must be supplied together")
        if self.latitude_deg is not None and self.longitude_deg is not None:
            latitude = finite_number(self.latitude_deg, "latitude_deg")
            longitude = finite_number(self.longitude_deg, "longitude_deg")
            if not -90.0 <= latitude <= 90.0 or not -180.0 <= longitude <= 180.0:
                raise ValueError("latitude/longitude outside degree ranges")
            object.__setattr__(self, "latitude_deg", latitude)
            object.__setattr__(self, "longitude_deg", longitude)

    @property
    def antenna_altitude_msl_m(self) -> float:
        return self.ground_elevation_msl_m + self.antenna_height_agl_m


@dataclass(frozen=True)
class UavGeometry:
    identifier: str
    altitude: AltitudeSpec

    def __post_init__(self) -> None:
        object.__setattr__(self, "identifier", nonempty(self.identifier, "identifier"))
        if not isinstance(self.altitude, AltitudeSpec):
            raise ValueError("altitude must be an AltitudeSpec")


@dataclass(frozen=True)
class RadioEndpoint:
    identifier: str
    tx_power_dbm: float
    tx_gain_dbi: float
    tx_feeder_loss_db: float
    rx_gain_dbi: float
    rx_feeder_loss_db: float
    receiver_sensitivity_dbm: float
    receiver_mode: str
    sensitivity_source: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "identifier", nonempty(self.identifier, "identifier"))
        for field_name in (
            "tx_power_dbm",
            "tx_gain_dbi",
            "rx_gain_dbi",
            "receiver_sensitivity_dbm",
        ):
            object.__setattr__(self, field_name, finite_number(getattr(self, field_name), field_name))
        for field_name in ("tx_feeder_loss_db", "rx_feeder_loss_db"):
            object.__setattr__(self, field_name, nonnegative(getattr(self, field_name), field_name))
        object.__setattr__(self, "receiver_mode", nonempty(self.receiver_mode, "receiver_mode"))
        object.__setattr__(
            self, "sensitivity_source", nonempty(self.sensitivity_source, "sensitivity_source")
        )


@dataclass(frozen=True)
class LinkConfiguration:
    direction: LinkDirection
    frequency_hz: float
    ground_radio: RadioEndpoint
    uav_radio: RadioEndpoint
    required_fade_margin_db: float = 0.0

    def __post_init__(self) -> None:
        try:
            direction = LinkDirection(self.direction)
        except (TypeError, ValueError) as exc:
            raise ValueError("direction must be uplink or downlink") from exc
        object.__setattr__(self, "direction", direction)
        object.__setattr__(self, "frequency_hz", positive(self.frequency_hz, "frequency_hz"))
        if not isinstance(self.ground_radio, RadioEndpoint) or not isinstance(
            self.uav_radio, RadioEndpoint
        ):
            raise ValueError("ground_radio and uav_radio must be RadioEndpoint values")
        object.__setattr__(
            self,
            "required_fade_margin_db",
            nonnegative(self.required_fade_margin_db, "required_fade_margin_db"),
        )

    @property
    def transmitter(self) -> RadioEndpoint:
        return self.ground_radio if self.direction is LinkDirection.UPLINK else self.uav_radio

    @property
    def receiver(self) -> RadioEndpoint:
        return self.uav_radio if self.direction is LinkDirection.UPLINK else self.ground_radio


@dataclass(frozen=True)
class NumericalSettings:
    absolute_tolerance_m: float = 0.01
    relative_tolerance: float = 1.0e-9
    maximum_iterations: int = 100

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "absolute_tolerance_m",
            positive(self.absolute_tolerance_m, "absolute_tolerance_m"),
        )
        object.__setattr__(
            self, "relative_tolerance", positive(self.relative_tolerance, "relative_tolerance")
        )
        if isinstance(self.maximum_iterations, bool) or not isinstance(self.maximum_iterations, int):
            raise ValueError("maximum_iterations must be an integer")
        if self.maximum_iterations <= 0:
            raise ValueError("maximum_iterations must be positive")

