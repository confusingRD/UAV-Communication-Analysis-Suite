# UAV Communication Analysis Suite (UAV-CAS): Audit and Development Plan

Audit date: 17 November 2026. Status: proposal for review; application implementation and executable packaging have not started.

Scientific direction, revised 17 November 2026: **Refractivity-Aware Ray-Tracing Framework for UAV Communication Coverage Analysis**. UAV-CAS remains the working application name.

This document is the implementation handoff for an offline Windows engineering application and a reusable scientific Python engine. The original assignment added only this document; the present revision changes only this document in place. Original archive inspection and execution used a disposable temporary directory; source and ZIP files were preserved. Solver source and relevant tests were reinspected for this revision; no new physics functionality was implemented and no tests were rerun. The 38-test evidence below belongs to the original audit.

## 1. Executive Summary

Use the `cubesat_link` package inside [cubesat-link-0.2.0-source.zip](CommZipFile/cubesat-link-0.2.0-source.zip) as the preserved scientific baseline. Do not rebuild the application around the incomplete root Streamlit prototype. The package has explicit units, provenance, missing-data semantics, geometry, a restricted spherical refraction solver, link-budget arithmetic, and satellite effects. All 38 supplied tests passed during the original audit on the existing Python 3.15.2 environment. This is numerical/software verification, not experimental validation; no new test execution is claimed in this revision.

The root prototype imports four absent modules: `atmosphere`, `refractivity`, `losses`, and `linkbudget`. Its atmospheric and coverage features therefore cannot be recovered merely by installing its dependencies. The packaged library is substantially better organized, but it does not implement ISA atmospheric state, a P.676 gas calculator, maximum UAV coverage, terrain clearance, or a desktop interface. Its `P676GasProvider` explicitly reports unavailable functionality. Synthetic gas tables in examples are not a verified atmospheric model.

The primary workflow is atmospheric state -> physically defined `n(h)` -> verified spherical ray boundary-value solution -> path connectivity, geometry, bending and delay -> conditional link budget -> feasible coverage intervals and boundaries. Ray tracing is the primary propagation-geometry method and its verification is a release gate. EER and geometric LOS are separate analytical references, benchmarks and user-selected comparisons. They must never silently replace a failed ray calculation or contribute an additional curvature correction to a refracted path.

Recommended first release: verified nonducting spherical rays between ground/UAV endpoints, atmosphere/refractivity profiles, path plots and diagnostics, independent uplink/downlink hardware, a conditional budget using endpoint-chord FSPL as an explicit spreading approximation, ray-based coverage/altitude sensitivity, and independent EER/geometric comparisons. Retain scenario saving/comparison, CSV/JSON/plot export, PySide6 Qt Widgets and PyInstaller one-directory Windows delivery. Ray-tube focusing, ducting, terrain interactions, multipath and horizontal atmospheric gradients remain outside the first release.

Proceed next with Phase 1 atmosphere and scientific contracts after review, then a dedicated Phase 2 solver verification/extension gate before coverage. A tiny Qt/freezer compatibility check is planned early without delaying that scientific gate. A more sophisticated solver is not automatically a more accurate real-world predictor: numerical error, model fidelity, environmental input uncertainty and experimental agreement are distinct. Hardware, datum, gas-model, licensing and Windows compatibility decisions remain explicit; deterministic range is not guaranteed operational range or statistical availability.

## 2. Project Objectives and Scope

### Mandatory first-release capabilities

- Run offline on explicitly tested Windows 10/11 x64 versions by opening an executable, without Python installation or a terminal.
- Calculate atmospheric temperature, pressure, density, dynamic viscosity, speed of sound, and refractivity at a specified altitude, including profiles and units. Humidity-derived results require a declared humidity model or measurement.
- Accept MSL or AGL altitude with explicit ground elevation requirements; distinguish atmospheric geopotential height from geometric height and geodetic ellipsoidal height.
- Configure ground/UAV TX and RX independently, calculate EIRP, each loss, received power, sensitivity, raw margin and margin after reserve.
- Build a bounded refractivity profile with source, units, interpolation and frequency/height validity, and use it in the primary spherical ray solver on the actual Earth radius.
- Solve and verify the declared first-release ground/UAV endpoint families: unequal/equal elevations, either endpoint higher, radial paths, and a nonducting path with one radial minimum above the smooth surface when required. These are planned extensions, not current package capabilities.
- Report sampled ray coordinates, launch/arrival directions, bending, geometric/optical length, delay, ground clearance and convergence diagnostics; classify unsupported, unavailable and failed calculations separately from physical blockage within the model.
- Calculate conditional maximum endpoint slant separation, ray length and ground distance from verified ray connectivity and hardware feasibility; retain all resolved feasible intervals and unresolved regions.
- Display ray paths, idealized top-down coverage and altitude sensitivity, with separate EER (`k=1`, `k=4/3`, justified derived-k) comparison results and no terrain-aware claims.
- Save/load versioned local scenarios, compare at least two scenarios, and export inputs, assumptions, results, CSV, JSON and PNG.
- Preserve existing numerical APIs/tests and support scientific engine use without importing Qt.

### Recommended improvements

A verified optional P.676 backend for eligible frequencies; separate noise-derived sensitivity; light/dark themes; SVG plots and a polished installer. Import of bounded, documented `n(h)` tables and an approximate refracted-path Fresnel diagnostic belong to the scientific first release; arbitrary weather-file formats and quantitative refractive Fresnel theory can follow. Fresnel enforcement is optional and must expose its approximation.

### Optional advanced features

Directional pattern files and azimuthal coverage, PDF reports, 3D geometry, offline geographic overlays, DEM obstruction/diffraction, measured RF calibration, and extended atmospheric profiles. These must not delay a credible baseline submission.

### Research extensions

Atmospheric trapping/ducting, multiple eigenrays and caustics, terrain-aware stochastic models, satellite orbit inputs, IRI/IGRF providers, scintillation, modem/BER/throughput, and time-dependent availability. The simple nonducting radial-minimum branch needed for elevated-endpoint coverage is first-release work, not a deferred ducting feature. No cloud account, paid API, online map, telemetry transmission, or weather download is required for the MVP.

Proposed operating envelope: UAV geometric MSL altitude 0–11,000 m, endpoints above a declared uniform smooth ground surface, and 0.1–12 GHz as a conservative application envelope. First-release rays require positive `n`, horizontally stratified scalar refractivity, and strictly increasing `q(r)=n(r)r` over the complete explored height domain, with any additional uniqueness/domain conditions established in Phase 2. A profile failing those conditions is unsupported, not a no-link result. This is a product boundary, not a statement that every model is valid throughout it. Each selected model applies its own narrower limits. Below-sea-level sites are explicitly unsupported in the initial UI; reject with an explanation rather than silently clipping them. A supported subset must be published before release; if branch verification fails, report that limitation and delay or explicitly narrow the release rather than substituting EER.

## 3. Existing Repository Audit

### Scope and inspection method

Inspected the entire active project file inventory at `C:/Users/admin/Desktop/pduy/UAV_comm`, including root source/documentation/launchers, both archives in [CommZipFile](CommZipFile), environment metadata and installed-distribution inventory in [.venv](.venv), and filenames in [__pycache__](__pycache__). Read all six root Python source files. No other application source/data directories, source tests, Qt files, installer specification, CI configuration, or Git directory were found in the root inventory. No applicable `AGENTS.md` was found in the checked project/ancestor locations. Third-party interpreter internals and compiled bytecode were not treated as project source.

The original audit's root inventory comprised [app.py](app.py), [config.py](config.py), [main.py](main.py), [plots.py](plots.py), [raytrace.py](raytrace.py), [service.py](service.py), `README.md`, [requirements.txt](requirements.txt), [run_gui.bat](run_gui.bat), and [run_gui.sh](run_gui.sh).

Revision inventory note: the root `README.md` was read in the original audit but was not found in the current root listing during this revision's consistency check. Its earlier findings below are retained as historical evidence; its absence was not caused or repaired by this document-only task. The other nine source/configuration/launcher files still match their archived legacy bytes, and both archive hashes remain unchanged. Do not confuse the archive's different README with the original prototype README.

The environment configuration points to CPython 3.15; the environment tool identified 3.15.2. Only `pip-26.3.dist-info` was found in the local installed-distribution inventory. The root requirements list NumPy, SciPy, Matplotlib, pandas, Streamlit and `itur` without version constraints; these distributions were not present in that inventory. No dependency installation was performed. Terminal interpreter evidence is not a claim about a separately configured editor/Pylance interpreter.

Cached bytecode includes Python 3.12 and 3.15 filenames. This does not establish supported runtimes or provide the missing physics source. The root README refers to `tests/test_core.py`, which is absent, and explicitly asks the developer to repair `itur` API calls in absent atmosphere/loss modules. These are unresolved implementation instructions, not evidence of working integration.

### Confirmed architectural and correctness concerns

1. `service.run` imports missing physics modules, preventing the supplied application workflow from being self-contained.
2. `Inputs.validate` only checks positive frequency/distance, the 11 km cap, and UAV-above-station ordering. It lacks finite-number, geographic, altitude-reference, solver-step, loss, and hardware completeness validation.
3. `shoot_to_target` can return a grazing or 89.9-degree ray that does not connect the requested endpoint. The service handles `beyond_horizon` but does not reject `too_close`, so that branch can feed an incorrect endpoint into a budget. This is a source-level finding; the broken root application was not executed.
4. Failed far-ray evaluation can produce NaN range metadata. The distance sweep starts at 5 km, uses only 30 points, and caps at 2,000 km. It cannot support reliable short-range boundaries or prove a maximum. The referenced maximum-range implementation itself is absent.
5. `trace_ray` does not expose a distinct solver-failure result or check `sol.success` separately from target events. Ground intersection allows a 0.5 m offset; grazing and root bracketing assumptions need tests, especially for nonmonotonic profiles.
6. Root `excess_delay_m` integrates only `(n-1) ds`; it omits curved-path geometric excess when interpreted relative to the straight vacuum chord. The archive package corrects this distinction.
7. Root service labels absent gas data as zero loss with a note. The UI describes clamping 868/915 MHz to 1 GHz, but the missing gas module prevents verification of that implementation. Do not carry that advertised behavior into UAV-CAS.
8. The root radio has one combined cable loss and no independent TX/RX endpoint configurations. The horizon call uses UAV MSL altitude with station antenna AGL height, which is inconsistent for nonzero site ground elevation.
9. `plots.py` forces the global Agg backend. Reusing it unchanged would interfere with an embedded Qt plotting design. `plot_rays` also assumes a nonempty set when taking a maximum.
10. Streamlit executes UI configuration at import time. The shared service returns interpolator-containing objects and performs a ray fan and sweep on every run. This is unsuitable as the lightweight public API for a responsive desktop UI.
11. The Windows batch launcher depends on an installed `streamlit` command and does not set its working directory. It is not a standalone executable distribution.

## 4. ZIP Archive Inspection Findings

Both archives were read directly before any execution. Paths were checked for traversal/absolute-path hazards and duplicates. CRC checks and every manifest SHA-256 passed. A safe temporary extraction of only package, tests, and examples was then used for the inspected unittest suite; it was removed automatically. Build/release scripts were read, not executed.

| Archive | Contents and role | Audit result |
|---|---|---|
| [cubesat-link-0.2.0-source.zip](CommZipFile/cubesat-link-0.2.0-source.zip) | 65 entries under `cubesat-link-0.2.0/`: package, legacy snapshots, build metadata/scripts, wheel, docs, schemas, tests and examples | Preferred development baseline; integrity checks passed |
| [cubesat-link-0.2.0-integration.zip](CommZipFile/cubesat-link-0.2.0-integration.zip) | 33 entries: wheel, docs, schemas, examples, tests and manifest; no loose library source or build metadata | Distribution/integration bundle of the same release, not another development version |

Archive SHA-256 values recorded in this audit:

```text
source:      a4b3c89d3c9b04d7abf05329e58748438f8b8b480d22ed40cf0c0fcbc2948eae
integration: 8389a9ef3c32a66200fde308c28ede1eea52fef4fb18416493196e9d822a75df
```

All common payload files are byte-identical; manifests differ because payload membership differs. All nine root files that also appear in the source archive's `legacy/` are byte-identical. Root README has no legacy counterpart there.

Archive-relative paths below refer to the `cubesat-link-0.2.0/` prefix, not extracted files currently present in the workspace:

- `cubesat_link/`: 11 Python files (`__init__`, `__main__`, `api`, `budget`, `cli`, `geometry`, `interface`, `ionosphere`, `neutral`, `providers`, `types`) and two bundled schemas.
- `pyproject.toml`: setuptools build backend (`>=68`), Python `>=3.10`, no runtime dependencies, and console entry point `cubesat-link = cubesat_link.cli:main`.
- `dist/cubesat_link-0.2.0-py3-none-any.whl`: pure-Python wheel with matching package source/schema bytes. Metadata contains no runtime dependency declarations. A console-script launcher generated by installing this wheel is not a Python-free desktop application.
- `tests/`: eight unittest modules, 38 test methods; inspected and rerun successfully.
- `docs/`: `AUDIT.md`, `INTEGRATION.md`, `PHYSICS.md`, `RELEASE.md`, `verification.json`. Historical verification claims were distinguished from current checks.
- `examples/`: Python entry points, `build_inputs.py`, four input JSON scenarios (`uav`, `cubesat`, `cubesat_ideal`, `pass`) and saved outputs. These are synthetic fixtures, not measurements, meteorological data, antenna patterns or terrain datasets.
- `schemas/`: request/response Draft 2020-12 contracts matching the packaged copies. The internal validator is deliberately limited to the schema keywords shipped in this release.
- `scripts/`: schema generation, source/integration archive creation, installed-wheel verification and archive handoff verification. No PyInstaller/Nuitka/installer infrastructure.
- `legacy/`: the nine matching root files plus older `api.py`, `budget.py`, `geometry.py`, `neutral.py`, and `ionosphere.py`. These snapshots use relative imports but lack their own complete package dependencies; do not adopt them as a second core.

Version comparison: packaged API adds providers and path binding; budget preserves radio assumptions; geometry explicitly labels geometric windows; neutral tracing adds bounded UAV profiles, consistent Earth defaults and full excess delay. Legacy ionosphere is byte-identical to its packaged counterpart. The source ZIP release packaging script expects historical root files when creating `legacy/`; a checkout reconstructed from this ZIP instead already has `legacy/`. Consequently, `package_release.py` needs layout adaptation before it can serve as a repeatable future release command. Do not run it blindly.

No LICENSE file or explicit project license declaration was found in the archive listings/build metadata. Establish ownership and redistribution terms before public distribution. Internal manifests demonstrate integrity, not external authenticity or permission to redistribute.

The saved UAV output has a computed integral of synthetic gas attenuation but an unavailable complete link margin; the saved CubeSat output has unavailable gas and margin. Only the explicitly idealized CubeSat fixture has a complete margin (approximately 7.968592 dB). The pass input contains 121 timestamped states and its output contains geometric windows. These outputs reinforce that an `ok: true` response means a valid request, not necessarily a complete budget or a working communication link.

## 5. Existing Functionality Inventory

Verification labels: **current pass** records the last observed result from the original 38-test audit, not a rerun of planned changes; **static** means inspected but not executed in that audit; **missing** means referenced source is absent. A passing test is limited to its tested cases.

