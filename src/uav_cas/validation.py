"""Small strict-validation helpers shared by public dataclasses."""

from __future__ import annotations

from math import isfinite


def finite_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError(f"{field} must be a finite real number")
    return float(value)


def positive(value: object, field: str) -> float:
    result = finite_number(value, field)
    if result <= 0.0:
        raise ValueError(f"{field} must be positive")
    return result


def nonnegative(value: object, field: str) -> float:
    result = finite_number(value, field)
    if result < 0.0:
        raise ValueError(f"{field} must be nonnegative")
    return result


def nonempty(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()

