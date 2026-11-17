# UAV Communication Analysis Suite (UAV-CAS) — Phase 2B Scientific Verification

## 1. Executive Summary

Phase 2B establishes a reproducible numerical-verification baseline for the bounded, nonducting spherical atmospheric ray solver implemented in Phase 2A. The work adds an independently formulated Cartesian Fermat RK4 shooting reference, systematic profile/quadrature/shooting/path-sampling campaigns, a near-horizon sensitivity investigation, independent Effective Earth Radius (EER) comparisons, a benchmark matrix that retains blocked cases, scientific figures, and automated tests.

The previously reported 130 km case was regenerated without hard-coded outputs. With the same request-derived controls used in Phase 2A, it remains a solved single-minimum ray with 6.868748665 m minimum smooth-surface clearance, 0.002408767 m Cartesian endpoint error, 130,046.286091 m optical path, and 114.973255 ns excess delay relative to the vacuum endpoint chord. Tighter controls change the numerical solution by millimetres or less, but atmospheric and endpoint perturbations are much more consequential near the visibility boundary.

This phase verifies code behavior and numerical consistency for the declared solver family. It is not experimental validation, does not establish field accuracy, and does not show that a geometrically clear ray provides a usable communication link.

## 2. Verification Objectives

The objectives were to:

- independently regenerate the Phase 2A demonstration;
- separate profile discretization, quadrature, shooting, and path-sampling effects;
- verify constant-index analytical limits, spherical geometry, the Bouguer invariant, and reciprocity;
- compare against a formulation that does not use the production invariant quadratures or root solver;
- characterize ground-grazing sensitivity and explicit solver failure modes;
- benchmark, without calibrating to, geometric `k=1`, conventional `k=4/3`, and gradient-derived EER approximations; and
- produce deterministic machine-readable evidence before Phase 3 coverage work.

## 3. Governing Equations and Assumptions

For the production solver, the phase refractive index is scalar and spherically symmetric, `n=n(r)`. The Bouguer invariant is

```text
b = n(r) r cos(theta)
```

where `theta` is ray elevation relative to the local horizontal. On a radial leg,

```text
dphi/dr = b / [r sqrt((n r)^2 - b^2)]
ds/dr   = n r / sqrt((n r)^2 - b^2)
dQ/dr   = (n - 1) ds/dr
OPL     = L + Q
```

The single-minimum tangent singularity is regularized with `r=r_min+u^2`. Integrals are split at every piecewise-linear profile knot. Coordinates use a 6,371,000 m spherical MSL datum; endpoint heights are radial metres above that sphere, and surface separation is sphere arc length.

The independent reference integrates the Cartesian Fermat ray equation

```text
d(n u)/ds = grad(n),  |u| = 1
du/ds = [grad(n) - u (u dot grad(n))] / n
```

using fixed-step RK4 and an independent launch-elevation shoot to the receiver central angle. It shares the same bounded piecewise-linear `n(h)` input and spherical/horizontal-homogeneity assumptions, but it does not import or call the production BVP integration routines. Thus it is numerically independent but not an independent atmospheric model or experimental reference.

The verified family remains limited to short-arc radial, radial-monotonic, and one-lower-minimum direct rays with strictly increasing `q(r)=n(r)r`. The ground is a smooth absorbing sphere. Ducting, multiple eigenrays, caustics, terrain, reflection, diffraction, scattering, and amplitude transport are excluded.

## 4. Numerical Methods

The production method uses bounded bisection for either invariant `b` or minimum radius, adaptive vector Simpson quadrature for angle, geometric length, and refractivity excess, and independent diagnostic path reconstruction. The reference method uses fixed-step Cartesian RK4 plus launch-elevation bracketing and bisection.

Convergence declarations use output-relevant comparisons rather than only internal tolerances. For the fine profile-grid campaign, shooting was tightened to `1e-12 rad` and 0.005 m endpoint tolerance so root error was below the observed grid-refinement changes. The 0.05 m ground-grazing band is retained from Phase 2A as a conservative numerical classification boundary, not a physical roughness or terrain uncertainty estimate.