| Existing File / Module | Current Functionality | Reuse Status | Required Changes | Verification Status |
|---|---|---|---|---|
| [config.py](config.py): `Inputs`, `LinkInputs`, `GeometryInputs`, `SolverConfig` | Mutable inputs, defaults and limited validation | Reuse with modification | Borrow input concepts; explicit SI/datum/endpoints, immutable validated models | Static; no root tests |
| [raytrace.py](raytrace.py): `trace_ray`, `grazing_angle`, `shoot_to_target`, `ray_fan`, `RayResult` | SciPy DOP853 spherical ODE, shooting, gas/path integral and ray coordinates | Reuse with modification | Preserve governing equations and research comparison ideas; do not adopt its unverified shooting wrapper as production solver | Static; original medium module missing |
| [service.py](service.py): `run`, `max_range`, JSON dataclass helpers | Shared CLI/Streamlit orchestration | Rewrite | Separate atmosphere/link/coverage services, explicit unavailable states | Missing imports; not runnable as supplied |
| [app.py](app.py): `cached_run`, `itur_available` and UI | Streamlit forms, tabs, results and downloads | Rewrite | Reuse workflow ideas only in Qt; independent pages and cancellation | Static; broken dependency chain |
| [plots.py](plots.py): `plot_atmosphere`, `plot_gradient`, `plot_rays`, `plot_losses` | Matplotlib figure construction and PNG export | Reuse with modification | Backend-neutral functions, English labels, empty/unknown handling and new data contracts | Static |
| [main.py](main.py): `main` | Argparse CLI, prints and plots | Defer | Keep original; new headless API/CLI should use consolidated core | Missing imports |
| [requirements.txt](requirements.txt), launchers and original root `README.md` | Prototype setup instructions | Rewrite | Separate core/desktop/dev dependencies, pinned release lock, executable instructions | Static original audit; referenced test absent; root README not found at revision check |
| Missing `atmosphere.py`, `refractivity.py`, `losses.py`, `linkbudget.py` | Advertised ISA/ITU/loss/coverage implementations | New implementation | Implement verified UAV modules; do not infer old equations | Missing in root and both ZIP payloads |
| Archive `cubesat_link/types.py`: `Effect`, `Earth`, `GroundStation`, `SatelliteState` | SI values, finite checks, UTC/frame contracts, provenance statuses | Reuse as-is | Preserve API; add UAV models externally for MSL/AGL and endpoint roles | Current pass, indirectly through suites |
| Archive `budget.py`: `fspl_db`, `Radio`, `compute_budget`, `Budget` | P.525 spreading, fixed component ledger, threshold margin | Reuse with modification | Reuse arithmetic unchanged; add UAV adapter, separated feeder inputs, EIRP/totals and threshold source | Current pass: analytic scaling and hand ledger |
| Archive `geometry.py`: `station_ecef`, `enu`, `geometry` | WGS-84/spherical coordinates, angles, Earth segment occultation and elevation mask | Reuse with modification | Reuse transforms/reference geometry; use ray clearance and ray directions for primary UAV connectivity/masks | Current pass: poles, tangent, overhead, occultation |
| Archive `geometry.py`: `contact_windows` | Cone intersections with linear ECEF interpolation | Reuse as-is | Preserve satellite API; defer UI integration | Current pass: hidden passes, clipping/gaps, orbit convergence |
| Archive `neutral.py`: `NeutralProfile`, `trace_spherical`, `p834_reference_profile` | Spherical outward rays, adaptive quadrature, refraction, path/delay, supplied gas integration | Reuse with modification | Preserve old API and tests; add verified endpoint-general BVP, sampled paths, signed directions, clearance and failure contracts before coverage | Current pass: vacuum, analytic integrals, RK4, convergence; new branches unimplemented |
| Archive `ionosphere.py`: `integrate_electrons`, `ionospheric_effects`, `polarization_loss` | Finite STEC, first-order delay/phase/Faraday and ideal polarization | Reuse as-is | Preserve satellite engine; UAV adapters explicitly exclude ionosphere under low-altitude assumptions | Current pass: synthetic analytic cases; no measured validation |
| Archive `providers.py`: table/reference/electron providers and metadata/binding | Provenance, units, epoch/path checks | Reuse as-is | Retain contracts; new atmosphere/gas providers alongside | Current pass: unit/epoch/boundary failures |
| Archive `providers.py`: `P676GasProvider` | Reports missing model or unsupported frequency | New implementation | Retain legacy behavior; add separately named verified backend and capability status | Current pass verifies unavailability, not gas physics |
| Archive `api.py`: `evaluate_link`, `LinkResult` | Geometry/ray/electron/ledger orchestration | Reuse with modification | Preserve satellite signature; add UAV service/policy rather than rewrite satellite defaults | Current pass: incomplete/blocked budgets, delay independent of power |
| Archive `interface.py`, `cli.py`, `__main__.py` and schemas | JSON request validation, errors and CLI | Reuse with modification | Preserve schema 1.0; add separate UAV scenario schema and migrations | Current pass: CLI/API equality and invalid requests |
| Archive tests and synthetic examples | Numerical/API regression corpus | Reuse as-is | Retain unchanged fixtures; add UAV-specific verification separately | 38/38 current pass |
| Archive `scripts/`, `pyproject.toml`, wheel | Library release/build scaffolding | Reuse with modification | Fix legacy file layout, add desktop package/release stages and licensing | Static scripts; wheel bytes checked; no new wheel build |

There is no existing maximum-range solver in the supported package, atmospheric state calculator, aerodynamic viscosity/sound-speed model, actual P.676/P.835 implementation, Fresnel/terrain module, pattern parser, desktop Qt app, or Python-independent Windows release.

## 6. Reusable Components and Required Modifications

Preserve the archive package as an independently installable library with its historical name and public API. Add a small `uav_cas` package that depends on it and contains UAV policy, atmosphere, coverage, visualization and application layers. Avoid a wholesale numerical rewrite or renaming all satellite classes. A UAV endpoint can be adapted to `SatelliteState` internally, but the UI should call it a UAV, not a satellite.

Reuse `fspl_db`, result provenance, finite-input checks, coordinate transforms, table profiles and tested neutral/ionospheric algorithms. Preserve `compute_budget` and translate explicit UAV loss assumptions into its fixed ledger. Add TX/RX feeder details to the UAV result without changing the meaning of the library's existing combined `cable_loss_db`.

The ray algorithm is a central reuse target. Preserve `trace_spherical` and its `NeutralRay` meanings for existing callers, including its outward-branch limitations and WGS-84 rejection. Add a separate reusable endpoint solver and richer path result in `cubesat_link` through an additive, versioned API; the proposed name is `trace_spherical_between`. This new API does not exist in release 0.2.0. It should reuse reviewed quadrature/profile primitives where they apply, with independent tests for every extension. Do not quietly change the old function to return different branches, angles or fields. New UAV method adapters belong in `uav_cas`, and must not force the old `evaluate_link` satellite orchestration to handle unsupported UAV configurations.

Preserve `computed`, `assumed`, and `not_computable` semantics. For a low-altitude, idealized UAV scenario, the adapter may declare ionospheric and selected unmodeled terms zero with `assumed` status and a visible physical/scope rationale. It must not convert arbitrary missing values to zero or activate `vacuum=True` merely to obtain a complete budget when atmospheric effects are otherwise selected.

Place optional added environmental loss outside the old fixed ledger in the UAV layer, or extend the library through a deliberate new API version. Do not overload `rain`, `beam_spreading` or `cable_loss_db` with unrelated margins. Use a single documented final-budget calculation to prevent duplicate deductions. Keep a regression equivalence test for the zero-additional-loss adapter.

Retain original root/legacy source without moving or deleting it during initial consolidation. Extract/import only the supported package and test resources after plan approval; record the archive hash. Avoid adding extracted caches/build products to source control. Preserve all 38 tests, then establish separate tests for new behavior.

Keep an independent Cartesian Fermat ODE test implementation, extending the existing `test_release_core.py` comparison ideas for new endpoint families. This is independent numerical verification of the same physical model, not a second production engine or experimental validation. Legacy ODE equations may inform that harness; copying production invariant integration into the harness would not provide an independent check.

## 7. Missing Features and Technical Gaps

| Gap | Consequence | Priority |
|---|---|---|
| ISA state, viscosity/sound speed, humidity and P.453 refractivity | Atmospheric page cannot be implemented credibly from current package | Phase 1 mandatory |
| AGL/MSL/geopotential/ellipsoid conversion contract | Wrong atmospheric state, horizon and endpoint geometry | Phase 1 mandatory |
| Separate TX/RX roles, feeder losses, EIRP and threshold provenance | Uplink/downlink results can be misleading | Phase 1 mandatory |
| General ground/UAV ray boundary-value solver | Existing outward solver rejects equal/lower endpoint radius and misses initially descending elevated-station paths | Phase 2 mandatory before coverage |
| Path reconstruction, signed arrival directions, surface-clearance and diagnostics | Existing packaged result lacks coordinates/arrival angle and detailed failure taxonomy | Phase 2 mandatory |
| Independent ray endpoint/invariant/convergence verification | Existing tests cover restricted families only | Phase 2 primary scientific gate |
| Ray-based coverage and interval/root solver | No maximum UAV communication area exists yet | Phase 3 mandatory |
| Separate EER/geometric references and method comparison | No independent comparison service exists | Phase 3 mandatory; reference primitives in Phase 1 |
| Antenna masks applied to ray endpoint directions | Archive's nonnegative station mask can reject a valid direction below local horizontal | Phase 2/3 mandatory |
| Qt scientific pages, scenario store and exports | Current UI cannot meet standalone desktop target | Phase 4 mandatory |
| Frozen build and clean-machine tests | Current wheel/batch scripts require Python | Tiny compatibility check in Phase 1; full release in Phase 5 |
| Verified gaseous attenuation backend | Cannot claim automatic P.676 loss at any frequency | Optional release gate, see below |
| Terrain, clutter, multipath, rain/cloud statistics, antenna patterns | Idealized coverage may differ strongly from field behavior | Explicit limitations; later implementation |
| License and build compatibility decisions | Redistribution/build uncertainty | Resolve before release |

Endpoint-chord FSPL does not become a refractive power-transfer solution simply because a ray exists. Ray-tube spreading/focusing is unimplemented; initial coverage is explicitly conditional on that power approximation. Missing terrain/diffraction/multipath cannot be represented as solved physics. Computational cost and near-grazing conditioning are new major feasibility risks: cache profiles, refine adaptively, record timing, and prioritize solver verification ahead of UI breadth.

For a realistic student MVP, support three gas states: explicitly neglected design assumption, externally supplied loss/table with provenance, and a verified backend if completed. Unknown selected gas data makes the complete budget/range unavailable. This scope is an open approval decision: if automatic atmospheric attenuation is required for submission, the verified backend becomes mandatory before the release, rather than silently weakening that requirement.

## 8. Scientific Models and Physical Assumptions

### Model policy

Use deterministic ray tracing in a spherical, horizontally homogeneous atmosphere above a smooth surface as the primary model. Atmosphere is a reference estimate unless measured inputs are supplied. A measured surface observation is not a measured vertical profile. No probabilistic uptime, packet delivery, regulatory authorization or flight safety guarantee follows from positive margin. This is geometrical optics for a declared scalar refractivity field, not full-wave electromagnetic simulation.

| Model/reference | Intended use and applicable conditions | Release decision |
|---|---|---|
| ISA-compatible lower atmosphere, with U.S. Standard Atmosphere 1976 tables as verification source | Dry-air hydrostatic layers; geopotential altitude; initial 0–11 km geometric MSL envelope | Mandatory |
| ITU-R P.453-14 | Radio refractivity from temperature, dry pressure and water-vapour pressure; no absorption prediction | Mandatory, explicit dry/humid input basis |
| ITU-R P.835 | Reference atmospheric profiles, not weather at a coordinate; heights and seasonal/latitude regimes must follow selected edition | Optional profile provider; distinguish P.835-6 from later P.835-7 |
| ITU-R P.676-13 Annex 1 | Specific gas attenuation, 1–1,000 GHz, with pressure/temperature/water-vapour profiles and verified line data; method restrictions apply | Optional verified backend; no clamp below 1 GHz |
| P.676 Annex 2 | Approximate method, 1–350 GHz and its additional path/meteorological restrictions | Do not substitute without a documented applicability check |
| ITU-R P.838-3 | Specific rain attenuation `gamma_R = k_R R_rain^alpha` [dB/km], 1–1,000 GHz; polarization and frequency dependent | Later deterministic rain profile; rain rate alone does not define whole-path loss or availability |
| ITU-R P.840-9 | Liquid-cloud/fog attenuation, 1–200 GHz, small-droplet liquid-water model; needs temperature and liquid-water content | Later; no automatic ice/rain equivalence |
| ITU-R P.525-5 | Free-space spreading between antennas in the applicable far field | Mandatory conditional endpoint-chord spreading baseline; not a ray-tube model |
| ITU-R P.526 | Fresnel geometry and diffraction methods with obstacle/ground inputs | Approximate refracted-path clearance diagnostic now, labeled; diffraction later |
| ITU-R P.834-9 | Atmospheric refraction principles; existing reference exponential and outward tracer | Mandatory ray methodology/reference checks; general UAV branches still require implementation/verification |
| Geometric LOS reference | Straight segment over physical smooth Earth; vacuum/constant-index limiting geometry | Independent limiting-case reference, never a hidden fallback |
| EER reference | `k=1`, conventional `k=4/3`, or locally derived k within its approximation domain | Separate benchmark/diagnostic, never the primary propagation solver |
| P.528 / P.1812 / P.452 / P.618 | Potential aeronautical/terrestrial/interference/Earth-space extensions respectively | Assess exact domains before adoption; none is a generic drop-in UAV coverage model |

Do not apply both an effective-Earth-radius correction and explicit refractive ray curvature to the same calculation. Keep geometric LOS, radio-model visibility, Fresnel clearance, and received-power feasibility as separate outputs. Frequency validity belongs to each model, not to a shared UI frequency slider.

### Separate effective-Earth-radius reference

