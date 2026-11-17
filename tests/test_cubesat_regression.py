import cubesat_link


def test_preserved_cubesat_public_api_and_version():
    assert cubesat_link.__version__ == "0.2.0"
    for name in ("fspl_db", "compute_budget", "trace_spherical", "evaluate_link"):
        assert hasattr(cubesat_link, name)

