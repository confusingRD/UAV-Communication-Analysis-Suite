import sys

import pytest

import uav_cas
from uav_cas.atmosphere import RefractivityProfile
from uav_cas.propagation import PropagationRequest, RaySolveStatus


def test_unified_package_public_api_runs_without_legacy_imports() -> None:
    profile = RefractivityProfile.from_dry_isa(0.0, 5_000.0, 25.0)
    request = PropagationRequest("ground", "uav", 10.0, 1_000.0, 20_000.0)
    result = uav_cas.trace_uav_path(request, profile)

    assert result.status is RaySolveStatus.SOLVED
    assert result.diagnostics.minimum_clearance_m == pytest.approx(10.0, abs=1.0e-6)
    assert uav_cas.free_space_path_loss_db(1_000.0, 2.4e9) == pytest.approx(
        100.0520080561155
    )
    assert not any(name == "cubesat_link" or name.startswith("cubesat_link.") for name in sys.modules)