For a near-horizontal path with approximately constant gradient and `n` close to one, the P.834 effective-radius approximation is `k approximately 1/(1 + R_s*dn/dh)`. Use metres consistently: with gradient G in N-units/km, `dn/dh = G*1e-9 /m`. A conventional `k=4/3` is a chosen reference, not an exact solution for an arbitrary atmosphere. Record the gradient interval and assumptions; reject nonpositive or near-singular denominators. See [P.834-9, Annex 1 Section 2](https://www.itu.int/dms_pubrec/itu-r/rec/p/R-REC-P.834-9-201712-I!!PDF-E.pdf).

The derived-k comparison is disabled when a representative constant gradient is unjustified; show the profile's gradient variation rather than fitting k to ray results and calling it independent. Keep physical endpoint heights/ground distances common across methods. EER's transformed straight line is not a sampled physical refracted path; unsupported quantities remain null. EER agreement is an approximation benchmark, not proof of tracer correctness.

### Four distinct accuracy questions

1. Numerical verification: does the solver solve its stated equations within measured residuals/convergence bounds?
2. Physical-model fidelity: are spherical symmetry, scalar refractivity and geometrical optics appropriate for the scenario?
3. Environmental uncertainty: how well do the sampled profile, height datum, hardware and antenna attitude represent actual conditions?
4. Experimental validation: do predictions agree with independent observations at stated uncertainties?

Smaller integration error does not resolve the other three questions. Comparisons must identify which question is being tested.

### Verifiable reference register

These are source locations for implementation and review, not a claim of full conformance. Official catalogues/deployment documentation and standard-atmosphere sources were located during the audit; every future coefficient dataset and method must be edition-pinned and checked against its full primary reference before implementation. Existing archive tests retain their original reference editions.

1. [U.S. Standard Atmosphere, 1976, NASA-TM-X-74335](https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/19770009539.pdf): physical constants, geometric/geopotential definitions and reference tables. Use the lower-atmosphere equations; do not label it an implementation of all ISO/ICAO provisions.
2. [ITU-R P.453-14](https://www.itu.int/rec/R-REC-P.453-14-201908-I/en): refractivity.
3. [ITU-R P.676-13](https://www.itu.int/rec/R-REC-P.676-13-202208-I/en): gaseous attenuation target edition.
4. [ITU-R P.835 catalogue](https://www.itu.int/rec/R-REC-P.835/en): reference atmospheres; P.835-7 (2024) is listed, so third-party P.835-6 support must not be called the latest model.
5. [ITU-R P.838-3](https://www.itu.int/rec/R-REC-P.838-3-200503-I/en): rain coefficients and restrictions.
6. [ITU-R P.840 catalogue](https://www.itu.int/rec/R-REC-P.840/en): cloud/fog methods; choose an edition explicitly.
7. [ITU-R P.525-5](https://www.itu.int/rec/R-REC-P.525-5-202411-I/en): free-space attenuation.
8. [ITU-R P.526 catalogue](https://www.itu.int/rec/R-REC-P.526/en): Fresnel zones/diffraction; catalogue includes P.526-16 (2025).
9. [ITU-R P.834-9](https://www.itu.int/rec/R-REC-P.834-9-201712-I/en): effects of tropospheric refraction. Its primary text was checked again for this revision: Annex 1 Sections 1–2 support the bending/EER distinction; preserve the original edition-specific outward-ray comparisons and their scope.
10. [ITU-R study group 3 software/data/reference examples](https://www.itu.int/en/ITU-R/study-groups/rsg3/rwp3m/Pages/digprod.aspx): candidate independent gas-model reference cases; check data licensing and revision.
11. [Qt for Python deployment](https://doc.qt.io/qtforpython-6/deployment/index.html), [Qt/PyInstaller](https://doc.qt.io/qtforpython-6/deployment/deployment-pyinstaller.html), [Qt/Nuitka](https://doc.qt.io/qtforpython-6/deployment/deployment-nuitka.html).
12. [PyInstaller operating modes](https://www.pyinstaller.org/en/stable/operating-mode.html): one-directory debugging and one-file temporary extraction behavior.

## 9. Atmospheric Calculation Design

### Inputs, altitude and units

Store SI internally: geometric altitude `z_m`, geopotential altitude `H_m`, temperature K, pressure Pa, density kg/m3, viscosity Pa s, frequency Hz, humidity fraction 0–1. Convert to hPa only at explicit P.453/ITU adapter boundaries. Display K and Celsius (`T_C = T_K - 273.15`). Label vapour density separately from air density.

AGL conversion requires terrain MSL elevation at the UAV position: `z_uav_msl = z_ground_at_uav_msl + height_uav_agl`. Station antenna MSL elevation is site elevation plus phase-centre height AGL. Do not substitute station ground elevation at a distant UAV unless the user selects a uniform-ground scenario. Coordinates alone cannot provide terrain height offline without a dataset.

For geodetic ECEF mode, `h_ellipsoid = H_orthometric + N_geoid`; geoid undulation and source are mandatory or the conversion must remain unavailable. Do not identify MSL with the WGS-84 ellipsoid. The MVP idealized spherical mode instead uses a declared spherical MSL reference and uniform surface elevation; it is not a precise global datum transformation.

For ISA, convert geometric to geopotential altitude with the standard-atmosphere effective radius, `H = r_atm z / (r_atm + z)`, using `r_atm = 6,356,766 m`. Keep this distinct from the 6,371,000 m radio-geometry sphere. Document the approximation that MSL height is used as the standard-atmosphere geometric coordinate. An input of 11 km geometric is not 11 km geopotential.

### Dry atmosphere equations

Use `T0=288.15 K`, `p0=101325 Pa`, `g0=9.80665 m/s2`, `Rd=287.05287 J/(kg K)`, and tropospheric lapse magnitude `L=0.0065 K/m`:

```text
T(H) = T0 - L H
p(H) = p0 [T(H)/T0]^(g0/(Rd L))
rho = p/(Rd T)
a = sqrt(1.4 Rd T)
mu = beta T^(3/2)/(T + S), beta = 1.458e-6, S = 110.4 K
```

Apply this lapse expression only within its layer. If profiles are later extended above 11 km geopotential, use the isothermal layer pressure expression and continuous layer bases. Do not extrapolate the tropospheric lapse rate into satellite altitudes. Viscosity and sound speed use dry-air approximations even when a humidity overlay is supplied, unless a separate moist-air model is implemented and identified.

### Humidity and refractivity

Default mode is explicitly dry reference atmosphere: `e=0` is an assumption, not a humidity measurement. Offer measured local `T`, `p`, and RH or vapour pressure as an alternative local-state mode. A single local state does not silently replace the entire altitude profile. Supplied full profiles must include height coverage, units, source, timestamp and interpolation policy; bounded n(h) table ingestion is a first-release capability even when a user chooses a generated reference profile instead.

For RH-derived vapour pressure, use an edition-pinned saturation-vapour-pressure expression with declared water/ice convention and temperature range: `e = RH * e_sat(T)`. Reject invalid RH, nonpositive T/p and `e >= p`. Do not assume constant RH with altitude without exposing that model choice. Calculate moist density if requested as `(p-e)/(Rd T) + e/(Rv T)` with `Rv` documented; distinguish this from the dry reference density.

For the P.453 dry/wet decomposition, use pressures in hPa and T in K:

```text
N = 77.6 pd/T + 72 e/T + 3.75e5 e/T^2
pd = p_total - e
n = 1 + N*1e-6
```

Pin the exact edition/coefficient expression; do not accidentally mix total-pressure and dry-pressure forms. Test both the dry limit and humid calculations. Refractivity itself is dimensionless (customarily N-units); `n` is dimensionless. P.834 exponential refractivity is an alternative reference profile, not an ISA thermodynamic-state generator.

Gas backend, if implemented, computes specific attenuation at each state/frequency and integrates it along the selected path. A local specific attenuation [dB/km] and integrated path loss [dB] are separate outputs. Any supplied attenuation table must be frequency-bound and cover the path; no extrapolation or silent clamp. Choose a verified `itur` adapter or coefficient implementation only after version/domain/reference tests. Do not make the large optional atmosphere stack a dependency of satellite geometry or FSPL.

Atmospheric outputs carry model/version, input reference, normalized height, humidity basis, units, validity flags and warning list. Plot temperature, pressure, density and refractivity against altitude; mark the selected UAV altitude. Profiles have their own declared coverage, not an arbitrary `UAV + 500 m` extrapolation.

### Refractivity profile as the primary solver input

Create an immutable `RefractivityProfileSpec` that records the thermodynamic model or supplied `n(h)` source, original and normalized geometric heights, horizontal-homogeneity assumption, sample spacing, interpolation, validity interval, timestamp/temporal kind, frequency scope and boundary policy. Preserve the thermodynamic state alongside `n(h)` for traceability. Dry ISA + P.453, documented P.834 reference, and a bounded imported table are distinct profile choices. P.834 alone does not provide T/p/humidity outputs; leave those unavailable rather than reconstructing invented weather.

Convert geometric MSL height to `r=R_E+z` with the actual chosen spherical radius. Ground at nonzero MSL is a separate absorbing boundary, not a shift of the profile's altitude zero. Cover the complete explored ray domain, including any radial minimum below both endpoints. A table covering only the two endpoint altitudes is insufficient for initially descending rays. Use `outside='unavailable'` for bounded UAV profiles. Never force `n(top)=1` at 11 km to create an artificial vacuum transition; retain the existing explicit satellite vacuum-tail policy separately.

Initially retain piecewise-linear `n` interpolation and split integrals at every knot. Check `q'(r)=n+r*dn/dr` on each one-sided interval, profile positivity, derivative discontinuities, and coverage before solving. Reject duplicate/nonincreasing heights and unknown units. Do not smooth away a duct or extrapolate missing layers. Study profile-grid refinement separately from quadrature/shooting tolerances; use the same immutable profile for production/reference numerical comparisons where applicable. Temperature/RH uncertainty can strongly affect derivatives even when local N changes little.

Expose input resolution and source uncertainty; imported reference/synthetic profiles are not real-time weather. Full profile ingestion is mandatory for controlled computational experiments, while automatic online weather acquisition remains outside scope.

## 10. Communication Link Budget Design

Define two independent endpoint hardware records and a direction selector. Uplink is ground TX to UAV RX; downlink reverses endpoints but retains each endpoint's actual hardware. Different frequencies, powers, modem modes and receiver thresholds are allowed. A two-way command/telemetry coverage result is the intersection of both feasible regions, not the larger range.

The primary budget consumes a verified ray result, not a LOS/EER visibility flag. In a reciprocal, static scalar medium, a path may be reversed with correctly transformed tangent vectors; this does not make hardware budgets identical. Reuse a ray across directions only when frequency dependence, profile epoch and assumptions permit it. Otherwise solve each direction/frequency separately. Use launch direction for TX gain and direction toward the transmitter at the receiver for RX antenna gain; the latter is opposite the arriving propagation tangent.

Mandatory hardware: positive frequency, finite TX power, gains, nonnegative feeder/connector losses, receiver sensitivity plus source/mode, and required fade reserve. Antenna heights/positions belong to geometry. Optional pointing loss, polarization, bandwidth/noise figure/SNR and pattern data are explicit advanced inputs.

```text
P_tx_dBm = 10 log10(P_tx_W) + 30          (P_tx_W > 0)
EIRP_dBm = P_tx_dBm - L_tx_feed + G_tx_directional
FSPL_dB = 20 log10(4 pi D_chord f / c)    (explicit approximate spreading baseline)
L_propagation = FSPL + A_gas + A_rain + A_cloud + L_polarization
                + other separately declared propagation terms
P_rx_dBm = EIRP + G_rx_directional - L_rx_feed - L_propagation - L_environment
M_raw_dB = P_rx_dBm - sensitivity_dBm
M_design_dB = M_raw_dB - required_fade_margin_dB
```

If gains are boresight gains, deduct pointing losses separately once. If gains already come from the actual pattern direction, do not deduct the same pointing loss again. Define total link loss as feeder losses + separately represented pointing losses + propagation/environment losses, excluding gains and the fade reserve. Display that definition beside the result. Required fade reserve is a decision threshold, not a measured attenuation to be subtracted twice.

Sensitivity source modes are mutually exclusive: directly supplied datasheet/measurement threshold, or a theoretical estimate. For a thermal-noise estimate use `10 log10(k_B T_noise B / 1e-3) + NF + required_SNR` dBm, with the equivalent noise-temperature/reference assumptions stated (conventional `-174 dBm/Hz` is an approximation at approximately 290 K). Do not apply receiver noise figure twice. Require bandwidth in Hz and the modem SNR definition; label the output estimated. Never derive throughput or packet success from sensitivity/margin alone.

### Geometry is not electromagnetic power transfer

Retain `fspl_db(D_chord, f)` with the actual endpoint chord `D_chord=norm(x_rx-x_tx)` as the first-release spreading approximation, consistent with the existing package. Do not replace its distance by curved ray arc length and claim a validated refractive spreading model. A successful ray gives geometry and optical delay; received power additionally requires amplitude transport. Set the omitted focusing correction to an explicitly accepted `assumed` zero only in the conditional baseline; retain that assumption prominently in coverage/report labels. A request for full refractive spreading is unavailable until that model exists.

Ray-tube divergence, endpoint Jacobians, focusing/defocusing and caustics require separate amplitude-transport theory and independent validation. These are later research work. A chord occulted by the physical sphere does not automatically invalidate a verified refracted path, but extending the chord-FSPL power approximation to such paths is especially uncertain and must be flagged. Do not attach a full-wave-accuracy or operational-range claim to it.

Absorption is separate from bending: `A_gas = integral gamma(s) ds/1000` dB for gamma in dB/km and s in m, on the solved physical ray. Use a verified attenuation generator or a frequency-bound, correctly sourced table with complete ray coverage. A supplied total loss is not presented as an integrated model. Preserve P.676 frequency limits (including no 868/915 MHz clamp), source/version and unavailable handling. Refractive phase/group delay is never a power loss.

Reflections, diffraction, terrain/buildings, multipath, fading and interference are separate mechanisms. Neglected mechanisms need visible assumptions; missing required losses make the budget undetermined even when the ray geometry is computed. Explicitly assuming matched polarization or negligible ionosphere is permissible in the low-altitude baseline; it does not establish those effects from ray tracing.

Budget classifications: `unavailable` for required unknown data, unsupported branch or numerical failure; `blocked_within_model` only for an established propagation obstruction; `constraint_rejected` for verified ray directions/clearance outside selected design constraints; `below sensitivity` for negative raw margin; `insufficient reserve` for nonnegative raw margin below reserve; `meets conditional design threshold` otherwise. Preserve the detailed propagation reason alongside this budget classification. Do not apply a straight-line horizon clip to a refracted ray. No classification is an uptime percentage or a statement that all electromagnetic paths have been excluded.

Preserve a line-item loss ledger, model/version/source and assumption status for every term. A valid conditional calculation can explicitly neglect rain in a declared dry scenario; absence of a rain observation is not proof of zero rain. For low-altitude paths, explicitly declare the ionospheric contribution excluded by scenario scope. Polarization omission must likewise be visible as an alignment assumption or supplied loss.

## 11. UAV Coverage Calculation Methodology

### Definition and common physical geometry

Maximum estimated communication boundary is the farthest resolved feasible point within the declared altitude, azimuth, range domain, supported ray family and conditional power model. Return all resolved feasible intervals, unresolved intervals and boundary brackets. If farther candidates remain undetermined, call the result the farthest demonstrated feasible point, not an established global maximum. A finite sample scan cannot prove absence of arbitrarily narrow intervals; report search resolution and refinement evidence.

The first release uses constant UAV MSL altitude over a declared uniform smooth spherical surface. Let `R_s=R_E+ground_MSL`, `h1=station_antenna_AGL`, `h2=UAV_MSL-ground_MSL`, `r1=R_s+h1`, `r2=R_s+h2`. Actual ground arc is `d_ground=R_s*phi`. Actual endpoint-chord slant separation is computed stably as:

```text
D_chord^2 = (h2-h1)^2 + 4*r1*r2*sin(phi/2)^2
L_ray = integral ds
OPL = integral n ds
```

Report chord slant separation, curved ray length and optical path separately. Atmospheric height remains `r-R_E`. Never replace the physical radius with `k R_s` inside the primary tracer. Spherical idealized MSL coordinates and WGS-84 ellipsoidal coordinates are not interchangeable.

### Per-position computation and classification

1. Normalize endpoints, datums, antenna heights/attitude, frequency, environment and independent TX/RX hardware. Validate the altitude, profile and analysis domain before starting a sweep.
2. Construct the selected immutable `n(h)` profile, preserving its physical origin, full height coverage, interpolation, metadata and limits. Missing atmosphere is an unavailable primary result, not a request for automatic EER substitution.
3. Solve the TX-to-RX ray boundary-value problem in the supported physical model. Search the relevant nonducting branch families established by Phase 2, rather than accepting a nearby altitude intercept as an endpoint solution.
4. Check endpoint residuals, invariant/path reconstruction consistency, numerical diagnostics and complete profile coverage. Establish whether a supported ray connects the endpoints. Solver exhaustion, unsupported branch and proven blockage have different statuses.
5. Evaluate the physical ray against the smooth ground boundary, TX/RX pointing/elevation constraints using local ray directions, and any explicitly selected approximate clearance criterion. Chord occultation is a separate geometric-reference diagnostic, not a veto on a clear refracted ray.
6. Calculate path coordinates, bending, geometric/optical lengths, delay and any verified ray-integrated absorption. Combine them with the explicitly approximate spreading and loss ledger in Section 10. Geometry may be available while power remains undetermined.
7. Apply the correct receiver threshold/mode and required fade reserve. Evaluate each direction independently; reverse paths only under the declared reciprocity assumptions.
8. Classify communication feasibility as feasible, infeasible within the supported model/constraints, or unavailable/undetermined, with machine-readable reasons and human-readable limits. Positive conditional margin is not full-wave or field validation.
9. Search the finite range domain for every resolved feasible interval and communication boundary, retaining gaps and undetermined cells.
10. Refine ray tolerances, profile spacing and range sampling separately; report how the boundaries changed and whether the requested accuracy was attained.

| Underlying outcome | Coverage meaning | Required handling |
|---|---|---|
| Verified supported ray, clearance/masks pass, conditional margin meets reserve | Feasible under stated assumptions | Record path and budget provenance |
| Verified supported ray, insufficient power/reserve | Power-limited infeasible | Retain ray outputs and margin; not a propagation blockage |
| Ray established to intersect absorbing smooth ground, or complete supported-family search with justified domain exclusion | Blocked within the declared direct-ray model | State proof/domain and excluded diffraction/reflection; never claim no electromagnetic signal exists |
| Verified ray outside antenna mask or selected clearance criterion | Constraint-rejected | Preserve physical connectivity separately |
| Quadrature/shooting failure, invalid residual or work limit | Undetermined: numerical failure | Retry only under recorded settings; no hidden analytical fallback |
| Endpoint/profile requires unimplemented family, nonmonotonic q, multiple rays or non-spherical medium | Undetermined: unsupported model/branch | Do not color as a confirmed dead zone |
| Missing atmospheric samples, attenuation selected but unavailable, or incomplete radio | Undetermined: missing data | Retain whichever geometry outputs are valid |
| Feasibility continues to domain edge or farther regions are unresolved | Domain-limited result | Report lower bound/farthest demonstrated point and unresolved extent |
| Terrain/diffraction/multipath not modeled | Scope limitation on every result | Distinguish assumed smooth-surface coverage from field coverage |

Use the richer propagation status of Section 13 internally. A sampled failed ray alone is never evidence for `blocked_within_model`; the distinction must survive exports, comparisons and maps.

### Range search and convergence

Define a finite user-visible domain and physical minimum separation. For an aperture, `2 D_aperture^2/lambda` is one useful far-field criterion, not a complete antenna model. Missing aperture data require an explicit far-field assumption. Zero ground distance is valid for distinct vertically separated endpoints; coincident phase centres are invalid. No link over the station does not imply no farther feasible interval.

Begin with a moderate radial grid, then refine near connectivity/status changes, mask/clearance transitions, small margins and suspected extrema. Use branch-aware continuation as a speed aid, with bracket checks and independent reinitialization near boundaries. Never let continuation failure overwrite a previously valid family result. Only use a monotonic root solver where continuity/monotonicity is established within a resolved branch; otherwise subdivide and return intervals. Unresolved cells remain gaps, not interpolated feasible or infeasible data.

Suggested range-boundary precision target: bracket width no more than max(1 m, 1e-5 times the analysis scale), demonstrated by refinement. Tighten path errors sufficiently that the boundary does not move more than that target under another refinement; near grazing, return a wider uncertainty bracket if necessary. Numerical precision is not physical prediction accuracy. Record profile-grid, quadrature, shooting and coverage-grid settings separately, plus tested resolution below which interval detection is not assured.

Do not cap the ray search at the EER or geometric horizon. Derive any supported-ray domain bound from the profile and verified family analysis; otherwise use a finite declared range bound and flag clipping. At each boundary report the limiting cause: supported-path boundary, ground/mask/clearance, power/reserve, numerical/support/data uncertainty, or domain edge. Multiple simultaneous causes are allowed. Preserve a geometry-only boundary when full budget is unavailable, but never label it maximum communication range.

The constant-loss closed-form budget-only chord limit `c/(4*pi*f)*10^(L_allow/20)`, with `L_allow=Ptx+Gtx+Grx-feeder/pointing/other losses-sensitivity-reserve`, is retained as an analytical budget reference only. It neither proves ray connectivity nor provides the primary coverage boundary. A separate method result may combine it with EER for comparison, visibly labeled as analytical reference coverage.

### Independent EER/geometric comparison

For the geometric reference, the exact smooth-sphere two-height tangent distance is `R_s*[acos(R_s/(R_s+h1))+acos(R_s/(R_s+h2))]`. It is a vacuum/constant-index limiting check. For EER, define the approximate transformed horizontal range `R_eff*[acos(R_eff/(R_eff+h1))+acos(R_eff/(R_eff+h2))]`, where `R_eff=k*R_s`, and compare this engineering ground-range estimate to the physical `d_ground`. Document the transformation; do not turn its transformed central angle into a physical ECEF endpoint angle.

Run `k=1`, `k=4/3`, and justified derived-k cases independently on compatible physical heights/hardware. Each uses its own connectivity predicate and labeled common budget assumptions. Differences reveal approximation behavior; EER is not sufficient proof of the tracer. Only an explicitly selected reference run may show analytical coverage when ray results are undetermined. Preserve both results and statuses; never relabel reference data as ray results.

### Fresnel, area and plots

Evaluate clearance relative to the sampled physical refracted centreline and the smooth surface. A first-release diagnostic may use `r_F(s) approximately sqrt(lambda0*s*(L_ray-s)/L_ray)`, with vacuum wavelength and arc distances, projected in the local normal plane. Identify this as a paraxial, weak-refraction estimate; it is not a rigorous Fresnel surface in an inhomogeneous medium. Test that it reduces to the conventional straight-path expression in vacuum. Keep a chord-based reference diagnostic separately labeled if useful.

Choose path sampling fine enough to locate minimum surface clearance; use geometric minimization between samples or a convergence bound, not endpoints alone. A 60% zone criterion is a selectable design heuristic, not proof that diffraction/multipath is negligible. It is diagnostic by default; if enforced, the approximate criterion and its influence on coverage must be visible. Near grazing or strong gradients it may be unreliable; warn or mark the diagnostic unavailable. Full refractive Fresnel/second-variation amplitude theory and diffraction are deferred.

For azimuth-independent profiles/constant gains, rotate resolved radial intervals into disks/annuli. Do not fill unresolved gaps. Use actual ground distance on axes; annotate ray-connectivity and conditional chord-FSPL assumptions. A planar disk area `pi*d_ground^2` is a local approximation; spherical cap area is `2*pi*R_s^2*(1-cos(d_ground/R_s))`. For annuli subtract inner from outer area; provide resolved area and unresolved extent instead of an unjustified total. No terrain-aware map claim is permitted.

Directional patterns/azimuth sweeps can follow; define heading/pitch/roll and coordinate frames and integrate actual feasible intervals per angle. Altitude sensitivity reruns the full ray/connectivity/budget process, not a horizon formula alone. Show ray-only and communication limits, undetermined bands, conditional margins and separate analytical-reference curves. Neither altitude monotonicity nor outward connected coverage is assumed.

## 12. Ray-Tracing Reuse Strategy

### Governing equations and inspected implementations

With elevation theta measured from the local horizontal in the source-to-receiver direction, both implementations use scalar `n(r)` in a spherically symmetric atmosphere and the Bouguer invariant `b=n*r*cos(theta)`. The root ODE is:

```text
dr/ds = sin(theta)
dphi/ds = cos(theta)/r
dtheta/ds = cos(theta)*(1/r + (dn/dr)/n)
dQ/ds = n-1                         Q = integral (n-1) ds
dA_gas/ds = gamma/1000               gamma in dB/km
```

The root implementation uses SciPy `solve_ivp(method='DOP853')`, dense path output and `brentq` launch-angle shooting. The supported package instead integrates the invariant radial equations, with adaptive vector Simpson quadrature and 52 bisection iterations for b. For an outward radial leg, the inspected formulation is equivalent to:

```text
q(r) = n(r)*r
dphi/dr = b/[r*sqrt(q(r)^2-b^2)]
ds/dr = q(r)/sqrt(q(r)^2-b^2)
```

It splits layers at profile knots and uses `r=r_source+t^2` to regularize tangency at the source. This existing transformation is not automatically a general turning-point solver. Both methods describe geometry, not electromagnetic spreading. Neither includes terrain, reflections, diffraction, horizontal gradients or full-wave interference.

| Capability | Root [raytrace.py](raytrace.py) | Packaged `cubesat_link.neutral.trace_spherical` |
|---|---|---|
| Source/receiver heights | `r0=R_E+h_ground+h_ant`, target `R_E+h_uav`; config requires UAV above station | Target norm must be strictly greater than station radius (`rt<=r0` rejected); station altitude is ellipsoidal/spherical phase-centre height, not AGL |
| Arbitrary valid endpoint connection | No; terminates on upward crossing of target radius, with angle shooting assumptions and nonconnecting fallback rays | No; higher receiver on outward radial branch only; endpoint-angle solve within that family |
| Initially descending paths | Negative launch angles are attempted near a surface-grazing formula, but full family completeness/validity is unverified | Not searched; elevated station can miss a clear path needing initial descent |
| Equal/lower receiver radius | Disallowed by normal input contract; reverse propagation not implemented | Rejected; no general endpoint reversal API |
| Grazing and simple radial minimum | ODE may pass a radial minimum before an upward target event; grazing formula/ground offset and bracket require tests | Source tangency handled on outward branch; internal radial minimum and two-leg grazing path absent |
| Ducting/turning/multiple rays | Equations may evolve such trajectories, but shooting/event policy does not search or verify them | Rejects `q'<=0`; no atmospheric turning/trapping/multiple-ray family search |
| Coordinates and angles | `path_r`, `path_phi`, launch theta, arrival theta and geometric angle are returned | Launch apparent elevation and total bending returned; arrival is calculated locally but not in `NeutralRay`; no path coordinates/tangents exported |
| Endpoint residual/failure | No explicit metric; target event is not endpoint proof; returns None or nonconnecting fallback; no separate `sol.success` contract | `endpoint_residual_rad`, cutoff 1e-8 rad; numerical/domain/branch issues share `not_computable` plus reason |
| Ground clearance | Event at `r_surf-0.5 m`; does not provide complete clearance diagnostics | `ground_clear=r0>=R_E`, justified only by its outward-family assumptions; no general path-to-terrain clearance calculation |
| Length/delay | L and Q; Q/c omits curved-path geometric excess relative to vacuum chord | L, Q, `L-D_chord` and total excess; nondispersive excess delay in API |
| Attenuation | Integrates supplied `medium.gamma`; missing provider prevents full root workflow | Integrates supplied gamma table at its exact frequency; no P.676 generator |
| Evidence | Original medium modules/test absent; static review only | Existing vacuum/zenith/independent Cartesian RK4 and other tests passed in original 38-test audit; no evidence for new branches |

No current implementation connects all valid UAV endpoints. The packaged routine is the stronger baseline because it exposes missing physics, controls boundaries and has independent numerical comparisons; its tests do not verify downward, equal-height or internal-minimum cases. Preserve `NeutralProfile`, `p834_reference_profile`, old `trace_spherical`, delay definitions and all tests; extend through a separate API instead of rewriting already tested outward calculations.

### Planned first functional ray release: bounded nonducting families

Use actual spherical geometry with `q'>0` over the explored profile and an absorbing smooth ground boundary at `R_s`. Support radial monotonic paths in either direction, equal-height endpoints where a nonradial path is required, and a simple inward-then-outward leg with one radial minimum at or above the surface. That minimum occurs even for a straight vacuum chord between elevated points; it is distinct from atmospheric trapping/ducting caused by a more complicated q profile.

Proposed additive algorithm in `trace_spherical_between`:

1. Accept generic source and receiver spherical Cartesian endpoints, a positive physical radius, separate surface radius, profile, frequency and configurable solver settings. Spherical symmetry confines the ray to the plane through the centre and endpoints; solve there and map samples back to Cartesian coordinates. Validate radii/frame, finite values, profile coverage and the declared short-arc/local UAV domain. Reject coincident endpoints; handle radial degeneracy explicitly and avoid antipodal/long-path ambiguities in the first release. Retain the neutral profile's existing n>=1 domain (including vacuum n=1); do not silently broaden its physical contract.
2. Reuse layer-split invariant integrals for radial-monotonic branches, reversing direction explicitly when the receiver is lower. Equal-height endpoints need the internal-minimum branch except for the invalid coincident case. Validate radial/zenith/nadir limits without artificial 89.9-degree caps.
3. Add the single-minimum family using `q(r_min)=b` and two radial-leg integrals between `r_min` and the two endpoints. Require `r_min>=R_s`. Use a separately verified square-root change of variable about `r_min`, split at knots, and handle one-sided derivative limits there. Do not evaluate through an imaginary square root or clip an invalid branch into existence.
4. Bracket roots by branch over admissible b/minimum-radius intervals. Establish angle-versus-b behavior and family completeness for the published domain; monotonic q alone must not be treated as an unproved guarantee of unique BVP roots for every supplied profile. If roots/multiplicity cannot be resolved, return unsupported or undetermined. Do not arbitrarily select a discovered path and call it the only ray.
5. Reconstruct cumulative arc length/angle and Cartesian path samples with launch and arrival unit tangents. Verify endpoint and invariant residuals against that reconstruction. Derive signed elevations consistently; keep receive look direction distinct from the incident tangent. Smooth-surface minimum clearance requires minimization per leg, not a check of station radius alone.
6. Return L, Q, OPL, total delay and optional absorption from the same physical path. In the nondispersive approximation `OPL=L+Q`, `t=OPL/c`, `excess_delay=(L-D_chord+Q)/c`. Group delay requires group index if a dispersive refractive model is added; do not silently call phase index a broadband group index.
7. Preserve solver diagnostics (branch, root bracket, endpoint residuals, quadrature errors/work, reconstruction sampling and limits) and distinguish blocked/unsupported/numerically failed/missing-data results before link-budget use.

This is a proposed extension, not a proven implemented algorithm. Derive the branch brackets, singular limits and admissible-domain proof during Phase 2 and verify them independently. If the expanded integral solver cannot meet the tests, revise that focused algorithm or the published support envelope before coverage release; do not discard verified outward functionality or route failures to EER. The first research milestone may demonstrate restricted outward rays, but it cannot claim general elevated-station coverage.

Initial targets for new successful rays: angular endpoint residual <=1e-8 rad and Cartesian endpoint error <=0.1 m over the declared local domain, with tighter convergence where needed for the requested boundary bracket. A stricter existing reference tolerance remains intact. Report failure to attain tolerances; never reduce physical input uncertainty by displaying more digits.

### Deferred physics and reproducibility

Atmospheric ducts/trapping, upper turning layers from nonmonotonic q, multiple eigenrays/caustics, terrain intersections/reflections, diffraction and horizontally varying n are later capabilities. Physical branches outside the first-release envelope remain unsupported even if the old ODE can produce a curve. Ray-tube amplitude and rigorous refractive Fresnel geometry are separate later requirements.

Record endpoints/datum, model edition, profile samples/hash, frequency, branch/settings, Earth/surface radii and library version. No random numbers occur in the inspected core. Reproducibility is not validation; preserve all old CubeSat results/API behavior while adding the new scientific capability.

## 13. Proposed Software Architecture

Maintain two installable packages in one repository: preserved `cubesat_link` and new `uav_cas`. A modest multi-package repository is justified by the existing dependency-free library and future CubeSat reuse; avoid microservices, a database server or a general plugin framework.

Dependency direction:

```text
Qt views -> controllers/workers -> application services
                                  |-> atmosphere/profile construction
                                  |-> RayTracingPropagation -> cubesat_link BVP/path API
                                  |-> EffectiveEarthRadiusReference (isolated)
                                  |-> GeometricLOSReference (isolated)
                                  |-> comparison service -> compatible method results
                                  |-> coverage + conditional link budget
                                  |-> scenario/export
Figure builders <--------------------- immutable calculation results
```

Neither engine imports Qt, Streamlit, Matplotlib or persistence code. Services accept validated values, return immutable numerical results, and never show dialogs. Figure builders consume results and return figures; the GUI owns canvas/backend selection. Scenario storage handles only versioned JSON, never pickled interpolators or arbitrary executable expressions.

Use frozen dataclasses and enums with unit-suffixed field names. Proposed contracts: `AltitudeSpec`, `GroundSite`, `UavPosition`, `RadioEndpoint`, `LinkDirection`, `AtmosphereSpec`, `RefractivityProfileSpec`, `PropagationRequest`, `SolverSettings`, `PropagationResult`, `RayPath`, `CoverageRequest`, `Scenario`, `AtmosphereResult`, `LinkBudgetResult`, `CoverageResult`, `ComparisonResult`, `ModelProvenance`. Arrays may use NumPy inside the UAV package but must serialize to ordinary numbers/lists at export boundaries. These types are planned; existing library names and meanings remain stable.

### Explicit propagation-method interface

Define a small `PropagationMethod` protocol with `solve(request: PropagationRequest) -> PropagationResult` and declared capabilities. Request includes physical endpoints, Earth/surface model, frequency, profile reference, settings and method-specific options; incompatible options are rejected rather than ignored. `RayTracingPropagation` is the default production method. `EffectiveEarthRadiusReference` and `GeometricLOSReference` are comparison implementations. EER's k value belongs exclusively to its options, never the primary ray request. Methods may share normalized immutable inputs and unit helpers but not mutable state or one another's derived geometry.

| Method | Inputs and output basis | Role |
|---|---|---|
| `RayTracingPropagation` | Physical sphere, n(h), supported BVP; sampled physical path, ray angles, length/OPL/delay and numerical evidence | Primary; required for ray-based communication coverage |
| `EffectiveEarthRadiusReference` | Common physical heights/range plus declared k/gradient mapping; transformed straight-line geometry and approximate horizon | Benchmark/diagnostic; physical ray coordinates/OPL remain unavailable unless a separately justified reconstruction is added |
| `GeometricLOSReference` | Actual endpoint chord and physical surface intersection; straight path and geometric angles; D/c only under explicit vacuum assumption | Analytical limiting reference; k=1 EER should agree on compatible geometry |

Common result envelope: method ID/version, physical-input hash, model assumptions, status/reason codes, Earth/datum, units, profile hash where applicable, `endpoint_chord_m`, source/receiver IDs and validity domain. Optional fields distinguish actual physical paths from transformed reference representations. Do not fill missing EER bending, absorption integrals or physical delay with zero. A reference's predicted horizon is not a ray solver residual.

`RayPath` carries arc-length and position samples, physical tangent vectors at both ends, signed elevations and angle convention, b/invariant diagnostics, minimum surface clearance, branch identity, geometric length, Q, OPL and nondispersive delay. Path sampling settings are distinct from solver accuracy. Preserve nulls for unavailable attenuation/amplitude physics; status per field can reuse the existing `Effect` concept.

### Propagation status and comparison contracts

Use an enum such as `solved`, `blocked_within_model`, `unsupported_model`, `unsupported_branch`, `missing_data`, `numerical_failure` and `invalid_input`, plus stable reason codes (`ground_intersection`, `endpoint_residual`, `quadrature_limit`, `nonmonotonic_q`, etc.). Invalid input may raise a structured error at the service boundary. A successfully solved path can still fail antenna/clearance or radio constraints; preserve that distinction. Search-domain clipping is a coverage status, not a fabricated failed ray. Old `NeutralRay.status` and `Effect.status` remain unchanged; the new adapter maps their limited outcomes conservatively and does not infer confirmed blockage from a `not_computable` reason string.

The comparison service runs selected methods independently on the same compatible scenario revision and physical endpoints. It records unmatched model domains, masks, gradients and attenuation assumptions. Compare common geometry/status outputs; compute differences only where both quantities have compatible physical meanings. EER cannot supply a physical optical-delay difference without a separately declared model; show unavailable rather than zero. Preserve each method's feasible intervals, domain/resolution and conditional power assumptions. No reference result repairs or overwrites a failed ray result.

Each result includes normalized inputs/input hash, calculation timestamp, package/model versions, component statuses/reasons, assumptions, warnings, and solver diagnostics. Store values in SI plus explicitly dimensioned logarithmic units. Do not infer units from magnitude. Input schema version and engine version are separate; preserve old CubeSat JSON schema 1.0, and introduce a distinct UAV scenario schema with explicit migrations. Reject unsupported future versions and nonfinite numbers. Unknown fields should produce an actionable error rather than disappearing.

Represent invalid input as structured validation errors with field paths. Treat missing model data as an unavailable result; treat numerical failure as a distinct diagnostic. Catch unexpected exceptions at the application boundary, retain the previous result labeled stale, log a traceback locally and show a useful message. Do not replace exceptions or missing losses with zero.

Use explicit strategy selection, not dynamic code loading. Cache profiles and rays by normalized endpoints, profile hash, frequency where relevant, method/branch and solver settings. Never reuse a loose-tolerance ray as tighter evidence or cache incomplete results as solved. Measure the existing pure-Python quadrature cost before selecting worker parallelism; start with sequential headless correctness, then QThreadPool for responsiveness and a bounded process worker only if profiling justifies CPU parallelism. On Windows the frozen process entry point/start method must be tested. Add cooperative cancellation between solves and iteration/work limits inside long solves; workers never mutate widgets. Discard results whose scenario revision no longer matches the current request.

## 14. Recommended Directory Structure

New package/module paths below are proposed, not created. The existing plan, archives and retained prototype appear for context. Preserve current root source/archive files during initial import; any later relocation requires a separate reviewed change.

```text
UAV_comm/
  plan.md
  CommZipFile/                         # original immutable handoff archives
  app.py, config.py, ...               # original prototype, retained initially
  packages/
    cubesat-link/
      pyproject.toml
      cubesat_link/
        neutral.py                   # preserve old trace_spherical API/behavior
        ray_bvp.py                   # planned additive trace_spherical_between
        ray_types.py                 # generic endpoints/path/settings/results
        ...                          # existing API, physics, schemas preserved
      tests/                          # original eight modules plus new BVP tests
      examples/
      docs/
  src/uav_cas/
    __init__.py
    models.py                         # public immutable input/result types
    units.py
    validation.py
    atmosphere/
      isa.py
      humidity.py
      refractivity.py
      profiles.py
      gas.py                          # optional verified adapter, not a fake model
    propagation/
      contracts.py                    # PropagationMethod, request/status contracts
      geometry.py                     # physical datums, endpoints, ray directions
      ray_tracing.py                  # primary adapter to cubesat_link BVP
      eer_reference.py                # isolated k reference calculations
      geometric_reference.py          # physical straight-path limiting cases
      fresnel.py                      # explicitly approximate path diagnostic
      losses.py
    link_budget.py
    coverage.py
    comparison.py                     # independent method runs and compatible deltas
    services.py
    scenarios.py
    schemas/scenario-v1.schema.json
    visualization/
      atmosphere.py
      ray_paths.py
      link_budget.py
      coverage.py
      comparison.py
    export/
      csv_export.py
      json_export.py
      figures.py
    desktop/
      __main__.py
      main_window.py
      controllers.py
      workers.py
      settings.py
      pages/
        atmosphere.py
        ray_propagation.py
        link_budget.py
        coverage.py
        model_comparison.py
        export.py
      resources/
  tests/
    unit/
    numerical/
      test_ray_analytic.py
      test_ray_endpoints.py
      test_ray_independent_ode.py
      test_ray_convergence.py
      test_ray_failures.py
      test_eer_benchmarks.py
    integration/
    gui/
    fixtures/                         # sourced references and synthetic cases separate
  examples/uav/
  studies/ray_vs_eer/                 # later study manifests/results, not claims
  docs/
    physics.md
    verification.md
    limitations.md
    user-guide.md
    references.md
  packaging/
    uav_cas.spec
    version_info.txt
    icons/
  scripts/
    verify_release.py
    build_windows.ps1
    smoke_qt_freezer.py               # tiny future compatibility check only
  pyproject.toml                      # UAV package, extras and test configuration
  requirements-release.lock
  LICENSE                            # after ownership/terms are established
  THIRD_PARTY_NOTICES.md
```

Keep legacy package interfaces stable. The new generic BVP/path API belongs in the reusable library, exported under an additive version only after its tests pass; UAV atmosphere/hardware/coverage policies stay in `uav_cas`. No SciPy/Qt requirement is added to the preserved package merely for a verification harness or desktop integration. File names in this tree are proposed responsibilities, not files created by this revision.

## 15. Desktop UI/UX Design

Recommend PySide6 Qt Widgets with a left navigation rail and a central stacked-page workspace. Qt Widgets offers native desktop controls, tables, accessibility and stable Matplotlib integration without introducing a web server. QML is unnecessary for this engineering MVP.

Shared layout: top bar with project name, save/open, scenario revision and primary method badge; left rail with six scientific pages; main page with grouped inputs on the left and results/plots on the right; bottom status area with model validity, convergence, calculation state and local log access. A collapsible assumptions panel remains available on every analysis page. Distinguish editable inputs, selected assumptions and read-only results through labels as well as color. A separate dashboard is deferred; summary indicators can sit above relevant results without delaying scientific workflows.

| Page | Proposed layout and behavior |
|---|---|
| Atmospheric Analysis | Altitude/datum and ground elevation; thermodynamic/humidity or imported-profile source; T/p/rho/N/n/gradient plots; height coverage, interpolation and q-domain diagnostics |
| Ray Propagation Analysis | Ground/UAV endpoints, profile and solver controls; physical curved-Earth cross-section and ray centreline; launch/arrival angles, bending, chord/ray/optical lengths, delay, minimum clearance and residual/convergence panel; unsupported branches explained |
| Link Budget Analysis | Independent ground/UAV hardware and direction; selected verified ray summary; conditional received power/margin; waterfall and provenance ledger; spreading/absorption assumptions prominent |
| Communication Coverage Analysis | Altitude/domain/ray settings; resolved feasible intervals and top-down coverage with hatched undetermined regions; altitude sensitivity; separate path/power/constraint/solver/data/domain limits; no automatic EER clipping |
| Model Comparison | Ray tracing versus k=1/k=4/3/justified derived-k reference; compatible endpoint/profile assumptions, boundary/angle differences and convergence evidence; scenario-to-scenario comparisons as a tab |
| Results and Export | Inputs, profiles, ray samples, diagnostic settings/residuals, model versions/references, conditional loss ledger and unresolved intervals; CSV/JSON/plots; preserve method identity and unavailable outputs |

Use unit selectors next to values, explanatory tooltips, grouped TX/RX losses, keyboard navigation and a clear Calculate button. Switching display units must not change the stored physical value. Explain chord versus ray length, physical versus effective Earth, and numerical failure versus modeled obstruction in student-friendly tooltips. Reference k controls appear only in Model Comparison/reference mode. An explicitly selected analytical run has a persistent reference badge; it never replaces a failed ray plot automatically. For long ray sweeps, show progress, current work limits and Cancel. Preserve the last successful result as explicitly stale after edits, never as apparently current. Disable export of a result with unlabeled mismatched inputs.

Default examples must say Synthetic demonstration. Receiver sensitivity should require a hardware/mode source for a user scenario; do not present the prototype's -105 dBm as a universal ELRS specification. Warn at model-domain boundaries and explain unavailable values without alarming crash dialogs. Use readable scientific formatting, configurable decimals and explicit units on axes/colorbars/tables.

Support window resizing, scrollable input panels, 100–200% DPI and plot zoom/pan. Avoid color-only status encoding. Light theme is sufficient for the first functional UI; dark theme should use the same plotting palette contract when added. All page text and exported methodology should be English initially. Keep internal file paths, implementation class names and stack traces out of normal user flows.

Ray plots must state vertical exaggeration and show the actual Earth/surface model; an effective-radius reference diagram needs a separate frame/label so it is not mistaken for a physical ray. Show propagation tangents and receive look direction consistently. Report finite sampling and approximate Fresnel envelopes; do not draw an unavailable path as a dashed successful connection. Expandable numerical details belong in normal scientific analysis, while tracebacks remain in logs.

## 16. Windows Executable Packaging Strategy

Start with PyInstaller one-directory, windowed mode on Windows x64, built in a clean, pinned environment. Deliver a portable folder ZIP containing `UAV-CAS.exe` and its resources; the user extracts the complete folder and double-clicks the executable. This satisfies the no-Python/no-terminal requirement. The executable alone is not the entire distribution.

Before major UI work, Phase 1 includes a time-boxed compatibility smoke test: a minimal Qt window, one Matplotlib canvas, bundled schema access and one preserved library reference calculation frozen in one-directory mode. Record the interpreter/Qt/freezer combination and launch it without the developer working directory. This is planned risk reduction, not a completed build or scientific gate; no smoke code or packages are created/installed in this plan revision. Keep it isolated from the solver and cap its scope rather than expanding it into the application.

One-file builds can be evaluated after one-directory success. They unpack bundled libraries to a temporary location and may have slower startup and additional security-scanner interactions. Do not sacrifice reliability to force a single file. An installer wrapping the tested one-directory build is a later usability improvement.

| Option | Benefits | Costs and decision |
|---|---|---|
| PyInstaller | Straightforward freeze workflow, common Qt/NumPy/Matplotlib hooks, no separate application compiler design | Choose first; test collected plugins/data and exact Python support |
| Nuitka / `pyside6-deploy` | Official Qt deployment route exists; compiled distribution may improve some workloads | Requires compiler/toolchain and longer builds; assess only if measured deployment/performance issues justify it |
| Streamlit launcher | Reuses prototype appearance | Reject for target: browser/server model, missing modules, Python-dependent launcher |

Bundle Qt platform plugin `qwindows`, required image-format/style plugins, fonts/icons, Matplotlib data, selected numerical binary libraries, JSON schemas and any licensed scientific coefficient tables. Keep only one Qt binding. Use resource APIs/Qt resources and application-relative read-only assets; never developer-specific absolute paths. Set Windows icon, product/version metadata and useful executable name. Do not include `.venv`, test data unnecessarily, secrets or whole source archives in the app bundle.

Store preferences through QSettings or application-specific configuration under the user's app-data location. Store logs under a writable local app-data folder with rotation. User project files belong at a chosen user location. Never write settings beside the executable or inside a one-file extraction directory. Crash reporting is local and user-exported; no automatic uploads.

Choose the Python minor after checking binary wheels and freezer compatibility for the complete stack. The existing 3.15.2 environment demonstrates only that the dependency-free library tests run; it does not establish that PySide6, SciPy or PyInstaller support that environment. A conservative 3.12/3.13 candidate is reasonable, subject to current support/security and exact dependency checks. Do not silently raise the existing library's minimum Python version.

Release workflow: lock reviewed dependencies and hashes; build the preserved library wheel; run tests; install that wheel plus UAV package in a clean build environment; freeze with a versioned spec; perform clean-machine acceptance; record tool versions, source revision/archive hash, artifact checksum and test report. Reproducible means a traceable repeatable build; do not claim byte-identical binaries until timestamps/toolchain nondeterminism have been addressed.

Validation checklist:

- Test on documented Windows 10 and 11 x64 builds with no Python, no network and a standard user account. Verify the selected Qt version supports the targeted Windows versions.
- Start from Explorer and from a different working directory; test paths with spaces and non-ASCII characters, read-only installation directory, 100/150/200% DPI and ordinary display resolutions.
- Open/save scenarios, run all mandatory analyses, export files, cancel a sweep and reopen the application. Verify bundled formulas/data give the same results as the source tests.
- Check Qt plugins, Matplotlib fonts, dependency DLLs, schemas, exception logs, startup time and memory. Initial target: ready within 10 seconds on the recorded reference laptop; revise only from measured evidence.
- Verify offline operation, recovery from invalid/corrupt files and clear unavailable-model behavior. No missing dependency may silently alter model selection.
- Verify frozen ray endpoints/delay/diagnostics and failure classifications against source fixtures. Test cancellation and any process workers; no failure may trigger an unlabeled EER result.
- Review library/application licensing, Qt LGPL/commercial obligations, numerical packages and redistributed coefficient/data terms; include required notices. Review signing and antivirus/SmartScreen behavior before wider distribution.
- If adding an installer, test install/update/uninstall without removing user scenarios. Signing is recommended for distribution, not a substitute for numerical verification.

## 17. Dependencies and Technology Decisions

| Technology | Recommendation | Rationale and constraints |
|---|---|---|
| Python | Retain | Existing scientific code and approachable student workflow |
| Existing `cubesat-link` | Preserve independent dependency-free package | Already tested core; no GUI dependencies |
| NumPy | Use in UAV analysis/plots | Arrays and vectorized sweeps; not required by old library |
| SciPy | Recommended development-only independent solver comparison; runtime only if justified | DOP853/independent shooting can test extended invariant solver; retain dependency-free production library where practical |
| PySide6 | Choose Qt Widgets | Native desktop UI and offline executable support |
| Matplotlib | Choose QtAgg canvas in desktop layer | Reuse plotting knowledge, scientific axes, export, pan/zoom |
| pytest | Use for new tests; retain unittest suite | Existing unittest tests can run under pytest without rewriting |
| pytest-qt | Development-only when GUI work starts | Signal/event-loop integration tests |
| `itur` | Optional version-pinned model adapter after evaluation | API/version/data/domain checks necessary; do not assume latest ITU edition or accuracy from package name |
| pandas | Omit initially | CSV and simple scenario tables do not justify it; Qt models/std-lib CSV suffice |
| Streamlit | Retain only as legacy source | Not part of new desktop dependency graph |
| PyInstaller | Primary freezer | One-directory first |
| Nuitka | Alternative later | Toolchain/compatibility costs must be measured |
| JSON/CSV | Standard library | Human-readable scenarios and portable numerical export |
| PDF stack | Defer | PNG/CSV/JSON satisfy first export milestone |

Use minimal runtime extras for desktop and optional atmospheric capabilities; keep testing/build tools out of end-user model dependencies. Pin the release environment after compatibility testing, while keeping library metadata honest about its tested minimum/maximum. Record exact `itur` recommendation versions and packaged data hashes. Avoid introducing ORM, web services, remote database, GIS stack or unit framework solely for hypothetical future use; unit-suffixed dataclasses and tested boundary conversions suffice initially.

## 18. Numerical Verification and Validation Strategy

### Evidence retained from the original audit

The inspected tests were executed using the configured existing interpreter and `-B -m unittest discover -s tests -v` in the temporary source copy. Child CLI tests inherited bytecode suppression. Result: **38 tests, 0 failures, 0 errors, exit code 0; unittest reported 4.969 seconds**. No packages were installed. The archive's release/build scripts were not run. This was a source-copy test, not a fresh installed-wheel environment test; wheel package bytes were independently compared to source. Historical clean-wheel claims in `docs/verification.json` remain historical evidence.

This revision reinspected the root tracer, archive `neutral.py`/`api.py`, and relevant neutral/release-core tests to reassess the new architecture. It did not rerun tests, create new tests, install dependencies, or verify any planned solver extension. The original numerical results remain evidence for release 0.2.0's tested families only.

| Test module | Count | What the current passing cases establish | What they do not establish |
|---|---:|---|---|
| `test_api.py` | 7 | Vacuum budget, missing-data handling, path blocking, provenance retention, no delay-as-loss, duplicate guards | Actual weather/RF performance |
| `test_budget.py` | 3 | FSPL scaling/rounded-reference difference, hand ledger, invalid values | Receiver behavior, interference or availability |
| `test_geometry.py` | 6 | ECEF/ENU special cases, smooth Earth, mask, time gaps and window clipping | Terrain, geoid conversion or general orbit accuracy |
| `test_interface.py` | 4 | CLI/API equality for four fixtures, schemas, error codes, unit/frame rejection | GUI/frozen executable or complete JSON Schema implementation |
| `test_ionosphere.py` | 3 | Finite analytic electron integrals, first-order delay/Faraday, ideal polarization | IRI/IGRF, scintillation, absorption or measurements |
| `test_neutral.py` | 7 | Vacuum/zenith limits, gas-table integral, boundary/domain guards, refraction horizon and grid comparison | P.676 generation, all ray families, real atmosphere |
| `test_providers.py` | 5 | Metadata/epoch/path binding and bounded profiles; explicit P.676 unavailability | Correctness of external measured input data |
| `test_release_core.py` | 3 | Independent Cartesian RK4 comparison and synthetic orbit sample convergence, Earth consistency | Production field validation or whole-program ITU conformance |

### Preserve all 38 tests unchanged

Retain all eight modules/counts above without changing their fixtures, assertions or old API calls. In particular, preserve all seven `test_neutral.py` cases and all three `test_release_core.py` cases, including WGS-84 rejection, unsupported duct/boundary behavior, the restricted outward horizon, the P.834 comparison/grid check and independent Cartesian Fermat comparison. These remain correct tests of the old API, not limitations to erase from its contract. Preserve the other 28 tests, including explicit P.676 unavailability, schema 1.0, incomplete budgets and satellite contact windows. A new API accepting additional branches must have separate tests; it must not make the old tests pass by changing their expectations. No test already proves a new endpoint family merely because it shares the same invariant.

### Primary ray-solver release verification matrix

All rows below are planned checks. Phase 2 must publish results and the verified support envelope before Phase 3 can call the solver a reliable coverage geometry provider. Targets are numerical gates, not measured accuracy claims; tighten them where boundary conditioning requires it and never weaken retained old test bounds just to pass new cases.

| Category / case | Independent formulation or check | Gate and limitations |
|---|---|---|
| Vacuum, n=1 | Analytical chord, launch/arrival directions, zero bending/Q, exact tangent geometry, radial paths | New API Cartesian endpoint error <=0.1 m and angular residual <=1e-8 rad; old stricter tests unchanged; L agrees with chord to the declared integration tolerance |
| Uniform n=n0>1 | Straight Cartesian ray; L=D, OPL=n0*D, t=n0*D/c, excess=(n0-1)*D/c | Test in bounded `outside='unavailable'` profile; do not append a false vacuum boundary; nonzero index alone must not curve the path |
| Equal/unequal endpoint radii, reversed source/RX | Analytic vacuum cases and independent Cartesian ODE/shooting in a reciprocal scalar profile | Both altitude orderings and equal heights; same reversed curve/L/OPL with correctly reversed tangents; no forced UAV-above-station restriction |
| Near-tangent, internal radial minimum and surface grazing | Exact vacuum line-to-sphere minimum and independent numerical solutions, perturb endpoints on each side | Verify branch join, ground clearance and boundary brackets; exact tangency tagged marginal; no copied 0.5 m ground allowance or source-only `ground_clear` |
| Geometric horizon limit | Two-elevated-endpoint tangent formula and actual segment intersection | n=1 must approach k=1 geometry across both heights, including below-horizontal look angles; this is independent of EER fitting |
| Invariant conservation | Evaluate `b(s)=n(r)*r*cos(theta)` from independently integrated Cartesian samples/tangents | Proposed normalized drift <=1e-8 on resolved nonradial fixtures; use an absolute scale near radial b=0; reconstructing b from the same formula alone is insufficient evidence |
| Independent integration and shooting | Extend Cartesian Fermat `d(n*u)/ds=grad(n)` RK4/adaptive ODE harness with independent endpoint shooting | Compare endpoints, path, angles and Q on outward, reversed and minimum-radius families; retain existing 5 mm L / 1 mm Q fixture bounds; establish new case-specific tolerances before acceptance |
| Endpoint residuals and sample reconstruction | Root residual plus Cartesian endpoint and independently reconstructed terminal tangent | Both metrics saved; a higher-altitude intercept at wrong azimuth/range fails; avoid acos cancellation at tiny central angles, e.g. stable atan2 of cross/dot |
| Profile, quadrature, shooting and sampling convergence | Separate systematic refinement of each discretization, plus coupled refinement | Show stable length/angle/delay/clearance within stated error budget; distinguish input-grid interpolation error from integration error; no convergence inferred from one tolerance setting |
| Unsupported q/branches and possible multiplicity | Known nonmonotonic/duct profiles; ill-conditioned or multiple-root scenarios and explicit family checks | Return unsupported/undetermined, never a claimed unique ray or confirmed dead zone; monotonic q must not substitute for a BVP completeness argument |
| Solver-failure classification | Deliberate work/depth limits, missing lower layer, impossible bracket, failed residual, invalid inputs | Distinguish numerical failure, missing data, unsupported branch and modeled blockage; no EER result inserted |
| Path/time/attenuation integrals | Independent vertical piecewise-linear integrals and uniform gamma path; vacuum/constant-index delay limits | OPL=L+Q; excess relative to vacuum chord; gamma dB/km integrated once; missing or wrong-frequency gamma stays unavailable |
| Reproducibility / satellite preservation | Saved immutable inputs/settings/profile hashes, repeated runs and old API regression | Stable statuses and numerical results within declared precision; all 38 old tests retained; timestamps excluded from numeric equality |

For a ground-grazing solution, solver tolerance and zero-clearance uncertainty must be reported; optical contact with a smooth surface is not an operational clearance recommendation. Check both one-sided profile-knot behavior and smooth analytic profiles. For supported families, prove/verify branch completeness over the declared search domain; if not established, an unsuccessful search remains undetermined.

### Approximation benchmarks (separate from solver proof)

| Comparison | Controlled experiment | Required output/interpretation |
|---|---|---|
| Ray vs geometric LOS / k=1 | n=1, plus constant n and a range of antenna heights | Agreement in straight-path geometry/horizon; constant n changes delay, not bending |
| Ray vs conventional k=4/3 | Fixed reference profile and then varied gradients/heights | Signed/absolute horizon and feasible-interval differences; no requirement that an arbitrary profile match 4/3 |
| Ray vs derived k | Near-horizontal paths with documented approximately constant gradients, reference interval chosen before tracing | Unit-checked gradient derivation, stated validity and differences; nonapplicable cases unavailable rather than fitted |
| Altitude/gradient variation | Refractivity profiles over increasing UAV/station heights and range, with input-grid refinement | Difference versus elevation/height/gradient variability; distinguish approximation bias from numerical uncertainty |
| P.834 edition-specific checks | Preserve old approximation case and compare appropriate published cases within their domains | No extrapolation of Earth-space approximations as exact finite-UAV solutions; agreement is reference-model comparison, not field validation |

EER/geometric reference computation must be independent of the production ray root finder. Do not set k using a traced horizon and then count the resulting agreement as independent verification. Research comparisons also require matched physical endpoints and clear nulls for EER quantities that have no physical path/delay counterpart.

### Remaining engineering verification matrix

| Subject | Required independent checks | Initial acceptance target |
|---|---|---|
| Units | W/dBm round trips, MHz/GHz/Hz, Pa/hPa, K/Celsius, m/km; reject bool/NaN/Inf | 1 W = 30 dBm; exact scale identities within floating precision |
| ISA | Published sea-level and layer-boundary table values; geometric vs geopotential distinction | At H=0: T 288.15 K, p 101325 Pa, rho approximately 1.225 kg/m3; at H=11 km: T 216.65 K, p approximately 22632 Pa. Use table precision, e.g. 0.01 K / 1 Pa / 1e-4 kg/m3 |
| Viscosity/sound | Published standard-atmosphere table, separate from implementation formula | Sea-level approximately 1.789e-5 Pa s and 340.29 m/s; tolerances 0.1% / 0.05 m/s initially |
| Humidity/refractivity | Independently calculated dry/humid cases and saturation model references | Explicit coefficient/pressure convention; no arbitrary tolerance until reference precision recorded |
| FSPL | Retain exact-SI tests and +6.0206 dB per doubled distance/frequency | Reuse existing tolerances; distinguish rounded 32.4 from exact SI constant |
| Link budget | Independent spreadsheet/hand cases for both directions, separate feeder losses and fade reserve | Synthetic ledger existing test: P_rx -116 dBm, margin 4 dB; new EIRP and asymmetric fixtures must agree within 1e-9 dB for arithmetic |
| Reference geometry/horizon | Analytic sphere tangent and endpoint symmetry; small-height limit sqrt(2Rh1)+sqrt(2Rh2) | Independent reference checks; never used as a hidden primary ray cutoff |
| Altitudes | AGL at different local ground elevations; geoid sign; geometric/geopotential round trip | Reject unresolved AGL/geoid data; no datum mixing |
| Fresnel | Vacuum midpoint `sqrt(lambda*D/4)`, symmetry/endpoints; approximate ray-local diagnostic under sampling refinement | Relative error below 1e-10 for straight analytic formula; ray diagnostic explicitly approximate, unreliable cases flagged |
| Coverage | Verified-ray vacuum/constant-loss limit; power vs ray blockage, mask, no overhead link but feasible outer interval, narrow/disjoint intervals, unresolved cells, domain clipping and two-way intersection | Boundary bracket/refinement target attained or marked unresolved; no guarantee outside domain or below detection resolution |
| Model-domain gates | Frequencies below/above applicable ranges, negative altitude, inconsistent coordinates, e>=p, missing receiver modes | Structured field errors or unavailable status; no silent clamp/default |
| Gas backend | Official/reference independently generated values over state/frequency grid, including resonance behavior | Block release of backend until edition-specific reference tolerances and fixtures exist |
| Method isolation | Selecting k must not change a ray request/path; forced ray failure alongside successful EER reference; scenario revision mismatch | Distinct method IDs/hashes/statuses, no double refraction or automatic fallback, no incompatible quantity subtraction |
| Persistence/export | Scenario round trip and migration; stale input hash, missing values and source/units retained | Same normalized inputs and numerical outputs within specified serialization precision |
| GUI/frozen app | Calculations agree with headless fixtures; error/cancel/reload flows | No Qt import in core tests; complete clean-Windows smoke checklist |

Monotonicity tests apply only where supported branch continuity and loss monotonicity are established. Do not encode monotonic coverage as a universal physical law. Test near-zero separation, zenith/nadir, equal antenna heights, elevated station above UAV, exact threshold equality and very small/disjoint feasible regions. Antenna/terrain uncertainty is separate from solver tolerance. A release gate must fail if its only evidence is agreement with k=4/3.

Numerical verification tests equation implementation and convergence. Analytical model comparison tests agreement/differences between models under stated assumptions; it does not make the reference exact. Experimental validation tests predictions against observations. No measurement dataset was found. A future protocol should record contemporaneous vertically resolved atmosphere, its sampling/location/time uncertainty, calibrated TX power, gains/patterns, cable losses, frequency, receiver mode, bandwidth, positions/datum, antenna attitudes, RSSI calibration and repeated samples. Where available, measured angle/delay tests geometry more directly than RSSI, which also depends on amplitude/multipath physics. Compare residuals versus distance/elevation and report bias/scatter with held-out cases. Do not tune a loss margin or k to the same observations and call that independent validation.

The application and report must include limitations and sensitivity ranges. Show selected alternative k, humidity, sensitivity and feeder-loss scenarios rather than invented confidence percentages. Numerical tolerances, input uncertainties and model inadequacy must remain distinct.

## 19. Detailed Implementation Roadmap

The following phases are implementation instructions for after review, not completed work. Only Phase 0 has supporting completion evidence. The earlier analytical-MVP effort allowance is superseded: extending a robust near-grazing BVP is research work, so schedule Phase 2 by milestones and measured progress rather than promise a fixed total duration. Keep later UI scope small and reassess the submission scope after the solver gate. Gas spectra, terrain and ducting can extend the schedule substantially.

### Phase 0 — Repository audit (completed by this document)

- Objective: identify a trustworthy baseline and actual gaps.
- Relevant sources: all root files, both ZIPs, archive package/tests/docs/examples/build metadata.
- Files created: this document only; temporary inspection copy automatically removed.
- Tasks/evidence: inventory, source review, version/byte comparisons, manifests/CRC, wheel/source comparison and inspected unittest run.
- Dependencies: existing interpreter and standard library; no new installed dependencies.
- Scientific verification: 38 existing tests passed, with limits documented in Section 18.
- Acceptance: findings trace to named implementations; missing physics and uncertainty are explicit; no application refactor or build.
- Deliverable: reviewable plan and baseline decision.
- Risk: passing limited fixtures may be overinterpreted; preserve the evidence distinctions.

### Phase 1 — Atmosphere and scientific contracts (first implementation milestone)

- Objectives: preserve the tested library and define reproducible atmosphere/profile, geometry, radio and propagation-result contracts before extending the tracer.
- Relevant sources: archive `cubesat_link`, all tests/schemas/docs, package metadata; root input concepts and physical equations only.
- Create/modify: proposed `packages/cubesat-link/`, root UAV metadata, `models.py`, `units.py`, `validation.py`, atmosphere/profile modules, `propagation/contracts.py`, physical geometry/reference primitives, basic radio ledger helpers and headless fixtures/docs. No production solver-extension claim yet.
- Tasks: import supported package/tests without old API changes; implement ISA/viscosity/sound, dry/humid P.453 and bounded profile ingestion; normalize datums/radii; preserve profile gradients/boundaries/provenance; define generic endpoints, directed tangents, solver settings, failure taxonomy and conditional spreading assumptions. Specify independent TX/RX hardware and receiver modes. Establish k=1/geometric and declared-k reference functions independently of ray solving.
- Dependencies: review of this revised plan, edition/constants selection, supported Python choice, project ownership/license investigation; NumPy only where useful, no core GUI dependency.
- Early packaging risk check: after dependency compatibility review, create a tiny isolated Qt/Matplotlib/schema/reference-calculation smoke application and freeze one-directory using the candidate PyInstaller stack. Time-box to one working session; if blocked, document the compatibility issue and continue headless contracts/solver work while selecting a supported stack. No navigation/pages or full application work in this smoke test.
- Verification: all 38 original tests on imported source and intended library install; atmosphere tables and units/datum tests; profile coverage/q checks; hand radio ledger; independent reference geometry. The smoke confirms only deployment compatibility, not ray correctness.
- Completion criteria: a headless scenario produces a versioned thermodynamic/refractivity profile with hash, full geometry/radio contracts and explicit missing/assumed states; core imports no Qt; old APIs/fixtures unchanged. Compatible build stack is recorded or an explicit deployment blocker has an action plan; it cannot weaken the scientific gate.
- Expected outputs: contracts/API documentation, deterministic profile/scenario fixtures, preserved library baseline, numerical reference tests and a compact smoke record. No general coverage or new endpoint support is claimed.
- Major risks: datum/gradient errors, premature GUI scope, silent profile extrapolation and unverified gas expectations. Keep P.676 optional unless required by the submission rubric.

### Phase 2 — Ray-tracing solver verification and extension

- Objectives: make the reusable solver suitable for the declared ground/UAV source/receiver geometries and establish a primary scientific release gate.
- Relevant sources: archive `neutral.py`, `NeutralProfile`, existing `test_neutral.py` and independent Cartesian harness in `test_release_core.py`; root ODE equations/path ideas as unverified reference.
- Create/modify: planned additive `cubesat_link/ray_bvp.py`, `ray_types.py` and explicit package exports/version; preserve `neutral.py` behavior, sharing reviewed primitives only with regression evidence. Add new library tests; UAV `propagation/ray_tracing.py`, path/status adaptation and numerical verification fixtures/report. Legacy schema 1.0 remains unchanged.
- Tasks: derive supported branch brackets/domain and singular limits; handle outward/reversed/radial/equal-height and single-minimum nonducting paths; sample physical coordinates and tangents; compute endpoint/path/invariant/clearance diagnostics; return geometric/optical length and nondispersive delay; integrate only properly sourced attenuation; expose work/tolerance settings and distinct failure reasons. Build independent Cartesian endpoint-shooting comparison. Do not implement duct/multiple-ray physics simply to increase nominal scope.
- Dependencies: Phase 1 endpoint/profile/status contracts, actual sphere/surface boundary definition, independent numerical tool/harness; SciPy may be development-only. No desktop UI dependency.
- Verification gate: every primary-ray row in Section 18; old suite unchanged; analytic vacuum/constant-index and horizon limits; endpoint reciprocity; positive/negative launch directions; internal minimum/grazing; invariant conservation; independent ODE/shooting and profile/quadrature/tolerance/path-sampling refinement; forced-failure/unsupported cases.
- Completion criteria: declare and demonstrate the supported endpoint/profile envelope, branch handling and known completeness/uniqueness limits; Cartesian endpoint <=0.1 m and angle <=1e-8 rad for accepted new fixtures, with suitable convergence and old stricter limits retained. Publish unresolved cases as unsupported/undetermined. Coverage integration is blocked until this gate passes for the geometries it will advertise.
- Expected outputs: additive reusable BVP/path API, headless ray demonstrations/path data, verification report, machine-readable fixtures, timing baseline and explicit limitations. No general full-wave/amplitude validation claim.
- Major risks: singular grazing integrals, branch gaps/multiplicity, tiny-angle cancellation and false blockage. Resolve or narrow the declared support domain visibly; never conceal failure with EER or by returning a nearby ray.

### Phase 3 — Ray-tracing-based UAV communication coverage

- Objectives: turn verified ray connectivity into conditional hardware feasibility, coverage intervals and independent analytical comparisons.
- Relevant sources: passed Phase 2 path API; preserved budget/FSPL; Phase 1 profile, hardware and reference geometry.
- Create/modify: `link_budget.py`, `coverage.py`, `comparison.py`, services, propagation/reference/clearance modules, plot-ready data and numerical/integration tests.
- Tasks: apply ray-direction antenna masks/gains, distinguish path and radio statuses, integrate eligible absorption, retain endpoint-chord FSPL approximation and explicit focusing omission; handle independent directions/two-way intersection. Implement finite-domain adaptive sampling, branch-aware transitions and all resolved intervals; preserve unresolved cells/domain flags. Add altitude sensitivity, resolved disk/annulus areas, approximate ray-local Fresnel diagnostic and separately run k=1/k=4/3/justified derived-k references.
- Dependencies: passed solver gate for every advertised coverage family, complete traceable profiles/radio inputs and compatible reference assumptions; no full UI required.
- Verification: ray connectivity vs power/mask/clearance failures; missing-data and numerical/support cases; vacuum closed-form budget cross-check only as a reference; disjoint/narrow feasible intervals, unresolved gaps, overhead failure with outer feasibility, boundary convergence and bidirectional asymmetry. Test method isolation and no hidden fallback/double refraction.
- Completion criteria: every feasible cell has a verified path and conditional margin; maximum/farthest-demonstrated terminology is honest about unresolved/domain limits; EER never clips primary coverage; boundary precision attained or explicit uncertainty bracket returned; full layer provenance survives serialization.
- Expected outputs: headless ray-based coverage/comparison APIs, example intervals/coverage arrays, convergence study and reproducible report-ready figures. A first computational pilot of Section 23 may begin after the gate passes.
- Major risks: expensive sweeps, nonmonotonic/undetected intervals and overclaiming power fidelity. Use caching/continuation only with correctness guards, resolution reports and visible approximation labels.

### Phase 4 — Desktop UI and scientific visualization

- Objectives: six scientific pages exposing atmosphere, ray paths, budgets, coverage, comparisons and exports without hiding diagnostics.
- Relevant sources: Phase 1–3 immutable service results; original plotting concepts; early compatibility smoke evidence.
- Create/modify: desktop entry/window/controllers/workers/settings/resources/pages; backend-neutral atmosphere/path/budget/coverage/comparison figures; scenario persistence/schema migrations; CSV/JSON/plot export; GUI/integration tests and guide draft.
- Tasks: unit/datum-aware inputs, profile import and plots, physical ray cross-section/tangents, residual/branch/convergence panels, conditional ledger, coverage with undetermined hatching, independent reference overlays, two-scenario comparison, save/load, progress/cancel and stale-result handling. Default primary method is RayTracingPropagation. Do not build a cosmetic dashboard first.
- Dependencies: tested headless ray/coverage/comparison APIs, compatible PySide6/Matplotlib stack, stable versioned scenario/results contracts.
- Verification: GUI-to-headless fixture agreement; invalid profile/scenario errors; reference selection never changes a primary ray; both directions/units; exports preserve diagnostics/nulls; cancellation/no stale result acceptance; manual DPI/accessibility checks.
- Completion criteria: all six mandatory scientific workflows are usable in developer mode; solver failure is understandable and remains undetermined; reference results carry persistent labels; no widgets imported into core modules.
- Expected outputs: functional Qt application, scientific visualization/export examples, scenario comparison workflow and user guide draft.
- Major risks: frozen UI during ray sweeps, confusing physical/reference diagrams and hidden methodology. Profile worker performance and show expandable scientific details.

### Phase 5 — Packaging, verification and release

- Objectives: a traceable offline Windows distribution and credible engineering submission, with validation status honestly stated.
- Relevant sources: tested packages/Qt application, scientific fixtures/reference studies, early smoke evidence and archive release scaffolding after layout adaptation.
- Create/modify: `packaging/uav_cas.spec`, icon/version metadata, build/release scripts, pinned lock/notices/license, verification reports, methodology/reference/limitations/user-guide documents and final example scenarios. Optional CI can follow the same commands.
- Tasks: build one-directory in a clean compatible Windows environment; bundle Qt/schema/plot/scientific assets; run complete regression and clean-machine matrix; record hashes/toolchain/profile sources and worker behavior; independently review equations/units/convergence. Finalize computational study evidence without inventing field data. Consider one-file/installer only after the portable build passes.
- Dependencies: passed Phase 2 scientific gate, stable Phase 3/4 functionality, redistribution terms, selected Windows versions and reviewed dependency support. Actual measurements are optional unless the academic rubric requires experimental validation.
- Verification: Sections 16/18; source/installed/frozen ray paths, diagnostics and coverage fixtures agree; target Windows 10/11 machines without Python/network; no silent fallback; field comparisons only under the separate measured-data protocol.
- Completion criteria: opening the executable permits every mandatory workflow; reproducible examples and scientific limits are documented; unresolved release-critical failures are fixed or visibly excluded from supported scope; no unimplemented feature or unmeasured accuracy is advertised.
- Expected outputs: portable executable folder ZIP, release checksums/manifest, scientific verification dossier, user manual, reference/limitations documents, worked ray/EER comparisons and explicit experimental-validation status.
- Major risks: binary compatibility, Qt/process plugins, antivirus/signing, licensing and late scope growth. Keep a debuggable one-directory build/local logs and defer terrain, caustics, modem and satellite UI features.

## 20. Phase-by-Phase Deliverables

| Gate | Concrete handoff | Exit condition |
|---|---|---|
| P0 | This audit/plan | User reviews architecture, MVP assumptions and open decisions |
| P1 | Preserved library/tests; atmosphere/refractivity and endpoint/radio/solver contracts; independent reference primitives; time-boxed Qt/freezer smoke record | Headless reproducible profiles, old suite preserved, unit/datum checks, explicit build compatibility status |
| P2 | Additive BVP/path API, supported-domain statement and independent numerical verification dossier | Required endpoint families, residuals, invariant/convergence, clearance and failure taxonomy verified before coverage |
| P3 | Ray-based conditional coverage/comparison API, intervals and altitude sensitivity | Verified paths per feasible cell, unresolved/domain limits retained, no EER contamination and converged boundaries |
| P4 | Six scientific Qt pages, scenario/diagnostic exports and guide draft | GUI/headless agreement, physical path/reference diagrams distinct, responsive error/cancel handling |
| P5 | Portable Windows executable bundle, release manifest, scientific documentation and study examples | Clean offline Windows acceptance; all verification gates retained; honest validation status and licensing |

Make each gate reviewable and commit-sized where practical. Phase 1's compatibility smoke is part of the future roadmap; no implementation or packaging is authorized by this document-only revision. There is no release shortcut that replaces the Phase 2 scientific gate with EER agreement, an attractive path plot or a successful executable launch.

## 21. Risks, Limitations, and Mitigation Strategies

| Risk | Impact | Mitigation |
|---|---|---|
| Mixing MSL/AGL/ellipsoid/geopotential coordinates | Large atmosphere/visibility errors | Typed datum contracts and explicit required ground/geoid inputs |
| Treating a restricted ray failure as physical blockage | Incorrect coverage boundary | Separate numerical failure, unsupported branch, missing data and established modeled obstruction; no silent EER fallback |
| Generalizing outward-solver tests to new endpoint families | Plausible but wrong elevated-station coverage | Mandatory Phase 2 tests for reversed/equal-height/single-minimum paths before coverage |
| Grazing singularity, incomplete brackets or unknown multiplicity | Missing/false boundary or hidden numerical instability | Independent ODE/shooting, branch/domain analysis, residual/refinement gates and unresolved statuses |
| Inferring success from reconstructed invariant alone | Circular verification | Independently integrate/check Cartesian paths and analytic limits; invariant plus endpoint/convergence evidence |
| Reusing nonnegative station mask for all UAV paths | Underestimates clear paths from elevated stations | Evaluate user antenna constraints against local physical ray directions at both ends |
| Missing gas automatically becoming zero | Optimistic, untraceable budgets | Explicit assumed/unknown/computed states and conditional result labels |
| Replacing chord FSPL by ray length or assuming solved amplitude | Unsupported received-power accuracy | Retain labeled chord-FSPL approximation; focus/spreading needs separate future amplitude model |
| Profile resolution/gradient uncertainty or false vacuum top | Incorrect bending/horizon despite tight solver tolerance | Full height coverage, derivative/interpolation metadata, input-grid sensitivity and no forced UAV vacuum boundary |
| Ray horizon equated to general electromagnetic reach | Diffraction/multipath incorrectly ruled out | Direct-ray model label and separate absent-physics limitations on all no-path results |
| EER matching used as sole correctness criterion | Approximation bias becomes hidden target | Analytical limits plus independent numerical formulation and published scoped cases |
| EER quantities treated as physical ray delay/path | Invalid model-comparison differences | Capability-aware results, nulls for unsupported quantities and separate diagrams |
| Using synthetic examples as validation data | Unsupported scientific claims | Keep fixture labels and separate verification/measurement datasets |
| Root prototype and old snapshots shadowing package imports | Wrong implementation silently loaded | Package imports, source-layout discipline and installed-origin tests |
| Incomplete dependency/runtime compatibility | Packaging stalls | Early supported-stack check; do not extrapolate from Python 3.15 stdlib tests |
| Low-elevation clutter, multipath and terrain | Real coverage may be much smaller or irregular | State smooth-surface scope; reserve margin; validate later with measurements/DEM |
| Uncertain antenna patterns or sensitivity mode | Incorrect power budget | Require source/mode and distinguish synthetic defaults |
| Margin interpreted as uptime/throughput | Invalid engineering conclusions | Deterministic classification only; separate future modem/statistical model |
| Double counting losses/refraction | Systematically wrong results | Named ledger, explicit exclusions, one visibility/refraction mode |
| Mutable caches/stale GUI results | Results no longer match inputs | Immutable models, input hash/revision and stale/cancel handling |
| Expensive ray sweeps and small disconnected feasible regions | Slow app or missed coverage intervals | Measured timing, bounded work/cancel, cached immutable profiles, adaptive scans and resolution/unknown reports |
| License ambiguity in archive or coefficient datasets | Distribution blocked | Resolve project ownership/license and third-party notices before release |
| Scope expansion | Student submission delayed | Keep terrain, advanced ray physics and satellite UI outside MVP |

No verified experimental accuracy bound is available. Numerical tolerances describe implementation precision only. Offline reference atmosphere cannot represent real-time weather, local humidity structure, ducting or interference. A research-oriented first release is feasible only with a declared, independently verified nonducting endpoint/profile envelope and conditional power model. If those gates cannot be met on the submission schedule, revise the advertised scope explicitly; do not present a reference calculator as the completed ray-based framework.

## 22. Definition of Done and Acceptance Criteria

First-release acceptance requires all mandatory scope items and all of the following:

1. A clean Windows user launches the distributed executable without Python, terminal commands or network access; the documented Windows matrix passes.
2. Atmosphere outputs include T in K/Celsius, pressure Pa, density, viscosity, sound speed, humidity/vapour pressure where applicable, N and n, with model/reference metadata and altitude conversions.
3. A primary `RayTracingPropagation` calculation uses a physically defined profile and actual spherical Earth, supports the declared ground/UAV altitude orderings and families, and reports physical path samples, endpoint directions/bending, chord/ray/optical lengths, delay, clearance and solver diagnostics. Any excluded endpoint/profile case is explicitly unsupported.
4. Link outputs include TX dBm, EIRP, endpoint-chord FSPL as a labeled spreading approximation, each additional loss/status, total link loss, received power, sensitivity/source, raw/design margin and conditional classification. Absorption is integrated along the ray only with valid data/model; no full-wave power claim.
5. Uplink and downlink can differ; requested bidirectional coverage uses the intersection, and ray reuse respects reciprocity/frequency/profile assumptions.
6. Coverage is derived from verified rays and conditional budgets. It reports all resolved feasible intervals, unresolved extent, maximum/farthest-demonstrated chord/ray/ground ranges, limiting factors and search precision. Numerical failure never becomes confirmed physical blockage.
7. Top-down coverage and altitude sensitivity show undetermined regions, units and assumptions; no terrain awareness or guaranteed electromagnetic reach is claimed.
8. EER/geometric references run independently with method identities, applicability and compatible quantity comparisons. There is no double refraction, EER cutoff on ray coverage or hidden analytical fallback.
9. AGL/MSL and ellipsoid/geopotential conventions are documented and tested. Missing local ground/geoid/profile coverage cannot be silently guessed.
10. Saved scenarios and CSV/JSON/plot exports retain profile samples/hash, physical inputs, method/model versions, solver settings/residuals, assumptions, statuses and search limits.
11. All 38 original tests are retained unchanged and pass after implementation. The new primary ray matrix passes with independent analytical/numerical evidence before coverage release; EER agreement alone cannot satisfy it. GUI and frozen fixtures agree with headless results.
12. Every selectable automatic gas backend has independent reference checks/domain gates; otherwise it is unavailable or a declared assumption. No silent sub-GHz clamp or ITU conformance claim.
13. The core remains GUI-independent; satellite APIs/schema/fixtures and existing verified functionality remain compatible. New branches use an additive reusable API.
14. Invalid input, cancellation, missing/unsupported physics and numerical failure have understandable, distinct outcomes without crashes or fabricated results. Approximate refracted-path Fresnel diagnostics are labeled and sampling-converged.
15. Six scientific UI pages, scenario comparison, offline storage/export and clean Windows launch work; the early smoke does not replace full packaging acceptance.
16. Methodology, model domains, convergence evidence, uncertainty/limitations, license notices, reproducible builds and at least one controlled ray/EER comparison are documented.
17. Numerical verification, analytical approximation benchmarking and experimental validation are distinguished. Environmental input uncertainty and incomplete amplitude physics remain explicit; no measurement-based accuracy claim without data.

The present revision is done when only this plan has been updated and reviewed for consistency with ray tracing as the primary methodology. Application acceptance above belongs to future development; no new solver gate is claimed passed now.

## 23. Future Extension Opportunities and Scientific Research Value

### Proposed research question

**Under what atmospheric conditions does the conventional effective-Earth-radius approximation diverge significantly from refractivity-aware ray-tracing predictions for UAV communication geometry and coverage?**

This is a proposed computational/experimental study direction, not an established novel contribution or a claim that ray tracing is more accurate in the field. First establish numerical reliability for the declared model, then study approximation differences, and finally assess external agreement if atmospheric and RF observations become available.

### Realistic computational study

1. Predefine questions, model domains and practical significance thresholds in a study manifest. For example, use a declared engineering range-difference threshold alongside angle/delay thresholds tied to the chosen antenna/timing application; select these before seeing results. Do not invent a universal significance percentage or infer statistical significance from a deterministic difference.
2. Begin with vacuum and uniform-index control cases, then dry ISA/P.453, the existing P.834 exponential, documented constant-gradient layers within valid height bounds, and positive bounded piecewise profiles representing gentle gradient variations. Profiles are explicitly synthetic/reference unless sourced measurements exist. Reject nonmonotonic-q or unresolved-multiplicity cases from the first-release solved set while recording their exclusion.
3. Use a small pilot grid before scaling: station antenna heights such as 2, 10, 50 and 200 m over a specified uniform ground; UAV MSL heights such as 100, 500, 1,000, 3,000, 6,000 and 11,000 m where above ground and profile-covered; include a separate elevated-site case with the UAV lower than the station antenna. Do not extend a linear gradient into negative N or outside its declared domain merely to fill this grid.
4. Isolate geometry first: common surface/radius, no artificial nonnegative elevation masks, matched endpoint conditions and no RF range limit. Compare ray results against geometric and k=4/3 references; include derived-k only for the compatible near-horizontal/constant-gradient subset, with gradient interval chosen in advance. Never fit k to reproduce each traced horizon and call that independent benchmarking.
5. Add a second, explicitly conditional radio experiment with fixed asymmetric hardware and a common endpoint-chord FSPL/no-focusing baseline. Use a small band set (e.g. 915 MHz and 2.4 GHz), recording that nondispersive geometry can be shared only within profile scope. Keep gas explicitly neglected or supplied consistently in the first controlled comparison; an automatic P.676 extension is restricted to its verified domain and cannot be forced onto 915 MHz. Distinguish power-limited coverage changes from changes in path connectivity or mask angles.
6. Refine profile spacing, ray tolerances/path sampling and range grid separately around sensitive cases. Save unresolved cases and work limits. Quantify numerical error bands before interpreting a model difference as physically meaningful. Freeze code/model versions, profile hashes, configuration and units with each dataset.
7. Produce reproducible tables, figures and a short methods/limitations report. Do not select only examples where the ray model appears better. Report agreement cases, divergence cases, unsupported regimes and assumptions that dominate the comparison.

### Measurable comparison outputs

| Output | Measurement/definition | Comparison caution |
|---|---|---|
| Estimated direct-ray horizon | Farthest verified non-ground-intersecting supported path at fixed heights, separate from antenna/power limits | Compare to EER approximate ground distance with matching height/range conventions; unresolved bounds remain intervals |
| Feasible communication intervals | Range intervals meeting ray connectivity, selected constraints and conditional budget in each direction | Count/extent of intervals and unresolved gaps; not just largest radius |
| Launch/arrival angles and bending | Signed physical tangents, total bending and angle relative to geometric chord | EER transformed angles need a declared interpretation; otherwise show only compatible reference geometry, not invented physical bending |
| Geometric/optical path differences | `L_ray-D_chord`, `Q=integral(n-1)ds`, `OPL-D_chord` | These are physical ray/vacuum comparisons; a bare EER horizon has no OPL prediction |
| Delay | `OPL/c` and excess relative to `D_chord/c` under nondispersive assumptions | Compare to independent integration/controls or measured delay; EER delay stays unavailable without an explicit additional model |
| Profile sensitivity | Changes across temperature/humidity/gradient models, profile resolution and source uncertainty | A nominal profile is not actual weather; do not assign confidence intervals without uncertainty data |
| Numerical robustness/cost | Endpoint/invariant errors, refinement differences, status counts, work/time | Solver convergence and support limitations are part of findings, not details to omit |

### Later experimental study

If resources permit, combine contemporaneous measured vertical profiles with synchronized ground/UAV coordinates/attitude and calibrated radio measurements over repeatable paths/altitudes. A distant radiosonde or a surface sensor alone does not establish the whole propagation medium; record representativeness uncertainty. Angle/delay observations would help test ray geometry directly; RSSI also depends on antenna orientation, fading, scattering, interference and spreading/absorption assumptions.

Separate calibration from held-out validation, keep receiver mode and reference datums fixed, report measurement uncertainty and residuals for both ray and analytical predictions, and do not count fitted parameters as independent confirmation. Without these data, the report is a computational approximation study and numerical verification portfolio. More complex propagation geometry may still predict actual RSSI less accurately if atmospheric inputs or amplitude physics are inadequate.

### Later extensions

Add sourced P.835 humidity/climatology profiles, verified P.676 gas spectra, deterministic rain/cloud integration and statistical models with suitable climate inputs. Add offline DEMs only with resolution, vertical datum, interpolation and licensing recorded. Terrain-aware coverage needs Fresnel/diffraction and clutter assumptions, not simply colored circles on a map.

For antennas, support pattern coordinate frames, gain normalization, polarization/axial ratio and attitude-dependent bidirectional budgets. For propagation, investigate ray-tube amplitude/Jacobians and caustics, atmospheric trapping/multiple eigenrays, horizontally varying refractivity, reflection/diffraction and full refractive Fresnel geometry with independent comparisons. Basic descending/reversed/single-minimum paths and path-coordinate export are required for the first functional ray release, not deferred here.

For CubeSat reuse, retain finite electron integration, first-order plasma, ideal polarization, contact windows and ECEF geometry. Later add verified orbit-frame conversion, Doppler, actual orbit providers, IRI/IGRF with ray sampling/provenance and refracted/budget-based windows. These extensions must retain missing-data semantics and avoid applying the UAV altitude ceiling to satellite calculations.

## 24. Open Questions and Decisions Requiring Approval

These are review decisions for the next phase, not blockers to completing this audit. Suggested defaults make the plan actionable; no approval is inferred from silence.

| Decision | Recommended default | Why it matters |
|---|---|---|
| Submission deadline, rubric and expected demonstration | Verified ray/profile milestone before conditional coverage and UI breadth | Solver extension has research risk; scope/schedule must reflect the mandatory gate |
| First functional endpoint/profile envelope | Monotonic-q nonducting sphere; either endpoint higher, equal-height and simple radial-minimum branches verified; no ducts/multiple rays | Current outward solver does not yet meet this requirement; publish and test any narrowing |
| Scientific power scope | Endpoint-chord FSPL plus explicit no-focusing assumption and eligible ray-integrated/supplied losses | Ray geometry alone cannot deliver validated refractive power transfer |
| Reference/fallback behavior | EER/geometric results only as explicitly selected independent references; no automatic fallback | Ray failure must remain visible and cannot be reclassified as a successful ray |
| Hardware and operating modes | User-provided datasheet thresholds, exact radio/packet-rate settings; clearly synthetic examples meanwhile | Sensitivity is mode-specific; current -105 dBm default is not universally valid |
| Required bands | 868/915 MHz and 2.4 GHz presets, custom within model limits | Sub-GHz P.676-13 Annex 1 cannot be silently clamped |
| Gas scope | Explicit assumption/supplied-data mode in baseline; verified automatic backend as next increment | If automatic atmospheric loss is academically mandatory, schedule it as a release gate |
| Ground and UAV geometry | Actual spherical smooth ground with explicit MSL/AGL and primary n(h) ray solution; k=1/k=4/3 only in separate reference runs | Avoids double refraction and unsupported terrain/geoid assumptions |
| Below-sea-level sites and lower-than-station UAVs | Reject negative MSL in initial UI; verify elevated-station/lower-UAV ray geometry via new API | Existing satellite classes and outward tracer retain their restrictions |
| Antenna/Fresnel policy | Constant gains/known orientation evaluated at ray directions; approximate ray-local Fresnel diagnostic, enforcement optional | Rigorous refractive spreading/Fresnel physics is outside initial amplitude scope |
| Atmospheric profiles for research | Dry/reference and documented bounded imported tables, with no real-time claim | Significant gradients need more than a surface weather input |
| Research significance and validation | Define engineering thresholds and pilot grid before study; use held-out observations only if available | Deterministic model divergence is not automatically real-world error or novelty |
| Coverage direction | Separate uplink/downlink and selectable two-way intersection | Command and telemetry may have different limiting links |
| Windows target and packaging | Windows 10/11 x64, PyInstaller one-directory portable ZIP first | Confirm minimum OS versions and compatible Qt/freezer/Python stack |
| Project/library redistribution rights | Confirm authorship/license; preserve third-party notices | Archives contain no explicit LICENSE declaration |
| UI language and reports | English UI/methodology, CSV/JSON/PNG first | Matches current engineering deliverable; PDF/localization can follow |
| Validation data | No experimental-validation claim until measurements exist | Current examples and tests are synthetic/analytical |

After review, the first implementation milestone is Phase 1: import the preserved package/tests, establish headless endpoint/radio/profile/status contracts, and generate reproducible bounded n(h) inputs with verified units/datums and reference calculations. Include only the time-boxed compatibility smoke from the future roadmap. Then pass Phase 2's dedicated BVP/path verification gate before claiming ray-based coverage. Preserve tested outward algorithms; extend the missing families through an additive API. Stop after updating this plan for the present assignment; wait for review before implementing any phase.
