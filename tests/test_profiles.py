import pytest

from uav_cas.atmosphere.profiles import ProfileStatus, RefractivityProfile


def test_profile_interpolation_boundaries_and_hash():
    profile = RefractivityProfile.from_samples(
        [0.0, 100.0, 300.0], [1.000300, 1.000290, 1.000270],
        source="synthetic verification table", model_version="test-v1",
        humidity_basis="specified values",
    )
    midpoint = profile.evaluate(50.0)
    assert midpoint.status is ProfileStatus.AVAILABLE
    assert midpoint.refractive_index == pytest.approx(1.000295)
    assert profile.evaluate(-1.0).status is ProfileStatus.MISSING_DATA
    assert profile.evaluate(301.0).refractive_index is None
    assert len(profile.profile_hash) == 64


def test_profile_gradients_and_knot_sides():
    profile = RefractivityProfile.from_samples(
        [0.0, 100.0, 300.0], [1.000300, 1.000290, 1.000250],
        source="synthetic verification table", model_version="test-v1",
        humidity_basis="specified values",
    )
    assert profile.gradient_at(50.0) == pytest.approx(-1.0e-7)
    assert profile.gradient_at(100.0, side="left") == pytest.approx(-1.0e-7)
    assert profile.gradient_at(100.0, side="right") == pytest.approx(-2.0e-7)
    assert profile.gradient_at(400.0) is None


def test_profile_rejects_invalid_tables():
    with pytest.raises(ValueError):
        RefractivityProfile.from_samples(
            [0.0, 0.0], [1.0003, 1.0002], source="x", model_version="x",
            humidity_basis="x",
        )
    with pytest.raises(ValueError):
        RefractivityProfile.from_samples(
            [0.0, 100.0], [1.0003], source="x", model_version="x",
            humidity_basis="x",
        )


def test_dry_isa_profile_preserves_states_and_bounds():
    profile = RefractivityProfile.from_dry_isa(0.0, 250.0, 100.0)
    assert profile.geometric_heights_m == (0.0, 100.0, 200.0, 250.0)
    assert len(profile.thermodynamic_states) == 4
    assert profile.boundary_policy == "unavailable"

