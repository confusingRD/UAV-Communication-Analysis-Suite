"""Bounded nonducting spherical boundary-value rays between two endpoints.

This additive solver extends, but does not change, ``neutral.trace_spherical``.
It reuses the verified Bouguer-invariant formulation, profile-knot splitting,
square-root regularisation, and bounded bisection strategy from that routine.
The supported family is deliberately narrow: short-arc rays in a spherically
stratified, piecewise-linear profile for which q(r)=n(r)r is strictly
increasing, with either monotonic radius or one radial minimum.  Atmospheric
turning/ducting and multiple-eigenray searches are reported as unsupported.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import acos, asin, cos, degrees, isfinite, sin, sqrt

from .neutral import NeutralProfile
from .ray_types import (
    RayBranch,
    RayDiagnostics,
    RayPath,
    RaySolverSettings,
    RaySolveStatus,
    SphericalRayResult,
)
from .types import C


Vector = tuple[float, float, float]
_SUPPORTED_FAMILY = (
    "short-arc, spherical, horizontally stratified, strictly increasing q=n*r; "
    "radial-monotonic or one lower radial minimum; no ducts/multipath"
)
_ASSUMPTIONS = (
    "spherical symmetry and horizontally homogeneous refractive index n(h)",
    "piecewise-linear bounded profile; no extrapolation",
    "smooth absorbing spherical ground; no terrain, diffraction, reflection, or multipath",
    "phase index treated as nondispersive for optical travel time",
    "physical Earth radius used; no effective-Earth-radius correction",
)


def _dot(a: Vector, b: Vector) -> float:
    return sum(x * y for x, y in zip(a, b))


def _norm(a: Vector) -> float:
    return sqrt(_dot(a, a))


def _scale(a: Vector, value: float) -> Vector:
    return tuple(value * x for x in a)  # type: ignore[return-value]


def _add(a: Vector, b: Vector) -> Vector:
    return tuple(x + y for x, y in zip(a, b))  # type: ignore[return-value]


def _sub(a: Vector, b: Vector) -> Vector:
    return tuple(x - y for x, y in zip(a, b))  # type: ignore[return-value]


def _unit(a: Vector) -> Vector:
    length = _norm(a)
    if length == 0:
        raise ValueError("zero vector has no direction")
    return _scale(a, 1.0 / length)


@dataclass
class _QuadratureStats:
    evaluations: int = 0
    error_angle: float = 0.0
    error_length: float = 0.0
    error_refractivity: float = 0.0

    def add_error(self, error: tuple[float, float, float]) -> None:
        self.error_angle += error[0]
        self.error_length += error[1]
        self.error_refractivity += error[2]


def _adaptive_simpson_vector(
    function,
    lower: float,
    upper: float,
    tolerances: tuple[float, float, float],
    depth: int,
    stats: _QuadratureStats,
) -> tuple[float, float, float]:
    """Diagnostic form of the vector Simpson integrator used by neutral.py."""

    if upper == lower:
        return (0.0, 0.0, 0.0)

    def evaluate(value: float) -> tuple[float, float, float]:
        stats.evaluations += 1
        result = function(value)
        if not all(isfinite(item) for item in result):
            raise ArithmeticError("nonfinite_integrand")
        return result

    def simpson(
        a: float,
        b: float,
        fa: tuple[float, float, float],
        fm: tuple[float, float, float],
        fb: tuple[float, float, float],
    ) -> tuple[float, float, float]:
        return tuple((b - a) * (x + 4.0 * y + z) / 6.0 for x, y, z in zip(fa, fm, fb))  # type: ignore[return-value]

    def recurse(a, b, fa, fm, fb, whole, tol, remaining):
        middle = 0.5 * (a + b)
        left_mid = evaluate(0.5 * (a + middle))
        right_mid = evaluate(0.5 * (middle + b))
        left = simpson(a, middle, fa, left_mid, fm)
        right = simpson(middle, b, fm, right_mid, fb)
        delta = tuple(x + y - z for x, y, z in zip(left, right, whole))
        if all(abs(value) <= 15.0 * target for value, target in zip(delta, tol)):
            error = tuple(abs(value) / 15.0 for value in delta)
            stats.add_error(error)  # type: ignore[arg-type]
            return tuple(x + y + value / 15.0 for x, y, value in zip(left, right, delta))
        if remaining == 0:
            raise ArithmeticError("quadrature_limit")
        half_tol = tuple(value / 2.0 for value in tol)
        left_value = recurse(a, middle, fa, left_mid, fm, left, half_tol, remaining - 1)
        right_value = recurse(middle, b, fm, right_mid, fb, right, half_tol, remaining - 1)
        return tuple(x + y for x, y in zip(left_value, right_value))

    fa = evaluate(lower)
    fm = evaluate(0.5 * (lower + upper))
    fb = evaluate(upper)
    return recurse(
        lower,
        upper,
        fa,
        fm,
        fb,
        simpson(lower, upper, fa, fm, fb),
        tolerances,
        depth,
    )


def _profile_at(profile: NeutralProfile, radius_m: float, earth_radius_m: float):
    return profile.at(radius_m - earth_radius_m)


def _q(profile: NeutralProfile, radius_m: float, earth_radius_m: float) -> float:
    return _profile_at(profile, radius_m, earth_radius_m)[0] * radius_m


def _split_radii(
    profile: NeutralProfile,
    earth_radius_m: float,
    lower_m: float,
    upper_m: float,
) -> list[float]:
    return sorted(
        set(
            [lower_m, upper_m]
            + [
                earth_radius_m + height
                for height in profile.height_m
                if lower_m < earth_radius_m + height < upper_m
            ]
        )
    )


def _integrate_range(
    profile: NeutralProfile,
    earth_radius_m: float,
    base_radius_m: float,
    lower_radius_m: float,
    upper_radius_m: float,
    invariant_b_m: float,
    tangent_at_base: bool,
    settings: RaySolverSettings,
    stats: _QuadratureStats,
) -> tuple[float, float, float]:
    """Integrate phi, ds, and (n-1)ds over increasing radius."""

    if upper_radius_m <= lower_radius_m:
        return (0.0, 0.0, 0.0)
    pieces = _split_radii(profile, earth_radius_m, lower_radius_m, upper_radius_m)
    tolerances = (
        settings.quadrature_angle_tolerance_rad / max(1, len(pieces) - 1),
        settings.quadrature_length_tolerance_m / max(1, len(pieces) - 1),
        settings.quadrature_refractivity_tolerance_m / max(1, len(pieces) - 1),
    )
    base_n, base_slope, _ = _profile_at(profile, base_radius_m, earth_radius_m)
    base_q = base_n * base_radius_m
    base_q_prime = base_n + base_radius_m * base_slope
    if tangent_at_base and base_q_prime <= 0:
        raise ArithmeticError("nonmonotonic_q")
    result = [0.0, 0.0, 0.0]

    def integrand(t_value: float) -> tuple[float, float, float]:
        radius = base_radius_m + t_value * t_value
        n_value, slope, _ = _profile_at(profile, radius, earth_radius_m)
        q_value = n_value * radius
        if t_value == 0.0:
            if not tangent_at_base:
                return (0.0, 0.0, 0.0)
            common = 2.0 * invariant_b_m / sqrt(2.0 * invariant_b_m * base_q_prime)
            return (
                common / base_radius_m,
                common,
                common * (base_n - 1.0),
            )
        difference = q_value - invariant_b_m
        if tangent_at_base:
            predicted_n = base_n + base_slope * (radius - base_radius_m)
            if abs(predicted_n - n_value) <= 2.0e-14:
                difference = (
                    (base_n + base_radius_m * base_slope) * t_value * t_value
                    + base_slope * t_value**4
                )
        radicand = difference * (q_value + invariant_b_m)
        if radicand <= 0.0:
            raise ArithmeticError("imaginary_radial_branch")
        denominator = sqrt(radicand)
        ds_dt = 2.0 * t_value * q_value / denominator
        return (
            2.0 * t_value * invariant_b_m / (radius * denominator),
            ds_dt,
            ds_dt * (n_value - 1.0),
        )

    for lower, upper in zip(pieces, pieces[1:]):
        part = _adaptive_simpson_vector(
            integrand,
            sqrt(max(0.0, lower - base_radius_m)),
            sqrt(max(0.0, upper - base_radius_m)),
            tolerances,
            settings.maximum_quadrature_depth,
            stats,
        )
        result = [x + y for x, y in zip(result, part)]
    return tuple(result)  # type: ignore[return-value]


def _q_derivative_minimum(
    profile: NeutralProfile,
    earth_radius_m: float,
    lower_radius_m: float,
    upper_radius_m: float,
) -> float:
    minimum = float("inf")
    for lower, upper in zip(
        _split_radii(profile, earth_radius_m, lower_radius_m, upper_radius_m),
        _split_radii(profile, earth_radius_m, lower_radius_m, upper_radius_m)[1:],
    ):
        midpoint = 0.5 * (lower + upper)
        n_mid, slope, _ = _profile_at(profile, midpoint, earth_radius_m)
        for radius in (lower, upper):
            n_value = n_mid + slope * (radius - midpoint)
            minimum = min(minimum, n_value + radius * slope)
    if minimum == float("inf"):
        n_value, slope, _ = _profile_at(profile, lower_radius_m, earth_radius_m)
        minimum = n_value + lower_radius_m * slope
    return minimum


def _failure_diagnostics(
    settings: RaySolverSettings,
    *,
    branch: RayBranch | None = None,
    iterations: int = 0,
    parameter: str | None = None,
    bracket: tuple[float, float] | None = None,
    angular_residual: float | None = None,
    endpoint_error: float | None = None,
    stats: _QuadratureStats | None = None,
    clearance: float | None = None,
    q_derivative_minimum: float | None = None,
) -> RayDiagnostics:
    return RayDiagnostics(
        branch=branch,
        root_iterations=iterations,
        root_parameter_name=parameter,
        root_bracket=bracket,
        angular_endpoint_residual_rad=angular_residual,
        cartesian_endpoint_error_m=endpoint_error,
        invariant_max_relative_error=None,
        quadrature_evaluations=0 if stats is None else stats.evaluations,
        quadrature_error_estimate=None
        if stats is None
        else (stats.error_angle, stats.error_length, stats.error_refractivity),
        minimum_clearance_m=clearance,
        clearance_uncertainty_m=None,
        q_derivative_minimum=q_derivative_minimum,
        path_sample_count=0,
        supported_family=_SUPPORTED_FAMILY,
    )


def _failure(
    status: RaySolveStatus,
    reason_code: str,
    reason: str,
    source: Vector,
    receiver: Vector,
    earth_radius_m: float,
    surface_radius_m: float,
    frequency_hz: float,
    diagnostics: RayDiagnostics,
    *,
    central_angle_rad: float | None = None,
    endpoint_chord_m: float | None = None,
) -> SphericalRayResult:
    return SphericalRayResult(
        status=status,
        reason_code=reason_code,
        reason=reason,
        source_position_m=source,
        receiver_position_m=receiver,
        earth_radius_m=earth_radius_m,
        surface_radius_m=surface_radius_m,
        frequency_hz=frequency_hz,
        central_angle_rad=central_angle_rad,
        endpoint_chord_m=endpoint_chord_m,
        invariant_b_m=None,
        geometric_length_m=None,
        refractivity_excess_m=None,
        optical_path_length_m=None,
        vacuum_travel_time_s=None if endpoint_chord_m is None else endpoint_chord_m / C,
        travel_time_s=None,
        excess_delay_s=None,
        ground_clear=None,
        path=None,
        diagnostics=diagnostics,
        assumptions=_ASSUMPTIONS,
    )


def _leg_samples(
    profile: NeutralProfile,
    earth_radius_m: float,
    base_radius_m: float,
    end_radius_m: float,
    invariant_b_m: float,
    tangent_at_base: bool,
    count: int,
    settings: RaySolverSettings,
    stats: _QuadratureStats,
) -> tuple[list[float], list[float], list[float]]:
    if end_radius_m == base_radius_m:
        return [base_radius_m], [0.0], [0.0]
    fractions = [index / (count - 1) for index in range(count)]
    radii = [base_radius_m + (end_radius_m - base_radius_m) * value * value for value in fractions]
    angles = [0.0]
    lengths = [0.0]
    for lower, upper in zip(radii, radii[1:]):
        angle, length, _ = _integrate_range(
            profile,
            earth_radius_m,
            base_radius_m,
            lower,
            upper,
            invariant_b_m,
            tangent_at_base,
            settings,
            stats,
        )
        angles.append(angles[-1] + angle)
        lengths.append(lengths[-1] + length)
    return radii, angles, lengths


def _plane_basis(source: Vector, receiver: Vector, central_angle: float) -> tuple[Vector, Vector]:
    radial = _unit(source)
    sine = sin(central_angle)
    if abs(sine) > 1.0e-14:
        transverse = _unit(_sub(_unit(receiver), _scale(radial, cos(central_angle))))
        return radial, transverse
    trial: Vector = (0.0, 0.0, 1.0) if abs(radial[2]) < 0.9 else (0.0, 1.0, 0.0)
    transverse = _unit(_sub(trial, _scale(radial, _dot(trial, radial))))
    return radial, transverse


def _position(radial_basis: Vector, transverse_basis: Vector, radius: float, angle: float) -> Vector:
    return _scale(
        _add(_scale(radial_basis, cos(angle)), _scale(transverse_basis, sin(angle))),
        radius,
    )


def _tangent(
    radial_basis: Vector,
    transverse_basis: Vector,
    radius: float,
    angle: float,
    invariant_b_m: float,
    q_value: float,
    radial_sign: float,
) -> Vector:
    er = _add(_scale(radial_basis, cos(angle)), _scale(transverse_basis, sin(angle)))
    ephi = _add(_scale(radial_basis, -sin(angle)), _scale(transverse_basis, cos(angle)))
    tangential = max(0.0, min(1.0, invariant_b_m / q_value))
    radial = radial_sign * sqrt(max(0.0, 1.0 - tangential * tangential))
    return _unit(_add(_scale(er, radial), _scale(ephi, tangential)))


def _invariant_sampling_error(
    positions: list[Vector],
    invariant_b_m: float,
    profile: NeutralProfile,
    earth_radius_m: float,
) -> float:
    if invariant_b_m == 0.0 or len(positions) < 3:
        return 0.0
    worst = 0.0
    for index in range(1, len(positions) - 1):
        before, point, after = positions[index - 1], positions[index], positions[index + 1]
        chord = _sub(after, before)
        if _norm(chord) == 0.0:
            continue
        tangent = _unit(chord)
        radius = _norm(point)
        er = _scale(point, 1.0 / radius)
        tangential = sqrt(max(0.0, 1.0 - _dot(tangent, er) ** 2))
        sampled_b = _profile_at(profile, radius, earth_radius_m)[0] * radius * tangential
        worst = max(worst, abs(sampled_b - invariant_b_m) / invariant_b_m)
    return worst


def _build_path(
    source: Vector,
    receiver: Vector,
    central_angle: float,
    computed_angle: float,
    source_radius: float,
    receiver_radius: float,
    minimum_radius: float,
    invariant_b_m: float,
    branch: RayBranch,
    profile: NeutralProfile,
    earth_radius_m: float,
    settings: RaySolverSettings,
    stats: _QuadratureStats,
) -> tuple[RayPath, float]:
    radial_basis, transverse_basis = _plane_basis(source, receiver, central_angle)
    count = settings.path_sample_count

    if branch is RayBranch.RADIAL:
        radii = [
            source_radius + (receiver_radius - source_radius) * index / (count - 1)
            for index in range(count)
        ]
        angles = [0.0] * count
        lengths = [abs(radius - source_radius) for radius in radii]
        source_sign = 1.0 if receiver_radius > source_radius else -1.0
        receiver_sign = source_sign
    elif branch is RayBranch.RADIAL_MONOTONIC:
        low, high = sorted((source_radius, receiver_radius))
        canonical_r, canonical_a, canonical_s = _leg_samples(
            profile,
            earth_radius_m,
            low,
            high,
            invariant_b_m,
            invariant_b_m == _q(profile, low, earth_radius_m),
            count,
            settings,
            stats,
        )
        if source_radius <= receiver_radius:
            radii, angles, lengths = canonical_r, canonical_a, canonical_s
            source_sign = receiver_sign = 1.0
        else:
            total_angle, total_length = canonical_a[-1], canonical_s[-1]
            radii = list(reversed(canonical_r))
            angles = [total_angle - value for value in reversed(canonical_a)]
            lengths = [total_length - value for value in reversed(canonical_s)]
            source_sign = receiver_sign = -1.0
    else:
        source_span = source_radius - minimum_radius
        receiver_span = receiver_radius - minimum_radius
        total_span = source_span + receiver_span
        source_count = max(2, round((count + 1) * source_span / total_span))
        receiver_count = max(2, count + 1 - source_count)
        source_r, source_a, source_s = _leg_samples(
            profile,
            earth_radius_m,
            minimum_radius,
            source_radius,
            invariant_b_m,
            True,
            source_count,
            settings,
            stats,
        )
        receiver_r, receiver_a, receiver_s = _leg_samples(
            profile,
            earth_radius_m,
            minimum_radius,
            receiver_radius,
            invariant_b_m,
            True,
            receiver_count,
            settings,
            stats,
        )
        source_angle, source_length = source_a[-1], source_s[-1]
        radii = list(reversed(source_r)) + receiver_r[1:]
        angles = [source_angle - value for value in reversed(source_a)] + [
            source_angle + value for value in receiver_a[1:]
        ]
        lengths = [source_length - value for value in reversed(source_s)] + [
            source_length + value for value in receiver_s[1:]
        ]
        source_sign, receiver_sign = -1.0, 1.0

    positions = [
        _position(radial_basis, transverse_basis, radius, angle)
        for radius, angle in zip(radii, angles)
    ]
    source_tangent = _tangent(
        radial_basis,
        transverse_basis,
        source_radius,
        0.0,
        invariant_b_m,
        _q(profile, source_radius, earth_radius_m),
        source_sign,
    )
    receiver_tangent = _tangent(
        radial_basis,
        transverse_basis,
        receiver_radius,
        computed_angle,
        invariant_b_m,
        _q(profile, receiver_radius, earth_radius_m),
        receiver_sign,
    )
    source_er = _unit(source)
    reconstructed_receiver = positions[-1]
    receiver_er = _unit(reconstructed_receiver)
    source_elevation = degrees(asin(max(-1.0, min(1.0, _dot(source_tangent, source_er)))))
    incident_elevation = degrees(
        asin(max(-1.0, min(1.0, _dot(receiver_tangent, receiver_er))))
    )
    path = RayPath(
        arc_length_m=tuple(lengths),
        position_m=tuple(positions),
        radial_height_m=tuple(radius - earth_radius_m for radius in radii),
        source_tangent=source_tangent,
        receiver_incident_tangent=receiver_tangent,
        source_elevation_deg=source_elevation,
        receiver_incident_elevation_deg=incident_elevation,
        receiver_look_elevation_deg=-incident_elevation,
    )
    return path, _invariant_sampling_error(positions, invariant_b_m, profile, earth_radius_m)


def trace_spherical_between(
    source_position_m: Vector,
    receiver_position_m: Vector,
    frequency_hz: float,
    profile: NeutralProfile,
    earth_radius_m: float,
    surface_radius_m: float,
    settings: RaySolverSettings = RaySolverSettings(),
) -> SphericalRayResult:
    """Solve the verified initial nonducting short-arc endpoint family.

    Positions are sphere-centred Cartesian metres.  Profile heights are
    geometric heights above ``earth_radius_m``.  The profile must be explicitly
    bounded (``outside='unavailable'``); this solver never assumes a vacuum tail
    and never falls back to an effective-Earth-radius model.
    """

    try:
        source = tuple(float(value) for value in source_position_m)
        receiver = tuple(float(value) for value in receiver_position_m)
    except (TypeError, ValueError):
        source, receiver = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    empty_diagnostics = _failure_diagnostics(settings)
    numeric_values = (*source, *receiver, frequency_hz, earth_radius_m, surface_radius_m)
    if (
        len(source) != 3
        or len(receiver) != 3
        or not all(isfinite(value) for value in numeric_values)
        or frequency_hz <= 0.0
        or earth_radius_m <= 0.0
        or surface_radius_m < earth_radius_m
    ):
        return _failure(
            RaySolveStatus.INVALID_INPUT,
            "invalid_input",
            "finite 3-vector endpoints, positive frequency/radius, and surface>=Earth radius are required",
            source,  # type: ignore[arg-type]
            receiver,  # type: ignore[arg-type]
            earth_radius_m,
            surface_radius_m,
            frequency_hz,
            empty_diagnostics,
        )
    source = source  # type: ignore[assignment]
    receiver = receiver  # type: ignore[assignment]
    source_radius, receiver_radius = _norm(source), _norm(receiver)
    chord = _norm(_sub(receiver, source))
    if chord <= 1.0e-9:
        return _failure(
            RaySolveStatus.INVALID_INPUT,
            "coincident_endpoints",
            "source and receiver phase centres coincide",
            source,
            receiver,
            earth_radius_m,
            surface_radius_m,
            frequency_hz,
            empty_diagnostics,
            endpoint_chord_m=chord,
        )
    if source_radius < surface_radius_m or receiver_radius < surface_radius_m:
        return _failure(
            RaySolveStatus.BLOCKED_WITHIN_MODEL,
            "endpoint_below_surface",
            "an endpoint lies below the absorbing spherical surface",
            source,
            receiver,
            earth_radius_m,
            surface_radius_m,
            frequency_hz,
            empty_diagnostics,
            endpoint_chord_m=chord,
        )
    cosine_angle = max(-1.0, min(1.0, _dot(source, receiver) / (source_radius * receiver_radius)))
    central_angle = acos(cosine_angle)
    if central_angle > settings.maximum_central_angle_rad:
        return _failure(
            RaySolveStatus.UNSUPPORTED_MODEL,
            "local_domain_exceeded",
            "endpoint separation exceeds the declared short-arc UAV domain",
            source,
            receiver,
            earth_radius_m,
            surface_radius_m,
            frequency_hz,
            empty_diagnostics,
            central_angle_rad=central_angle,
            endpoint_chord_m=chord,
        )
    if profile.outside != "unavailable":
        return _failure(
            RaySolveStatus.UNSUPPORTED_MODEL,
            "unbounded_profile_policy",
            "trace_spherical_between requires an explicitly bounded profile (outside='unavailable')",
            source,
            receiver,
            earth_radius_m,
            surface_radius_m,
            frequency_hz,
            empty_diagnostics,
            central_angle_rad=central_angle,
            endpoint_chord_m=chord,
        )
    if not profile.frequency_range_hz[0] <= frequency_hz <= profile.frequency_range_hz[1]:
        return _failure(
            RaySolveStatus.MISSING_DATA,
            "frequency_outside_profile",
            "frequency lies outside the supplied profile validity interval",
            source,
            receiver,
            earth_radius_m,
            surface_radius_m,
            frequency_hz,
            empty_diagnostics,
            central_angle_rad=central_angle,
            endpoint_chord_m=chord,
        )
    profile_lower = earth_radius_m + profile.height_m[0]
    profile_upper = earth_radius_m + profile.height_m[-1]
    low_endpoint, high_endpoint = sorted((source_radius, receiver_radius))
    if low_endpoint < profile_lower - 1.0e-7 or high_endpoint > profile_upper + 1.0e-7:
        return _failure(
            RaySolveStatus.MISSING_DATA,
            "endpoint_outside_profile",
            "one or both endpoints lie outside the bounded refractivity profile",
            source,
            receiver,
            earth_radius_m,
            surface_radius_m,
            frequency_hz,
            empty_diagnostics,
            central_angle_rad=central_angle,
            endpoint_chord_m=chord,
        )

    stats = _QuadratureStats()
    try:
        q_minimum = _q_derivative_minimum(profile, earth_radius_m, low_endpoint, high_endpoint)
        if q_minimum <= 0.0:
            return _failure(
                RaySolveStatus.UNSUPPORTED_BRANCH,
                "nonmonotonic_q",
                "q(r)=n(r)r is not strictly increasing over the endpoint interval; duct/turning families are not searched",
                source,
                receiver,
                earth_radius_m,
                surface_radius_m,
                frequency_hz,
                _failure_diagnostics(settings, q_derivative_minimum=q_minimum),
                central_angle_rad=central_angle,
                endpoint_chord_m=chord,
            )

        branch: RayBranch
        iterations = 0
        parameter: str | None = None
        bracket: tuple[float, float] | None = None
        minimum_radius = low_endpoint

        if central_angle <= 1.0e-14:
            branch = RayBranch.RADIAL
            invariant_b = 0.0
            computed_angle = 0.0
            geometric_length = abs(receiver_radius - source_radius)
            _, _, refractivity_excess = _integrate_range(
                profile,
                earth_radius_m,
                low_endpoint,
                low_endpoint,
                high_endpoint,
                0.0,
                False,
                settings,
                stats,
            )
        else:
            q_low = _q(profile, low_endpoint, earth_radius_m)

            def outward(invariant: float) -> tuple[float, float, float]:
                return _integrate_range(
                    profile,
                    earth_radius_m,
                    low_endpoint,
                    low_endpoint,
                    high_endpoint,
                    invariant,
                    abs(invariant - q_low) <= 2.0e-12 * q_low,
                    settings,
                    stats,
                )

            outward_max = 0.0 if high_endpoint == low_endpoint else outward(q_low)[0]
            if high_endpoint > low_endpoint and central_angle <= outward_max + settings.angular_tolerance_rad:
                branch = RayBranch.RADIAL_MONOTONIC
                if abs(central_angle - outward_max) <= settings.angular_tolerance_rad:
                    invariant_b = q_low
                    computed_angle, geometric_length, refractivity_excess = outward(invariant_b)
                    bracket = (q_low, q_low)
                else:
                    lower_b, upper_b = 0.0, q_low
                    best = (0.0, 0.0, 0.0)
                    invariant_b = 0.0
                    for iterations in range(1, settings.maximum_iterations + 1):
                        invariant_b = 0.5 * (lower_b + upper_b)
                        best = outward(invariant_b)
                        if abs(best[0] - central_angle) <= settings.angular_tolerance_rad * 0.25:
                            break
                        if best[0] < central_angle:
                            lower_b = invariant_b
                        else:
                            upper_b = invariant_b
                    computed_angle, geometric_length, refractivity_excess = best
                    bracket = (lower_b, upper_b)
                parameter = "invariant_b_m"
            else:
                if surface_radius_m < profile_lower - 1.0e-7:
                    return _failure(
                        RaySolveStatus.MISSING_DATA,
                        "profile_missing_clearance_domain",
                        "the bounded profile does not extend to the surface needed to search the single-minimum family",
                        source,
                        receiver,
                        earth_radius_m,
                        surface_radius_m,
                        frequency_hz,
                        _failure_diagnostics(settings, stats=stats, q_derivative_minimum=q_minimum),
                        central_angle_rad=central_angle,
                        endpoint_chord_m=chord,
                    )
                q_minimum = _q_derivative_minimum(
                    profile, earth_radius_m, surface_radius_m, high_endpoint
                )
                if q_minimum <= 0.0:
                    return _failure(
                        RaySolveStatus.UNSUPPORTED_BRANCH,
                        "nonmonotonic_q",
                        "q(r)=n(r)r is not strictly increasing over the required clearance domain; ducts/upper turns are unsupported",
                        source,
                        receiver,
                        earth_radius_m,
                        surface_radius_m,
                        frequency_hz,
                        _failure_diagnostics(settings, stats=stats, q_derivative_minimum=q_minimum),
                        central_angle_rad=central_angle,
                        endpoint_chord_m=chord,
                    )

                def minimum_family(radius_minimum: float) -> tuple[float, float, float, float]:
                    invariant = _q(profile, radius_minimum, earth_radius_m)
                    first = _integrate_range(
                        profile,
                        earth_radius_m,
                        radius_minimum,
                        radius_minimum,
                        source_radius,
                        invariant,
                        True,
                        settings,
                        stats,
                    )
                    second = _integrate_range(
                        profile,
                        earth_radius_m,
                        radius_minimum,
                        radius_minimum,
                        receiver_radius,
                        invariant,
                        True,
                        settings,
                        stats,
                    )
                    return (
                        first[0] + second[0],
                        first[1] + second[1],
                        first[2] + second[2],
                        invariant,
                    )

                grazing = minimum_family(surface_radius_m)
                if central_angle > grazing[0] + settings.angular_tolerance_rad:
                    return _failure(
                        RaySolveStatus.BLOCKED_WITHIN_MODEL,
                        "ground_intersection",
                        "no supported direct ray clears the absorbing spherical surface; the requested angle exceeds the ground-grazing boundary",
                        source,
                        receiver,
                        earth_radius_m,
                        surface_radius_m,
                        frequency_hz,
                        _failure_diagnostics(
                            settings,
                            branch=RayBranch.SINGLE_MINIMUM,
                            stats=stats,
                            clearance=0.0,
                            q_derivative_minimum=q_minimum,
                        ),
                        central_angle_rad=central_angle,
                        endpoint_chord_m=chord,
                    )
                branch = RayBranch.SINGLE_MINIMUM
                parameter = "minimum_radius_m"
                if abs(central_angle - grazing[0]) <= settings.angular_tolerance_rad:
                    minimum_radius = surface_radius_m
                    computed_angle, geometric_length, refractivity_excess, invariant_b = grazing
                    bracket = (surface_radius_m, surface_radius_m)
                else:
                    lower_radius, upper_radius = surface_radius_m, low_endpoint
                    best = grazing
                    minimum_radius = surface_radius_m
                    for iterations in range(1, settings.maximum_iterations + 1):
                        minimum_radius = 0.5 * (lower_radius + upper_radius)
                        best = minimum_family(minimum_radius)
                        if abs(best[0] - central_angle) <= settings.angular_tolerance_rad * 0.25:
                            break
                        if best[0] > central_angle:
                            lower_radius = minimum_radius
                        else:
                            upper_radius = minimum_radius
                    computed_angle, geometric_length, refractivity_excess, invariant_b = best
                    bracket = (lower_radius, upper_radius)

        angular_residual = computed_angle - central_angle
        endpoint_error = 2.0 * receiver_radius * sin(abs(angular_residual) / 2.0)
        clearance = minimum_radius - surface_radius_m
        if (
            abs(angular_residual) > settings.angular_tolerance_rad
            or endpoint_error > settings.endpoint_tolerance_m
        ):
            return _failure(
                RaySolveStatus.NUMERICAL_FAILURE,
                "endpoint_residual",
                "bounded root solve did not meet the angular and Cartesian endpoint tolerances",
                source,
                receiver,
                earth_radius_m,
                surface_radius_m,
                frequency_hz,
                _failure_diagnostics(
                    settings,
                    branch=branch,
                    iterations=iterations,
                    parameter=parameter,
                    bracket=bracket,
                    angular_residual=angular_residual,
                    endpoint_error=endpoint_error,
                    stats=stats,
                    clearance=clearance,
                    q_derivative_minimum=q_minimum,
                ),
                central_angle_rad=central_angle,
                endpoint_chord_m=chord,
            )

        path, invariant_error = _build_path(
            source,
            receiver,
            central_angle,
            computed_angle,
            source_radius,
            receiver_radius,
            minimum_radius,
            invariant_b,
            branch,
            profile,
            earth_radius_m,
            settings,
            stats,
        )
        optical_length = geometric_length + refractivity_excess
        status = RaySolveStatus.SOLVED
        reason_code = "converged"
        reason = "supported nonducting spherical ray converged"
        ground_clear = clearance > settings.grazing_tolerance_m
        if clearance <= settings.grazing_tolerance_m:
            status = RaySolveStatus.BLOCKED_WITHIN_MODEL
            reason_code = "ground_grazing"
            reason = (
                "the computed boundary ray is ground-grazing within the declared clearance "
                "tolerance and intersects the absorbing surface"
            )
        diagnostics = RayDiagnostics(
            branch=branch,
            root_iterations=iterations,
            root_parameter_name=parameter,
            root_bracket=bracket,
            angular_endpoint_residual_rad=angular_residual,
            cartesian_endpoint_error_m=endpoint_error,
            invariant_max_relative_error=invariant_error,
            quadrature_evaluations=stats.evaluations,
            quadrature_error_estimate=(
                stats.error_angle,
                stats.error_length,
                stats.error_refractivity,
            ),
            minimum_clearance_m=clearance,
            clearance_uncertainty_m=max(
                settings.grazing_tolerance_m,
                endpoint_error,
                stats.error_length,
            ),
            q_derivative_minimum=q_minimum,
            path_sample_count=len(path.position_m),
            supported_family=_SUPPORTED_FAMILY,
        )
        return SphericalRayResult(
            status=status,
            reason_code=reason_code,
            reason=reason,
            source_position_m=source,
            receiver_position_m=receiver,
            earth_radius_m=earth_radius_m,
            surface_radius_m=surface_radius_m,
            frequency_hz=frequency_hz,
            central_angle_rad=central_angle,
            endpoint_chord_m=chord,
            invariant_b_m=invariant_b,
            geometric_length_m=geometric_length,
            refractivity_excess_m=refractivity_excess,
            optical_path_length_m=optical_length,
            vacuum_travel_time_s=chord / C,
            travel_time_s=optical_length / C,
            excess_delay_s=(optical_length - chord) / C,
            ground_clear=ground_clear,
            path=path,
            diagnostics=diagnostics,
            assumptions=_ASSUMPTIONS,
        )
    except (ArithmeticError, ValueError) as exc:
        code = str(exc) if str(exc) else "solver_failure"
        status = (
            RaySolveStatus.UNSUPPORTED_BRANCH
            if code in ("nonmonotonic_q", "imaginary_radial_branch")
            else RaySolveStatus.NUMERICAL_FAILURE
        )
        return _failure(
            status,
            code,
            f"ray solver stopped explicitly: {code}",
            source,
            receiver,
            earth_radius_m,
            surface_radius_m,
            frequency_hz,
            _failure_diagnostics(settings, stats=stats),
            central_angle_rad=central_angle,
            endpoint_chord_m=chord,
        )