Quadrature evaluation counts are cumulative across root trials and path reconstruction. The stored quadrature error estimates are adaptive-integration diagnostics, not certified total physical-error bounds.

## 5. Verification Cases

The benchmark matrix contains eight deterministic configurations:

| Case | Configuration | Outcome |
|---|---|---|
| Constant unequal height | 10 m to 1,000 m, 50 km, `n=1.0003` | Solved, radial-monotonic |
| Constant equal height | 1,000 m to 1,000 m, 50 km, `n=1` | Solved, single-minimum |
| Dry radial | 10 m to 1,000 m, zero separation | Solved, radial |
| Dry short | 10 m to 120 m, 10 km | Solved |
| Dry intermediate | 10 m to 1,000 m, 75 km | Solved |
| Dry near horizon | 10 m to 1,000 m, 130 km | Solved |
| Dry grazing | 10 m to 1,000 m, 135.85 km | Blocked, `ground_grazing` |
| Dry blocked | 10 m to 1,000 m, 140 km | Blocked, `ground_intersection` |

The complete metrics, settings, reason codes, and failed/blocked rows are in [phase2b_benchmark_matrix.csv](../outputs/phase2b/phase2b_benchmark_matrix.csv).

## 6. Convergence Studies

### Atmospheric profile resolution

The 130 km case was solved on 200, 100, 50, 25, and 12.5 m dry ISA/P.453 grids with tighter root/quadrature controls. Relative to the 12.5 m grid:

| Grid | Clearance difference | OPL difference |
|---:|---:|---:|
| 200 m | -0.027659 m | +0.000742 m |
| 100 m | -0.009512 m | +0.000194 m |
| 50 m | -0.002915 m | +0.0000470 m |
| 25 m | -0.000647 m | +0.00000996 m |

The sequence is consistent with convergence for the investigated profile interpolation. A 25 m grid is adequate for millimetre-level clearance stability in this synthetic reference case, but this does not quantify atmospheric-model uncertainty.

### Integration tolerances

Angle, path-length, and refractivity quadrature tolerances were varied independently over three orders of magnitude. Tightening the angular integral tolerance from `2e-9` to `2e-12 rad` changed OPL by approximately `1.09e-8 m` and increased cumulative evaluations from 8,045 to 8,405. Within the tested ranges, independent path-length and refractivity tolerance changes produced no resolved output change because the angular component controlled the shared adaptive vector-Simpson subdivision. This is an observed implementation property, not evidence that those quantities can be assigned arbitrary tolerances.

### Boundary-value shooting

With `1e-11 rad` angular tolerance, 8, 16, and 24 maximum iterations returned explicit `numerical_failure/endpoint_residual` outcomes. Forty iterations solved the case in 29 iterations with approximately `5.66e-6 m` Cartesian endpoint error; increasing the limit to 80 did not change the result. The solver therefore does not emit a nearby ray when root work is insufficient.

### Ray-path sampling

Changing path samples from 21 to 801 did not change integrated length, OPL, minimum clearance, or endpoint residual. The reconstructed invariant diagnostic ranged from approximately `9.35e-10` to `3.74e-9` and was not monotonic with sample count because centred chord tangents and their alignment with piecewise-linear profile knots are post-processing approximations. This negative result corrects any interpretation that the sampled invariant error must decrease monotonically. The invariant remains conserved to a few parts in `1e9` in all investigated samples.

Full tables and figures are [phase2b_profile_convergence.csv](../outputs/phase2b/phase2b_profile_convergence.csv), [phase2b_integration_convergence.csv](../outputs/phase2b/phase2b_integration_convergence.csv), [phase2b_shooting_convergence.csv](../outputs/phase2b/phase2b_shooting_convergence.csv), [phase2b_path_sampling_convergence.csv](../outputs/phase2b/phase2b_path_sampling_convergence.csv), and [phase2b_profile_convergence.png](../outputs/phase2b/phase2b_profile_convergence.png).

## 7. Independent Reference Comparisons

### Constant-index analytical reference

