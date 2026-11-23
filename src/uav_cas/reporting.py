"""Minimal reporting-oriented UAV communication workflow.

This module composes the established atmosphere, spherical-ray, geometric
reference, and conditional P.525 link-budget APIs.  It does not add a ray
fallback, gas absorption, terrain, diffraction, fading, or availability.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from math import ceil

from .atmosphere import (
    RefractivityProfile,
    low_latitude_reference_atmosphere,
    radio_refractivity,
    standard_atmosphere,
)
from .link_budget import ReferenceLinkBudgetResult, calculate_reference_link_budget
from .models import LinkConfiguration, LinkDirection, RadioEndpoint
from .propagation import (
    GeometricLosReference,
    PropagationRequest,
    RaySolveStatus,
    trace_uav_path,
)
from .validation import finite_number, nonnegative, positive

REFERENCE_LATITUDE_DEG = 10.82
REFERENCE_LONGITUDE_DEG = 106.63
EARTH_RADIUS_M = 6_371_000.0
PROFILE_TOP_M = 20_000.0
PROFILE_SPACING_M = 25.0


class AtmosphereModel(str, Enum):
    ITU = "ITU"
    ISA = "ISA"


@dataclass(frozen=True)
class ReportingInputs:
    ground_station_height_msl_m: float = 10.0
    uav_altitude_msl_m: float = 1_000.0
    surface_distance_km: float = 50.0
    frequency_mhz: float = 2_400.0
    transmit_power_dbm: float = 30.0
    transmitter_gain_dbi: float = 2.0
    receiver_gain_dbi: float = 2.0
    tx_loss_db: float = 1.0
    rx_loss_db: float = 1.0
    receiver_sensitivity_dbm: float = -100.0
    required_margin_db: float = 0.0
    atmosphere_model: AtmosphereModel | str = AtmosphereModel.ITU
    sweep_min_km: float = 0.0
    sweep_max_km: float = 500.0
    sweep_step_km: float = 5.0

    def __post_init__(self) -> None:
        for name in (
            "ground_station_height_msl_m",
            "uav_altitude_msl_m",
            "surface_distance_km",
            "tx_loss_db",
            "rx_loss_db",
            "required_margin_db",
            "sweep_min_km",
        ):
            object.__setattr__(self, name, nonnegative(getattr(self, name), name))
        for name in ("frequency_mhz", "sweep_max_km", "sweep_step_km"):
            object.__setattr__(self, name, positive(getattr(self, name), name))
        for name in (
            "transmit_power_dbm",
            "transmitter_gain_dbi",
            "receiver_gain_dbi",
            "receiver_sensitivity_dbm",
        ):
            object.__setattr__(self, name, finite_number(getattr(self, name), name))
        try:
            model = AtmosphereModel(self.atmosphere_model)
        except (TypeError, ValueError) as exc:
            raise ValueError("atmosphere_model must be ITU or ISA") from exc
        object.__setattr__(self, "atmosphere_model", model)
        if self.uav_altitude_msl_m <= self.ground_station_height_msl_m:
            raise ValueError("UAV altitude must be above the ground-station antenna height")
        if self.uav_altitude_msl_m > PROFILE_TOP_M:
            raise ValueError("reporting build supports UAV altitudes through 20 km MSL")
        if self.sweep_max_km <= self.sweep_min_km:
            raise ValueError("sweep_max_km must exceed sweep_min_km")
        if self.sweep_max_km * 1_000.0 / EARTH_RADIUS_M >= 0.35:
            raise ValueError("sweep maximum exceeds the verified local ray-solver domain")


@dataclass(frozen=True)
class AtmosphericOutputs:
    model: str
    temperature_k: float
    pressure_pa: float
    density_kg_m3: float
    radio_refractivity_n_units: float
    refractive_index: float


@dataclass(frozen=True)
class RayOutputs:
    solver_status: str
    reason_code: str
    reason: str
    ray_branch: str | None
    minimum_clearance_m: float | None
    geometric_path_length_m: float | None
    optical_path_length_m: float | None
    excess_delay_s: float | None
    geometric_visibility: bool
    ray_visibility: bool | None


@dataclass(frozen=True)
class LinkOutputs:
    received_power_dbm: float | None
    free_space_path_loss_db: float | None
    total_losses_db: float | None
    link_margin_db: float | None
    communication_feasible: bool
    reason: str


@dataclass(frozen=True)
class DashboardState:
    """Presentation-safe summary that preserves solver status distinctions."""

    status_label: str
    status_kind: str
    explanation: str
    ray_visibility_label: str


@dataclass(frozen=True)
class ReportingResult:
    inputs: ReportingInputs
    profile: RefractivityProfile
    atmosphere: AtmosphericOutputs
    ray: object
    ray_outputs: RayOutputs
    budget: ReferenceLinkBudgetResult | None
    link_outputs: LinkOutputs


@dataclass(frozen=True)
class SweepPoint:
    surface_distance_km: float
    ray_status: str
    ray_visible: bool | None
    link_margin_db: float | None
    feasible: bool


@dataclass(frozen=True)
class MaximumConnectionResult:
    maximum_surface_distance_km: float | None
    limiting_condition: str
    limiting_reason: str
    resolution_km: float
    points: tuple[SweepPoint, ...]


def build_profile(model: AtmosphereModel | str) -> RefractivityProfile:
    selected = AtmosphereModel(model)
    if selected is AtmosphereModel.ITU:
        return RefractivityProfile.from_itu_p835_low_latitude(
            0.0, PROFILE_TOP_M, PROFILE_SPACING_M
        )
    return RefractivityProfile.from_dry_isa(0.0, PROFILE_TOP_M, PROFILE_SPACING_M)


def _atmospheric_outputs(inputs: ReportingInputs) -> AtmosphericOutputs:
    if inputs.atmosphere_model is AtmosphereModel.ITU:
        state = low_latitude_reference_atmosphere(inputs.uav_altitude_msl_m)
        refractivity = radio_refractivity(
            state.temperature_k,
            state.pressure_pa,
            vapour_pressure_hpa=state.vapour_pressure_pa / 100.0,
            humidity_basis=state.humidity_basis,
        )
    else:
        state = standard_atmosphere(inputs.uav_altitude_msl_m)
        refractivity = radio_refractivity(state.temperature_k, state.pressure_pa)
    return AtmosphericOutputs(
        model=state.model,
        temperature_k=state.temperature_k,
        pressure_pa=state.pressure_pa,
        density_kg_m3=state.density_kg_m3,
        radio_refractivity_n_units=refractivity.radio_refractivity_n_units,
        refractive_index=refractivity.refractive_index,
    )


def _link_configuration(inputs: ReportingInputs) -> LinkConfiguration:
    ground = RadioEndpoint(
        "ground station",
        inputs.transmit_power_dbm,
        inputs.transmitter_gain_dbi,
        inputs.tx_loss_db,
        0.0,
        0.0,
        -200.0,
        "reporting uplink transmitter",
        "user input",
    )
    uav = RadioEndpoint(
        "UAV",
        0.0,
        0.0,
        0.0,
        inputs.receiver_gain_dbi,
        inputs.rx_loss_db,
        inputs.receiver_sensitivity_dbm,
        "user-declared receiver mode",
        "user input; verify against the selected radio mode datasheet",
    )
    return LinkConfiguration(
        LinkDirection.UPLINK,
        inputs.frequency_mhz * 1.0e6,
        ground,
        uav,
        inputs.required_margin_db,
    )


def _analyze_with_profile(
    inputs: ReportingInputs, profile: RefractivityProfile
) -> ReportingResult:
    request = PropagationRequest(
        "ground station",
        "UAV",
        inputs.ground_station_height_msl_m,
        inputs.uav_altitude_msl_m,
        inputs.surface_distance_km * 1_000.0,
        earth_radius_m=EARTH_RADIUS_M,
        frequency_hz=inputs.frequency_mhz * 1.0e6,
    )
    ray = trace_uav_path(request, profile)
    geometric = GeometricLosReference().solve(request)
    ray_visible: bool | None
    if ray.status is RaySolveStatus.SOLVED:
        ray_visible = bool(ray.ground_clear)
    elif ray.status is RaySolveStatus.BLOCKED_WITHIN_MODEL:
        ray_visible = False
    else:
        ray_visible = None
    branch = ray.diagnostics.branch.value if ray.diagnostics.branch is not None else None
    ray_outputs = RayOutputs(
        solver_status=ray.status.value,
        reason_code=ray.reason_code,
        reason=ray.reason,
        ray_branch=branch,
        minimum_clearance_m=ray.diagnostics.minimum_clearance_m,
        geometric_path_length_m=ray.geometric_length_m,
        optical_path_length_m=ray.optical_path_length_m,
        excess_delay_s=ray.excess_delay_s,
        geometric_visibility=bool(geometric.is_visible),
        ray_visibility=ray_visible,
    )

    budget = None
    if ray_visible and ray.endpoint_chord_m is not None:
        budget = calculate_reference_link_budget(
            _link_configuration(inputs), ray.endpoint_chord_m
        )
        total_losses = (
            inputs.tx_loss_db + budget.free_space_path_loss_db + inputs.rx_loss_db
        )
        link_outputs = LinkOutputs(
            received_power_dbm=budget.received_power_dbm,
            free_space_path_loss_db=budget.free_space_path_loss_db,
            total_losses_db=total_losses,
            link_margin_db=budget.design_margin_db,
            communication_feasible=budget.meets_required_margin,
            reason=(
                "clear direct ray and required link margin met"
                if budget.meets_required_margin
                else "clear direct ray but insufficient link margin"
            ),
        )
    else:
        link_outputs = LinkOutputs(
            received_power_dbm=None,
            free_space_path_loss_db=None,
            total_losses_db=None,
            link_margin_db=None,
            communication_feasible=False,
            reason=(
                "direct ray blocked within the model"
                if ray_visible is False
                else f"link budget unavailable because ray status is {ray.status.value}"
            ),
        )
    return ReportingResult(
        inputs=inputs,
        profile=profile,
        atmosphere=_atmospheric_outputs(inputs),
        ray=ray,
        ray_outputs=ray_outputs,
        budget=budget,
        link_outputs=link_outputs,
    )


def analyze_reporting_case(inputs: ReportingInputs) -> ReportingResult:
    """Evaluate one requested reference-atmosphere reporting case."""

    return _analyze_with_profile(inputs, build_profile(inputs.atmosphere_model))


def dashboard_state(result: ReportingResult) -> DashboardState:
    """Map scientific outcomes to concise UI states without hiding uncertainty."""

    ray = result.ray_outputs
    link = result.link_outputs
    if ray.ray_visibility is None:
        return DashboardState(
            status_label="LINK STATUS UNRESOLVED",
            status_kind="unresolved",
            explanation=(
                "The direct-ray solver could not determine visibility reliably: "
                f"{ray.reason_code}. No communication feasibility is inferred."
            ),
            ray_visibility_label="Unresolved",
        )
    if ray.ray_visibility is False:
        grazing = ray.reason_code == "ground_grazing"
        return DashboardState(
            status_label="LINK UNAVAILABLE",
            status_kind="unavailable",
            explanation=(
                "The supported direct ray is grazing the smooth surface under the selected model."
                if grazing
                else "No supported unobstructed direct-ray solution exists under the selected model."
            ),
            ray_visibility_label="Grazing" if grazing else "Blocked",
        )
    if link.communication_feasible:
        return DashboardState(
            status_label="LINK AVAILABLE",
            status_kind="available",
            explanation=(
                "A clear direct ray exists, and predicted received power meets the receiver "
                "threshold plus the required fade margin."
            ),
            ray_visibility_label="Clear",
        )
    return DashboardState(
        status_label="LINK UNAVAILABLE",
        status_kind="unavailable",
        explanation=(
            "A clear direct ray exists, but predicted received power is below the receiver "
            "threshold plus the required fade margin."
        ),
        ray_visibility_label="Clear",
    )


def _sweep_point(result: ReportingResult) -> SweepPoint:
    return SweepPoint(
        surface_distance_km=result.inputs.surface_distance_km,
        ray_status=result.ray_outputs.solver_status,
        ray_visible=result.ray_outputs.ray_visibility,
        link_margin_db=result.link_outputs.link_margin_db,
        feasible=result.link_outputs.communication_feasible,
    )


def _limiting_condition(result: ReportingResult) -> tuple[str, str]:
    if result.ray_outputs.ray_visibility is False:
        return "blocked ray", result.ray_outputs.reason_code
    if result.ray_outputs.ray_visibility is None:
        return "unresolved ray status", result.ray_outputs.reason_code
    return "insufficient link margin", result.link_outputs.reason


def estimate_maximum_connection(inputs: ReportingInputs) -> MaximumConnectionResult:
    """Sweep surface distance and refine the first feasible-to-infeasible boundary.

    This is a deterministic estimate for the currently supported direct-ray
    model.  It is not an operational range, availability, or terrain result.
    """

    profile = build_profile(inputs.atmosphere_model)
    count = int(ceil((inputs.sweep_max_km - inputs.sweep_min_km) / inputs.sweep_step_km))
    distances = [
        min(inputs.sweep_max_km, inputs.sweep_min_km + index * inputs.sweep_step_km)
        for index in range(count + 1)
    ]
    if distances[-1] < inputs.sweep_max_km:
        distances.append(inputs.sweep_max_km)
    points: list[SweepPoint] = []
    last_feasible: ReportingResult | None = None
    first_failure: ReportingResult | None = None
    for distance in distances:
        candidate = _analyze_with_profile(
            replace(inputs, surface_distance_km=distance), profile
        )
        points.append(_sweep_point(candidate))
        if candidate.link_outputs.communication_feasible:
            last_feasible = candidate
        elif last_feasible is not None:
            first_failure = candidate
            break

    if last_feasible is None:
        failure = first_failure or _analyze_with_profile(
            replace(inputs, surface_distance_km=distances[0]), profile
        )
        condition, reason = _limiting_condition(failure)
        return MaximumConnectionResult(None, condition, reason, inputs.sweep_step_km, tuple(points))
    if first_failure is None:
        return MaximumConnectionResult(
            last_feasible.inputs.surface_distance_km,
            "sweep limit reached",
            "feasible through configured sweep maximum; true boundary not established",
            inputs.sweep_step_km,
            tuple(points),
        )

    lower = last_feasible.inputs.surface_distance_km
    upper = first_failure.inputs.surface_distance_km
    resolution = max(0.05, min(0.25, inputs.sweep_step_km / 10.0))
    limiting_result = first_failure
    while upper - lower > resolution:
        midpoint = 0.5 * (lower + upper)
        candidate = _analyze_with_profile(
            replace(inputs, surface_distance_km=midpoint), profile
        )
        points.append(_sweep_point(candidate))
        if candidate.link_outputs.communication_feasible:
            lower = midpoint
        else:
            upper = midpoint
            limiting_result = candidate
    condition, reason = _limiting_condition(limiting_result)
    return MaximumConnectionResult(lower, condition, reason, upper - lower, tuple(points))


def maximum_distance_label(maximum: MaximumConnectionResult) -> str:
    """Format the estimated maximum connection distance without conflating outcomes."""

    if maximum.maximum_surface_distance_km is None:
        if maximum.limiting_condition == "unresolved ray status":
            return "Unresolved"
        return "No feasible link"
    if maximum.limiting_condition in {"sweep limit reached", "unresolved ray status"}:
        return f"≥ {maximum.maximum_surface_distance_km:.2f} km"
    return f"{maximum.maximum_surface_distance_km:.2f} km"


def altitude_coverage_curve(
    inputs: ReportingInputs, altitudes_m: list[float]
) -> tuple[tuple[float, MaximumConnectionResult], ...]:
    """Return altitude versus estimated maximum feasible surface distance."""

    results = []
    for altitude in altitudes_m:
        case = replace(
            inputs,
            uav_altitude_msl_m=altitude,
            surface_distance_km=min(inputs.surface_distance_km, inputs.sweep_max_km),
        )
        results.append((altitude, estimate_maximum_connection(case)))
    return tuple(results)
