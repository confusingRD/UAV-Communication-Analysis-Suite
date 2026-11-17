# Source provenance and environment record

## Preserved inputs

The two original archives in `CommZipFile/` were not modified. SHA-256 values recorded on 2026-11-17:

- `cubesat-link-0.2.0-source.zip`: `A4B3C89D3C9B04D7ABF05329E58748438F8B8B480D22ED40CF0C0FCBC2948EAE`
- `cubesat-link-0.2.0-integration.zip`: `8389A9EF3C32A66200FDE308C28EDE1EEA52FEF4FB18416493196E9D822A75DF`

The supported source archive was mechanically copied to `packages/cubesat-link/`. Its `cubesat_link` source package, eight original test modules, examples, schemas, documentation, build metadata, wheel, manifest, and legacy snapshot were retained. No original test was edited. The root UAV prototype, including `raytrace.py`, was not overwritten or removed.

## Python environment

The pre-existing `.venv` identifies CPython 3.15.2 managed by `uv`. It could not execute inside the repository sandbox and Python 3.15 is above the tested compatibility range of the selected scientific/GUI stack. It was therefore not used for scientific claims.

A repository-local CPython 3.13.18 distribution and `.venv-science` environment were created. The project declares `>=3.11,<3.14`. Verified scientific packages during Phase 1 were NumPy 2.5.5, Matplotlib 3.11.2, and pytest 9.2.0. Environment directories and caches are excluded by `.gitignore`.

## Packaging notes

`uav-cas` and the preserved `cubesat-link==0.2.0` were installed as editable local packages. The root package declares the preserved library dependency explicitly. PySide6/Matplotlib/PyInstaller are optional packaging-smoke dependencies and are not imported by the scientific core.

The first archive test invocation using the original Python 3.15 environment did not start because its managed interpreter was inaccessible. A later Python 3.13 invocation from outside the extracted source root collected eight import errors because `cubesat_link` was not on the import path; this was an invocation error, not a scientific test failure. Running from the extracted source root produced the recorded 38/38 passing result.

The time-boxed deployment smoke used PySide6 6.12.0, Matplotlib 3.11.2, and PyInstaller 6.22.3 on Windows 11 / CPython 3.13.18. The offscreen QtAgg canvas ran both from source and from a PyInstaller one-directory build. Generated smoke build files are isolated under ignored `.smoke/`; this establishes basic tool compatibility only, not a finished GUI or release executable.