For `n=1.0003`, 10 m to 1,000 m, and 50 km surface arc, the analytical chord is 50,013.634081431 m. With tight verification controls, the numerical geometric-length and `n*chord` OPL errors were both approximately `1.79e-7 m`; launch elevation differed from the analytical straight-line geometry by about `3.8e-12 deg`. Analytical and numerical travel times agreed to approximately `6e-16 s`.

### Cartesian Fermat RK4 reference

At 50 and 100 km with 20 m and 10 m steps, all four independent shoots converged. Across these cases, the maximum absolute production/reference differences were:

- geometric length: `2.29e-4 m`;
- refractivity excess: `1.12e-5 m`;
- launch elevation: `5.09e-6 deg`;
- Cartesian-reference endpoint radial error: below `0.009 m`.

Step refinement was not strictly monotonic at the last digits because the reference combines a fixed-step event interpolation with a finite shooting stop criterion. The agreement supports the production formulation for these cases but does not make the two methods experimentally independent.

### Reversibility

For the 50 km dry-profile case, forward and reversed solutions had zero reported differences in geometric length, OPL, and minimum clearance at stored precision. Corresponding launch/arrival directions agreed under the expected tangent reversal to floating-point precision.

See [phase2b_independent_reference.csv](../outputs/phase2b/phase2b_independent_reference.csv) and [phase2b_ray_reference_comparison.png](../outputs/phase2b/phase2b_ray_reference_comparison.png).

## 8. Near-Horizon Sensitivity

The 130 km baseline is numerically well separated from the 0.05 m grazing band, but it is physically sensitive:

- profile refinement from 200 m to 12.5 m changed clearance by 0.027659 m; 25 m to 12.5 m changed it by 0.000647 m;
- scaling the dry-profile vertical refractivity departure from the surface by 0.8 to 1.2 changed clearance from 4.338989 m to 8.708794 m;
- changing ground antenna height from 5 to 15 m changed clearance from 2.130928 m to 11.594961 m;
- lowering UAV altitude from 1,000 m to 900 m changed the 130 km classification from clear to `ground_intersection`; 1,100 m remained clear with 9.925075 m clearance;
- at the baseline endpoint heights, 135.75 km remained solved with 0.182915 m clearance, 135.85 km was `ground_grazing` with 0.036726 m modeled clearance, and 136 km was `ground_intersection`.

Numerical-tolerance changes altered baseline clearance by only micrometres, while atmosphere/height changes altered it by metres or changed status. The three uncertainty categories must therefore remain distinct:

1. **Numerical:** discretization, integration, shooting, and diagnostic sampling errors characterized here.
2. **Atmospheric model:** the dry reference and synthetic gradient factors are sensitivity inputs, not probability bounds or measured weather.
3. **Geometry/input:** antenna/UAV heights, datum, terrain, and surface representation can dominate a grazing classification.

Data and plots are [phase2b_near_horizon_sensitivity.csv](../outputs/phase2b/phase2b_near_horizon_sensitivity.csv), [phase2b_horizon_transition.png](../outputs/phase2b/phase2b_horizon_transition.png), and [phase2b_refractivity_sensitivity.png](../outputs/phase2b/phase2b_refractivity_sensitivity.png).

## 9. EER Benchmark Results

The dry profile over 0–1,000 m had sampled gradients from approximately -26.17 to -24.29 N-units/km. Their mean produces `k=1.191425654` with 3.75% maximum relative variation over the sampled interval. This `k` is derived from the atmospheric gradient, not fitted to ray results.

For 10 m/1,000 m endpoints, analytical horizons were:

| Reference | Horizon |
|---|---:|
| Geometric `k=1` | 124.161 km |
| Gradient-derived `k=1.1914` | 135.526 km |
| Conventional `k=4/3` | 143.371 km |

At 130 km, geometric `k=1` predicted blocked while both EER approximations and the ray were clear. At 140 km, `k=4/3` predicted visible while the ray and gradient-derived EER were blocked. Across the 12-case comparison, gradient-derived EER matched the ray visibility classifications, while `k=1` and `k=4/3` each disagreed in 2 cases. This finite matrix is a benchmark, not proof that the derived EER is generally equivalent to ray tracing.

