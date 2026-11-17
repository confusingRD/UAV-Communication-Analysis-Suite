"""Reproducibility checks for the Phase 2A scientific export bundle."""

from __future__ import annotations

import csv
import json

from uav_cas.phase2a_demo import run_demo


def test_phase2a_demo_exports_path_diagnostics_and_figure(tmp_path) -> None:
    summary = run_demo(tmp_path)
    expected = {
        "phase2a_ray_path.csv",
        "phase2a_profile_convergence.csv",
        "phase2a_constant_index_verification.csv",
        "phase2a_uav_ray_cross_section.png",
        "phase2a_summary.json",
    }
    assert expected == {path.name for path in tmp_path.iterdir()}
    assert summary["ray_result"]["status"] == "solved"
    assert summary["ray_result"]["diagnostics"]["cartesian_endpoint_error_m"] < 0.1
    assert summary["method_separation"]["effective_earth_radius"].startswith(
        "independent reference only"
    )
    with (tmp_path / "phase2a_ray_path.csv").open(encoding="utf-8", newline="") as handle:
        path_rows = list(csv.DictReader(handle))
    assert len(path_rows) == 401
    with (tmp_path / "phase2a_summary.json").open(encoding="utf-8") as handle:
        reloaded = json.load(handle)
    assert reloaded["atmosphere"]["profile_sha256"] == summary["atmosphere"]["profile_sha256"]
    assert (tmp_path / "phase2a_uav_ray_cross_section.png").stat().st_size > 100_000

