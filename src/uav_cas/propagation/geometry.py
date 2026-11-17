"""Independent spherical geometry primitives for analytical references."""

from __future__ import annotations

from math import acos, cos, sqrt

from uav_cas.validation import nonnegative, positive


RADIO_EARTH_RADIUS_M = 6_371_000.0


def endpoint_chord_m(
    source_height_m: float,
    receiver_height_m: float,
    surface_distance_m: float,
    *,
    earth_radius_m: float = RADIO_EARTH_RADIUS_M,
) -> float:
    h1 = nonnegative(source_height_m, "source_height_m")
    h2 = nonnegative(receiver_height_m, "receiver_height_m")
    distance = nonnegative(surface_distance_m, "surface_distance_m")
    radius = positive(earth_radius_m, "earth_radius_m")
    central_angle = distance / radius
    if central_angle > 3.141592653589793:
        raise ValueError("surface distance must not exceed half the spherical circumference")
    r1 = radius + h1
    r2 = radius + h2
    return sqrt(max(0.0, r1 * r1 + r2 * r2 - 2.0 * r1 * r2 * cos(central_angle)))


def single_endpoint_horizon_surface_distance_m(
    height_m: float,
    *,
    earth_radius_m: float = RADIO_EARTH_RADIUS_M,
) -> float:
    height = nonnegative(height_m, "height_m")
    radius = positive(earth_radius_m, "earth_radius_m")
    return radius * acos(radius / (radius + height))


def two_endpoint_horizon_surface_distance_m(
    first_height_m: float,
    second_height_m: float,
    *,
    earth_radius_m: float = RADIO_EARTH_RADIUS_M,
) -> float:
    return single_endpoint_horizon_surface_distance_m(
        first_height_m, earth_radius_m=earth_radius_m
    ) + single_endpoint_horizon_surface_distance_m(
        second_height_m, earth_radius_m=earth_radius_m
    )

