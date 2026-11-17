# UAV-CAS Decision Records

These records follow the repository-root `AGENTS.md` requirements. Records marked **Reconstructed** summarize decisions already evidenced by `plan.md`, progress reports, source provenance, tests, and outputs. They are not contemporaneous ADRs. The alternatives below are limited to alternatives explicitly discussed in those sources.

## ADR-001 — Preserve `cubesat_link` 0.2.0 as the scientific baseline

- **Date:** 2026-11-17 (reconstruction date; original decision date not independently recorded)
- **Status:** Accepted — **Reconstructed**
- **Context:** The audited root Streamlit prototype referenced missing physics modules and contained unverified propagation behavior. The archived `cubesat_link` package supplied explicit units, provenance, missing-data semantics, geometry, link-budget arithmetic, a restricted spherical solver, and 38 tests.
- **Decision and justification:** Preserve and import `cubesat_link` 0.2.0 as a separate package and backward-compatible baseline. Build UAV-CAS additions around stable, additive APIs instead of treating the incomplete root prototype as the scientific core.
- **Alternatives considered:** Rebuild around the root prototype; rewrite the preserved package in place. The roadmap rejected the former because required modules were absent and the latter because it would risk established APIs and regression behavior.
- **Trade-offs and limitations:** The baseline does not itself provide the required UAV atmosphere, general endpoint ray BVP, coverage engine, desktop UI, or release packaging. It also carries its own restricted solver scope.
- **Consequences:** Original CubeSat tests and APIs remain regression gates. UAV-specific functionality belongs in additive modules, and preserved source must not be represented as newly validated physics.

## ADR-002 — Keep physical ray tracing, geometric LOS, and EER separate

- **Date:** 2026-11-17 (reconstruction date; original decision date not independently recorded)
- **Status:** Accepted — **Reconstructed**
- **Context:** The roadmap requires refractivity-aware spherical ray tracing as the primary propagation-geometry method. Geometric LOS and effective-Earth-radius calculations are useful references, but they do not produce a physical refracted path and cannot diagnose a failed ray solution.
- **Decision and justification:** Use a physical-Earth spherical ray BVP as the primary method. Keep geometric LOS and EER (`k=1`, `k=4/3`, or a justified gradient-derived `k`) as separately labelled analytical comparisons. Never apply EER curvature in the ray equations or use EER as an implicit fallback for unsupported, blocked, missing-data, or failed ray results.
- **Alternatives considered:** Use EER as the primary method; silently replace a failed ray with EER; add an EER curvature correction to a refracted ray. These alternatives were explicitly rejected in the roadmap and progress reports because they conflate different physical approximations and obscure solver failure.
- **Trade-offs and limitations:** Coverage cannot be claimed until the applicable ray branches are verified. Explicit failures and unsupported states may leave results unavailable instead of producing an approximate range.
- **Consequences:** Requests/results require explicit method and status semantics. Comparison services may run independently, but may not overwrite ray status or fabricate ray path, delay, or optical quantities.

## ADR-003 — Use bounded, traceable atmosphere and refractivity profiles

- **Date:** 2026-11-17 (reconstruction date; original decision date not independently recorded)
- **Status:** Accepted — **Reconstructed**
- **Context:** Ray calculations require a physically defined `n(h)` with known units and domain. The Phase 1 demonstration needed reproducible atmosphere data without implying access to measured weather or a full humidity profile.
- **Decision and justification:** Implement an ISA-1976-compatible dry lower atmosphere and ITU-R P.453-14 refractivity, with geometric/geopotential altitude conversion. Represent `n(h)` as a bounded, immutable, piecewise-linear profile with provenance, deterministic hashing, and no extrapolation. Treat a local relative-humidity input as local only; do not manufacture a vertical humidity profile.
- **Alternatives considered:** Extrapolate beyond supplied profile bounds; infer a vertical humidity profile from one local RH value; treat synthetic gas/example data as a verified atmospheric model. The roadmap and Phase 1 report reject these behaviors.
- **Trade-offs and limitations:** The dry demonstration is not contemporaneous weather, and profile interpolation/discretization contributes numerical/model uncertainty. Missing vertical data can produce an explicit unavailable result.
- **Consequences:** Scientific outputs must state altitude coordinates, units, source, validity bounds, and assumptions. Measured/imported profiles require independent height-resolved data and provenance.

## ADR-004 — Limit Phase 2A to a verified nonducting direct-ray subset

