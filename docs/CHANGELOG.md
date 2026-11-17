# UAV-CAS Changelog

This changelog is maintained under the repository-root `AGENTS.md` rules. Entries marked **Reconstructed** were created after the implementation from repository artifacts. Their dates are reconstruction dates unless the cited evidence explicitly establishes an earlier date; they are not contemporaneous development notes.

## 2026-11-17 — Development-history initialization

- **Added:** The mandatory development-history system: `docs/CHANGELOG.md`, `docs/DECISIONS.md`, and `docs/DEVLOG.md`.
- **Affected files:** `docs/CHANGELOG.md`, `docs/DECISIONS.md`, `docs/DEVLOG.md`.
- **Backward compatibility:** Documentation-only change; no scientific code, API, model, dependency, numerical setting, or supported domain changed.

## 2026-11-17 — Phase 2A: bounded spherical ray BVP (**Reconstructed**)

Evidence: `docs/PROGRESS_PHASE2A.md`, `outputs/phase2a/phase2a_summary.json`, the named source and test files, and the generated Phase 2A artifacts. The original implementation-session date is not independently recorded; 2026-11-17 is the reconstruction date.

- **Added:** Immutable ray settings, path, diagnostics, status, and result contracts in `packages/cubesat-link/cubesat_link/ray_types.py`.
- **Added:** `trace_spherical_between` in `packages/cubesat-link/cubesat_link/ray_bvp.py` for the verified short-arc, nonducting, strictly increasing `q(r)=n(r)r` subset, including radial-monotonic and one-lower-minimum branches.
- **Added:** UAV profile/endpoint adapter, deterministic Phase 2A demonstration, ray-path visualization, CSV/JSON output, convergence controls, and ten Phase 2A tests.
- **Changed:** The repository test suite reported by the Phase 2A progress report increased from the Phase 1 baseline to 74 passed tests plus 15 passed subtests; this historical result was not rerun during history initialization.
- **Preserved:** The existing CubeSat `trace_spherical` API and `neutral.py`; EER remained an independent reference and was not used as a solver fallback.
- **Affected files:** `packages/cubesat-link/cubesat_link/ray_types.py`, `packages/cubesat-link/cubesat_link/ray_bvp.py`, `src/uav_cas/propagation/ray_tracing.py`, `src/uav_cas/phase2a_demo.py`, `src/uav_cas/visualization/ray_path.py`, `tests/test_ray_bvp.py`, `tests/test_phase2a_demo.py`, and `outputs/phase2a/`.
- **Backward compatibility:** Additive API work; the progress report states that the preserved CubeSat API and all 38 original tests remained unchanged and passing.

## 2026-11-17 — Phase 1: atmospheric and engineering foundations (**Reconstructed**)

Evidence: `docs/PROGRESS_PHASE1.md`, `docs/SOURCE_PROVENANCE.md`, `outputs/phase1/phase1_summary.json`, the named source and test files, and the generated Phase 1 artifacts. The original implementation-session date is not independently recorded; 2026-11-17 is the reconstruction date.

- **Added:** The preserved `cubesat_link` 0.2.0 source package, original eight test modules, schemas, examples, documentation, wheel, and metadata under `packages/cubesat-link/`.
- **Added:** The `uav_cas` package and root packaging/test configuration.
- **Added:** ISA-1976-compatible dry lower-atmosphere state calculations, geometric/geopotential altitude conversion, Sutherland viscosity, and dry-air sound speed.
- **Added:** ITU-R P.453-14 dry and specified local-humidity refractivity calculations and bounded, non-extrapolating, piecewise-linear refractivity profiles with provenance and deterministic hashes.
- **Added:** Validated MSL/AGL geometry, independent endpoint hardware and directionality, explicit calculation statuses, separate physical-sphere geometric/EER references, and a directional P.525 FSPL reference ledger.
- **Added:** A reproducible headless Phase 1 demonstration with CSV, JSON, and six PNG figures, plus 26 Phase 1 tests.
- **Preserved:** The root prototype, source archives, and public `cubesat_link` API. The legacy root ray tracer was not adopted as a verified production solver.
- **Affected files:** `packages/cubesat-link/`, `src/uav_cas/`, `tests/`, `pyproject.toml`, and `outputs/phase1/`.
- **Backward compatibility:** Additive foundation work. The Phase 1 progress report states that all 38 original CubeSat tests remained unchanged and passing; this historical result was not rerun during history initialization.

## 2026-11-17 — Repository initialization and initial publication

- **Added:** Git repository metadata on the `main` branch and an `origin` remote for `https://github.com/confusingRD/UAV-Communication-Analysis-Suite.git`.
- **Added:** `.gitattributes` rules that normalize source, documentation, configuration, and scientific text artifacts while preserving archive, wheel, and image bytes.
- **Changed:** Expanded `.gitignore` coverage for local Python environments, bytecode and test caches, coverage output, root packaging/freezer products, IDE and operating-system state, credentials, temporary files, and non-reproducible simulation intermediates.
- **Preserved:** Scientific source, tests, documentation, provenance archives, the preserved CubeSat wheel, and the Phase 1/2A reproducibility outputs remain in the tracked baseline. No scientific data was deleted.
- **Affected files:** `.gitattributes`, `.gitignore`, `docs/CHANGELOG.md`, `docs/DECISIONS.md`, and `docs/DEVLOG.md`; repository metadata under `.git/` is local metadata rather than tracked content.
- **Backward compatibility:** Repository-configuration and documentation change only. No scientific algorithm, physical assumption, API, dependency, unit, numerical tolerance, boundary condition, or supported domain changed.

## 2026-11-17 — Phase 2B: scientific verification and benchmarking

- **Added:** An independent Cartesian Fermat RK4 launch-shooting reference under `src/uav_cas/verification/`; it does not call the production spherical BVP quadratures or root solver.
- **Added:** The deterministic `python -m uav_cas.phase2b_demo` workflow and console entry point, producing JSON, eight CSV tables, and six 300 dpi scientific figures.
- **Added:** Systematic atmospheric-grid, quadrature-tolerance, shooting-limit, path-sampling, near-horizon, reversibility, analytical constant-index, EER, and benchmark-matrix studies.
- **Added:** Phase 2B regression tests for the independent formulation, failure taxonomy (including quadrature exhaustion, physical blockage, ground-level endpoints, and coincident endpoints), and complete output regeneration.
- **Added:** The academic verification report `docs/PROGRESS_PHASE2B.md` and reproducibility artifacts under `outputs/phase2b/`.
- **Verified:** The 130 km Phase 2A case was independently regenerated under its original adapter controls; the complete suite now passes 77 tests plus 15 subtests.
- **Preserved:** Production spherical BVP equations, solver settings/API, legacy CubeSat functionality, and the separation between ray tracing and EER. No EER fallback or Phase 3 coverage logic was added.
- **Affected files:** `src/uav_cas/phase2b_demo.py`, `src/uav_cas/verification/`, `tests/test_phase2b_verification.py`, `pyproject.toml`, `docs/PROGRESS_PHASE2B.md`, `docs/CHANGELOG.md`, `docs/DECISIONS.md`, `docs/DEVLOG.md`, and `outputs/phase2b/`.
- **Backward compatibility:** Additive implementation. Existing public APIs and numerical defaults are unchanged; all original CubeSat, Phase 1, and Phase 2A regression layers remain passing.

