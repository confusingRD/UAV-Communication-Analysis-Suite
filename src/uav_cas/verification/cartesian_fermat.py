"""Independent Cartesian Fermat-ray reference for bounded radial profiles.

This module deliberately does not import or call the production spherical BVP
integrator.  It integrates the Cartesian ray equation

    d(n u)/ds = grad(n),  |u| = 1,

with fixed-step RK4 and performs a separate launch-elevation shoot.  It is a
verification reference, not a production fallback.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from math import atan2, cos, degrees, hypot, isfinite, radians, sin, sqrt

from uav_cas.atmosphere.profiles import RefractivityProfile
from uav_cas.propagation.contracts import PropagationRequest


@dataclass(frozen=True)
class CartesianFermatResult:
    status: str
    reason: str
    launch_elevation_deg: float | None
    endpoint_error_m: float | None
    geometric_length_m: float | None
    refractivity_excess_m: float | None
    optical_path_length_m: float | None
    shooting_iterations: int
    integration_steps: int
    step_m: float
    position_m: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class _Crossing:
    radial_residual_m: float
    length_m: float
    refractivity_excess_m: float
    steps: int
    positions: tuple[tuple[float, float], ...]


class _PiecewiseLinearProfile:
    def __init__(self, profile: RefractivityProfile, earth_radius_m: float) -> None:
        self.heights = profile.geometric_heights_m
        self.indices = profile.refractive_indices
        self.earth_radius_m = earth_radius_m

    def evaluate(self, x_m: float, y_m: float) -> tuple[float, float, float]:
        radius = hypot(x_m, y_m)
        height = radius - self.earth_radius_m
        if height < self.heights[0] or height > self.heights[-1]:
            raise ArithmeticError("reference_profile_domain")
        interval = min(
            len(self.heights) - 2,
            max(0, bisect_right(self.heights, height) - 1),
        )
        h0, h1 = self.heights[interval], self.heights[interval + 1]
        n0, n1 = self.indices[interval], self.indices[interval + 1]
        slope = (n1 - n0) / (h1 - h0)
        n_value = n0 + slope * (height - h0)
        return n_value, slope * x_m / radius, slope * y_m / radius


def _add_scaled(values: tuple[float, ...], derivative: tuple[float, ...], scale: float):
    return tuple(value + scale * delta for value, delta in zip(values, derivative))


def _integrate_to_angle(
    evaluator: _PiecewiseLinearProfile,
    request: PropagationRequest,
    elevation_deg: float,
    step_m: float,
    *,
    collect_path: bool,
) -> _Crossing | None:
    target_angle = request.surface_distance_m / request.earth_radius_m
    target_radius = request.earth_radius_m + request.receiver_height_msl_m
    source_radius = request.earth_radius_m + request.source_height_msl_m
    elevation = radians(elevation_deg)
    state = (source_radius, 0.0, sin(elevation), cos(elevation), 0.0)
    travelled = 0.0
    positions: list[tuple[float, float]] = [(state[0], state[1])]
    maximum_length = max(20_000.0, 2.0 * request.surface_distance_m + 20_000.0)
    maximum_steps = int(maximum_length / step_m) + 2

    def rhs(values: tuple[float, ...]) -> tuple[float, ...]:
        x_m, y_m, ux, uy, _ = values
        n_value, gradient_x, gradient_y = evaluator.evaluate(x_m, y_m)
        projection = ux * gradient_x + uy * gradient_y
        return (
            ux,
            uy,
            (gradient_x - ux * projection) / n_value,
            (gradient_y - uy * projection) / n_value,
            n_value - 1.0,
        )

    for step_index in range(1, maximum_steps + 1):
        previous = state
        previous_angle = atan2(previous[1], previous[0])
        try:
            first = rhs(previous)
            second = rhs(_add_scaled(previous, first, step_m / 2.0))
            third = rhs(_add_scaled(previous, second, step_m / 2.0))
            fourth = rhs(_add_scaled(previous, third, step_m))
        except ArithmeticError:
            return None
        state = tuple(
            value + step_m * (a + 2.0 * b + 2.0 * c + d) / 6.0
            for value, a, b, c, d in zip(previous, first, second, third, fourth)
        )
        tangent_norm = hypot(state[2], state[3])
        state = (state[0], state[1], state[2] / tangent_norm, state[3] / tangent_norm, state[4])
        travelled += step_m
        angle = atan2(state[1], state[0])
        if collect_path:
            positions.append((state[0], state[1]))
        if angle >= target_angle:
            denominator = angle - previous_angle
            fraction = 1.0 if denominator <= 0.0 else (target_angle - previous_angle) / denominator
            fraction = max(0.0, min(1.0, fraction))
            crossing = tuple(
                before + fraction * (after - before) for before, after in zip(previous, state)
            )
            crossing_radius = hypot(crossing[0], crossing[1])
            if collect_path:
                positions[-1] = (crossing[0], crossing[1])
            return _Crossing(
                radial_residual_m=crossing_radius - target_radius,
                length_m=travelled - step_m + fraction * step_m,
                refractivity_excess_m=crossing[4],
                steps=step_index,
                positions=tuple(positions),
            )
        if hypot(state[0], state[1]) < request.earth_radius_m:
            return None
    return None


def trace_cartesian_fermat(
    request: PropagationRequest,
    profile: RefractivityProfile,
    *,
    step_m: float = 10.0,
    endpoint_tolerance_m: float = 0.02,
    maximum_iterations: int = 50,
) -> CartesianFermatResult:
    """Shoot an independently integrated direct ray to the receiver angle."""

    if not isfinite(step_m) or step_m <= 0.0:
        raise ValueError("step_m must be positive and finite")
    if not isfinite(endpoint_tolerance_m) or endpoint_tolerance_m <= 0.0:
        raise ValueError("endpoint_tolerance_m must be positive and finite")
    if maximum_iterations <= 0:
        raise ValueError("maximum_iterations must be positive")
    if request.surface_distance_m == 0.0:
        return CartesianFermatResult(
            "unsupported", "zero-angle reference shooting is not required", None, None,
            None, None, None, 0, 0, step_m, (),
        )

    evaluator = _PiecewiseLinearProfile(profile, request.earth_radius_m)
    # Dense near-horizontal scan.  This independently brackets the direct
    # branch and does not use a production launch direction or invariant.
    candidates = [-3.0 + 0.05 * index for index in range(121)]
    candidates.extend(3.25 + 0.25 * index for index in range(48))
    samples: list[tuple[float, _Crossing]] = []
    for elevation in candidates:
        crossing = _integrate_to_angle(
            evaluator, request, elevation, step_m, collect_path=False
        )
        if crossing is not None:
            samples.append((elevation, crossing))

    bracket: tuple[float, float] | None = None
    for (left_angle, left), (right_angle, right) in zip(samples, samples[1:]):
        if left.radial_residual_m == 0.0:
            bracket = (left_angle, left_angle)
            break
        if left.radial_residual_m * right.radial_residual_m <= 0.0:
            bracket = (left_angle, right_angle)
            break
    if bracket is None:
        return CartesianFermatResult(
            "unresolved", "independent launch scan did not bracket a direct ray", None,
            None, None, None, None, 0, 0, step_m, (),
        )

    lower, upper = bracket
    best_angle = lower
    best = _integrate_to_angle(evaluator, request, best_angle, step_m, collect_path=False)
    iterations = 0
    for iterations in range(1, maximum_iterations + 1):
        best_angle = 0.5 * (lower + upper)
        best = _integrate_to_angle(evaluator, request, best_angle, step_m, collect_path=False)
        if best is None:
            lower = best_angle
            continue
        if abs(best.radial_residual_m) <= endpoint_tolerance_m:
            break
        lower_crossing = _integrate_to_angle(
            evaluator, request, lower, step_m, collect_path=False
        )
        if lower_crossing is None or lower_crossing.radial_residual_m * best.radial_residual_m <= 0.0:
            upper = best_angle
        else:
            lower = best_angle
    if best is None or abs(best.radial_residual_m) > endpoint_tolerance_m:
        return CartesianFermatResult(
            "unresolved", "independent shooting tolerance was not met", best_angle,
            None if best is None else abs(best.radial_residual_m), None, None, None,
            iterations, 0 if best is None else best.steps, step_m, (),
        )
    final = _integrate_to_angle(evaluator, request, best_angle, step_m, collect_path=True)
    assert final is not None
    return CartesianFermatResult(
        status="solved",
        reason="independent Cartesian RK4 Fermat shoot converged",
        launch_elevation_deg=best_angle,
        endpoint_error_m=abs(final.radial_residual_m),
        geometric_length_m=final.length_m,
        refractivity_excess_m=final.refractivity_excess_m,
        optical_path_length_m=final.length_m + final.refractivity_excess_m,
        shooting_iterations=iterations,
        integration_steps=final.steps,
        step_m=step_m,
        position_m=final.positions,
    )