- **Date:** 2026-11-17 (reconstruction date; original decision date not independently recorded)
- **Status:** Accepted — **Reconstructed**
- **Context:** A general spherical refractive BVP can contain turning layers, ducts, multiple eigenrays, caustics, and singular numerical behavior. Phase 2A needed a verifiable foundation before any coverage search.
- **Decision and justification:** Support short-arc radial, radial-monotonic, and one-lower-radial-minimum direct families only, on a physical sphere with a bounded scalar `n(h)` and strictly increasing `q(r)=n(r)r`. Use Bouguer-invariant quadrature, regularize the tangent singularity with `r=r_min+u^2`, split at profile knots, and require explicit endpoint, invariant, clearance, and convergence diagnostics.
- **Alternatives considered:** Adopt the legacy shooting wrapper as production; claim general branch completeness; substitute EER when the BVP fails. The roadmap and Phase 2A report explicitly reject these alternatives.
- **Trade-offs and limitations:** Ducting, nonmonotonic `q`, multipath, long/antipodal paths, terrain, diffraction, reflection, caustics, and coverage search remain unsupported. Numerical verification does not establish field validation.
- **Consequences:** Unsupported model/branch, missing data, modeled blockage, numerical failure, and invalid input remain distinct outcomes. Phase 3 coverage must consume only verified ray results within this declared domain.

## ADR-005 — Track compact provenance and reproducibility artifacts in the baseline

- **Date:** 2026-11-17
- **Status:** Accepted
- **Context:** Initial Git publication required separating durable scientific evidence from local environments, caches, build products, secrets, and temporary simulations. The two original CubeSat archives, preserved wheel, and Phase 1/2A generated outputs are provenance or reproducibility evidence; none exceeds 1 MiB. The archives do not contain an explicit license declaration.
- **Decision and justification:** Track the original archives, preserved package wheel, source, tests, documentation, and current Phase 1/2A CSV/JSON/PNG outputs. Ignore local runtimes, caches, root build/distribution products, credentials, and explicitly named temporary/intermediate simulation directories. Retaining the compact artifacts makes the initial scientific state reproducible without deleting or silently externalizing source evidence.
- **Alternatives considered:** Exclude all archives and generated outputs to minimize repository size; track every local environment and intermediate product. The former would weaken baseline provenance despite the small file sizes, while the latter would add machine-specific and potentially sensitive material.
- **Trade-offs and known limitations:** Binary archives, wheels, and plots are not meaningfully diffable and increase repository size, although the current files are small. Tracking them does not resolve the existing redistribution-rights ambiguity; no license terms are inferred.
- **Consequences for future development:** Large or replaceable generated artifacts should be reviewed before tracking and may require an external artifact store or Git LFS. Provenance-critical scientific data must not be removed solely for size reduction, and licensing/ownership must be resolved before a formal public release claim.

## ADR-006 — Verify the spherical BVP with an additive Cartesian Fermat reference

- **Date:** 2026-11-17
- **Status:** Accepted
- **Context:** Phase 2B required a reference that did not merely repeat the production Bouguer-invariant integration and root solve. The existing Phase 2A test integrated one production launch direction but did not provide a reusable independent BVP shoot or reproducible benchmark output.
- **Decision and technical justification:** Add a two-dimensional Cartesian fixed-step RK4 integrator for `d(nu)/ds=grad(n)` with its own launch-elevation scan and bisection. Keep it in a verification-only module, pass it the same immutable bounded profile, and prohibit its use as a runtime fallback. This changes the numerical formulation while retaining common physical inputs for a controlled comparison.
- **Alternatives considered:** Reuse the production launch angle only; implement another Bouguer quadrature; replace a failed production result with the Cartesian reference. The first provides weaker BVP independence, the second shares the production formulation, and the third would hide solver status and violate the approved method separation.
- **Trade-offs and known limitations:** The reference shares the profile interpolation, spherical symmetry, and scalar-index assumptions. Fixed-step integration and receiver-angle event interpolation are less efficient and limit the last digits; it is suitable for deterministic verification cases, not production coverage search.
- **Consequences for future development:** Phase 3 continues to use the production spherical BVP. The Cartesian method remains a regression oracle for representative supported cases and must report unresolved outcomes rather than supplying fallback paths.

## ADR-007 — Separate numerical convergence from near-horizon physical uncertainty

- **Date:** 2026-11-17
- **Status:** Accepted
- **Context:** The 130 km demonstration clears the ideal surface by only about 6.87 m. Solver tolerances can be made much smaller than this value, but real refractivity, endpoint heights, datum, and terrain are not known to comparable precision.
- **Decision and technical justification:** Retain the established 0.05 m numerical grazing band; characterize profile, quadrature, shooting, and path-sampling effects separately; and label dry-profile gradient scaling as controlled sensitivity rather than a probabilistic weather uncertainty. Recommend only a conditional Phase 3 start within the verified direct-ray family.
- **Alternatives considered:** Treat solver precision as prediction accuracy; assign an invented atmospheric probability distribution; tune the ray to conventional `k=4/3`; or declare every positive modeled clearance operationally visible. These would conflate numerical, model, and input uncertainty or improperly calibrate the primary solver.
- **Trade-offs and known limitations:** The studies establish deterministic sensitivity but no confidence interval or empirical accuracy. A smooth-sphere classification may differ from terrain-aware or measured-atmosphere behavior even when numerical residuals are small.
- **Consequences for future development:** Coverage results must preserve clear/grazing/blocked/unresolved distinctions, expose input/model assumptions, and avoid link-availability claims. Terrain-aware or operational conclusions require later models and measured validation.