See [phase2b_eer_comparison.csv](../outputs/phase2b/phase2b_eer_comparison.csv) and [phase2b_eer_benchmark.png](../outputs/phase2b/phase2b_eer_benchmark.png).

## 10. Numerical Accuracy and Remaining Uncertainty

For the declared smooth-sphere, dry-profile model, the evidence supports sub-centimetre endpoint accuracy and sub-millimetre production/reference geometric-length agreement in the tested independent cases. Fine-grid profile changes are larger than tight integration errors but remain below a millimetre in minimum clearance for 25 m versus 12.5 m sampling.

These values are numerical accuracy statements only. No measured refractivity profile, terrain survey, antenna phase-centre survey, or field propagation data were supplied. Consequently, no experimental error bar, real-world visibility probability, or operational link range can be assigned.

## 11. Supported Solver Domain

Automated and benchmark cases cover radial rays, unequal/equal heights, reversed endpoints, single-minimum paths, coincident endpoints, ground-level endpoints, near-tangent/grazing paths, ground intersection, invalid geometry, missing profile coverage, nonmonotonic `q`, exhausted shooting work, quadrature precision exhaustion, and the local-angle limit. Outcomes remain explicitly separated as solved, blocked within the model, unsupported model/branch, missing data, numerical failure, or invalid input.

The tested successful domain is the Phase 2A direct-ray subset only. No claim is made for ducts, multipath, multiple-eigenray enumeration, long/antipodal paths, or nonmonotonic refractivity distributions.

## 12. Known Limitations

- The atmosphere is dry ISA/P.453 or a synthetic perturbation, not contemporaneous weather.
- The independent Cartesian method shares the profile interpolation and physical assumptions.
- Fixed-step event interpolation limits the independent reference at the last digits.
- Quadrature diagnostics are cumulative across solver work and are not rigorous total-error bounds.
- Sampled invariant reconstruction is a post-processing diagnostic and is not monotonic with sample count.
- Ground is smooth and spherical; no terrain, geoid, vegetation, structures, diffraction, reflection, or roughness is modeled.
- Phase refractive index is treated as nondispersive for delay; no group index is implemented.
- No ray-tube amplitude, focusing, atmospheric absorption, fading, interference, or link availability is computed.
- There is no experimental validation data.

## 13. Regression Test Results

Pre-change combined baseline:

```text
74 passed, 15 subtests passed in 7.12 s
```

Focused Phase 2B verification after implementation:

```text
3 passed in 29.97 s
```

Final component and combined results:

```text
Original CubeSat: 38 passed, 15 subtests passed in 5.14 s
Phase 1:          26 passed in 0.18 s
Phase 2A:         10 passed in 2.22 s
Phase 2B:          3 passed in 29.97 s
Combined:         77 passed, 15 subtests passed in 35.22 s
```

The Phase 2B run includes complete regeneration of the output bundle. No failures, errors, or skips were reported, and no test strictness was reduced.

## 14. Reproduction Instructions

From the repository root with the configured scientific environment:

```powershell
.venv-science\Scripts\python.exe -m uav_cas.phase2b_demo --output-dir outputs\phase2b
.venv-science\Scripts\python.exe -m pytest -q tests\test_phase2b_verification.py
.venv-science\Scripts\python.exe -m pytest -q
```

The machine-readable overview is [phase2b_summary.json](../outputs/phase2b/phase2b_summary.json). The workflow uses no random inputs and stores fixed configurations, tolerances, and model hashes.

## 15. Readiness Assessment for Phase 3

**CONDITIONAL GO** for Phase 3 implementation, restricted to the verified direct-ray family and explicit smooth-sphere/profile assumptions.

The numerical solver has analytical, reciprocal, convergence, failure-taxonomy, and independent-formulation evidence adequate for beginning a coverage engine that preserves explicit unavailable/blocked/unsupported states. The condition is that Phase 3 must not interpret a clear ray as link availability; must not use EER as fallback; must retain the 0.05 m grazing policy and declared solver domain; and must propagate atmospheric/height uncertainty warnings near the visibility boundary. Terrain-aware or operational coverage claims remain a no-go without additional models and validation.
