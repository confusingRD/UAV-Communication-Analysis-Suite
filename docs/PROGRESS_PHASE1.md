# UAV Communication Analysis Suite (UAV-CAS) — Phase 1 Progress

## 1. Project title and engineering objective

**UAV Communication Analysis Suite (UAV-CAS): atmospheric and engineering foundations for UAV-to-ground radio analysis.**

The immediate objective is a reproducible scientific foundation for evaluating how lower-atmosphere state and radio refractivity affect future UAV propagation calculations. Phase 1 establishes validated thermodynamic, refractivity, geometry, hardware, provenance, status, and reference-calculation contracts. It does **not** claim ray-based coverage.

## 2. Problem definition: atmospheric effects on UAV communication

UAV-to-ground radio propagation depends on endpoint geometry and the vertical refractive-index field. Pressure, temperature, and water vapour determine radio refractivity; its vertical gradient affects ray curvature. A conventional geometric horizon or effective-Earth-radius (EER) estimate can provide a useful analytical comparison, but neither replaces a refractivity-aware boundary-value ray solution. Link feasibility also depends on independent transmitter and receiver hardware in each direction.

This milestone therefore produces traceable atmospheric profiles and engineering contracts before attempting the Phase 2 ray-tracing boundary-value problem (BVP).

## 3. Proposed methodology and overall ray-tracing-first architecture

The approved architecture keeps three methods distinct:

1. A future atmospheric ray tracer is the primary propagation method.
2. Physical spherical geometric LOS is an independent limiting reference.
3. EER with declared `k` is an independent approximation reference.

Phase 1 creates bounded, immutable `n(h)` profiles with provenance and explicit unavailable states outside their domain. Common requests/results use stable status classifications (`solved`, modeled blockage, unsupported model/branch, missing data, numerical failure, invalid input). EER options do not enter a ray request, and analytical results cannot contain fabricated ray paths, optical path lengths, delays, or absorption.

The scientific core has no Qt dependency. Plotting is a headless consumer of calculated data. The original CubeSat library remains a separate preserved package.

## 4. Completed Phase 1 implementations

- Imported the audited `cubesat_link` 0.2.0 source tree, all eight original test modules (38 tests), schemas, examples, docs, wheel, and metadata into `packages/cubesat-link/` without changing its public API.
- Preserved both ZIP archives and the root UAV prototype unchanged.
- Added a `src/uav_cas/` package and root packaging/test configuration.
- Implemented ISA-1976-compatible dry lower atmosphere from 0 to 20 km geopotential altitude: tropospheric lapse layer and continuous 11–20 km isothermal layer.
- Implemented geometric/geopotential altitude conversion, temperature, pressure, density, Sutherland dynamic viscosity, and dry-air sound speed.
- Implemented ITU-R P.453-14 dry and specified local-humidity refractivity, including `N`, `n`, components, model metadata, and a conservative liquid-water RH conversion domain. A local RH value is never expanded into a vertical humidity profile.
- Implemented bounded piecewise-linear refractivity profiles, deterministic hashes, aligned thermodynamic states, one-sided knot gradients, strict non-extrapolation, and explicit `missing_data` evaluations.
- Implemented validated MSL/AGL geometry, independent endpoint radio hardware, uplink/downlink directionality, numerical settings, provenance, requests/results, and solver statuses.
- Implemented isolated spherical geometric and EER references for `k=1`, `k=4/3`, and a gradient-derived `k` constrained to a declared near-horizontal, approximately constant-gradient height interval.
- Reused the preserved ITU-R P.525 FSPL calculation in a directional reference link-budget ledger with separate TX/RX feeder losses and gains.
- Generated a reproducible headless atmospheric demonstration with CSV, JSON, and six 300 dpi PNG figures.

## 5. Governing physical equations and reference standards

For geometric altitude `z` and geopotential altitude `H`, using the standard-atmosphere effective radius `r_a = 6,356,766 m`:

```text
H = r_a z / (r_a + z)
```

For the troposphere (`0 <= H <= 11 km`):

```text
T = T0 - L H
p = p0 (T/T0)^[g0/(Rd L)]
rho = p/(Rd T)
```

with `T0=288.15 K`, `p0=101325 Pa`, `g0=9.80665 m/s²`, `Rd=287.05287 J/(kg K)`, and `L=0.0065 K/m`. Above 11 km through 20 km geopotential altitude, pressure uses the continuous isothermal-layer exponential equation.

```text
mu = 1.458e-6 T^(3/2)/(T + 110.4)       [Pa s]
a  = sqrt(1.4 Rd T)                       [m/s]
```

ITU-R P.453-14 refractivity uses pressure in hPa and temperature in K:

```text
pd = p_total - e
N  = 77.6 pd/T + 72 e/T + 3.75e5 e/T²
n  = 1 + N × 10^-6
```

The dry demonstration sets `e=0` explicitly as a reference assumption, not a humidity observation.

For an approximately constant vertical index gradient, the local EER comparison is:

```text
k = 1 / [1 + (R/n)(dn/dh)]
```

This is restricted to the declared gradient interval and near-horizontal approximation domain. It is not fitted to a ray result.

The conditional free-space reference budget reuses ITU-R P.525 spreading:

```text
FSPL = 20 log10(4 pi d f / c)
P_rx = P_tx - L_tx + G_tx + G_rx - L_rx - FSPL - L_other
M_design = P_rx - sensitivity - required_fade_margin
```

No atmospheric absorption model is implemented or silently assumed.

## 6. Numerical results and scientific figures

The demonstration uses a dry standard atmosphere from 0 to 5,000 m geometric MSL, sampled every 10 m. Its profile SHA-256 is `d61ad4966e704dd9c11e5d382351d5711e985eac171e406cd2a36c9eadd4d3d5`.

| Geometric altitude (m) | T (K) | p (Pa) | rho (kg/m³) | mu (Pa s) | a (m/s) | N (N-units) | n |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 288.150 | 101325.0 | 1.225000 | 1.78938e-5 | 340.294 | 272.872 | 1.000272872 |
| 500 | 284.900 | 95461.3 | 1.167273 | 1.77366e-5 | 338.370 | 260.014 | 1.000260014 |
| 1000 | 281.651 | 89876.3 | 1.111660 | 1.75785e-5 | 336.435 | 247.626 | 1.000247626 |
| 3000 | 268.659 | 70121.1 | 0.909254 | 1.69376e-5 | 328.584 | 202.539 | 1.000202539 |
| 5000 | 255.676 | 54048.3 | 0.736429 | 1.62825e-5 | 320.545 | 164.042 | 1.000164042 |

The dry 0–1 km profile has a mean `dn/dh = -2.52469e-8 1/m` (`-25.2469 N/km`) with 3.38% interval-gradient variation. Within that declared interval, the derived analytical reference is `k=1.19162`. The horizon figure also shows `k=1` and conventional `k=4/3`; all are labelled analytical references.

The manually traceable 2.4 GHz, 1 km reference has `FSPL=100.0520 dB`. With the declared asymmetric hardware, uplink received power is `-62.0520 dBm` and downlink received power is `-72.0520 dBm`. Both fixtures happen to have `17.9480 dB` design margin because their receiver sensitivities differ by 10 dB. This arithmetic does not establish coverage.

Figures:

- [Temperature versus altitude](../outputs/phase1/temperature_vs_altitude.png)
- [Pressure versus altitude](../outputs/phase1/pressure_vs_altitude.png)
- [Density versus altitude](../outputs/phase1/density_vs_altitude.png)
- [Radio refractivity versus altitude](../outputs/phase1/refractivity_N_vs_altitude.png)
- [Refractive index versus altitude](../outputs/phase1/refractive_index_vs_altitude.png)
- [Analytical horizon references](../outputs/phase1/analytical_horizon_references.png)

Machine-readable outputs are `uav_atmosphere_profile.csv`, `selected_uav_altitudes.csv`, and `phase1_summary.json` in `outputs/phase1/`.

## 7. Verification evidence and actual test results

Verification is numerical/software verification, not experimental validation.

- Untouched archive source suite on CPython 3.13.18: **38 tests passed, 0 failures, 0 errors**, 7.273 s.
- New Phase 1 suite alone (final run): **26 tests passed**, 0.10 s.
- Combined repository suite (final run): **64 tests passed plus 15 subtests**, 0 failures, 8.12 s.

An isolated deployment compatibility smoke also passed: an offscreen PySide6 6.12.0 / Matplotlib 3.11.2 QtAgg canvas rendered from source and from a PyInstaller 6.22.3 one-directory build on CPython 3.13.18. This confirms only basic import, canvas, freezer, and launch compatibility; it is not a production GUI or packaged UAV-CAS release.

An installed-origin check resolved `cubesat_link 0.2.0` to `packages/cubesat-link/cubesat_link/__init__.py` and `uav_cas 0.1.0` to `src/uav_cas/__init__.py`; the root legacy modules did not shadow either package.

New tests cover published ISA reference values, geometric/geopotential conversion, 11–20 km layer continuity, strict invalid inputs and units, dry and humid P.453 arithmetic, RH domain handling, bounded interpolation, missing boundaries, one-sided gradients, MSL/AGL conversion, hardware directionality, geometric/EER consistency, derived-k domain rejection, chord symmetry, manually calculated FSPL ledgers, and preserved CubeSat API/version presence. The full combined run executes all original CubeSat tests unchanged.

The original 38 passing tests verify only the preserved 0.2.0 behavior. They do not verify a general UAV ray BVP.

Reproduction:

```powershell
uv python install --install-dir .python --no-bin --no-registry 3.13
uv venv --python .python\cpython-3.13.18-windows-x86_64-none\python.exe .venv-science
uv pip install --python .venv-science\Scripts\python.exe -e packages\cubesat-link -e ".[demo,test]"
.venv-science\Scripts\python.exe -m pytest -q
.venv-science\Scripts\python.exe -m uav_cas.demo --output-dir outputs\phase1
```

## 8. Current scientific limitations

- The demonstration is a dry reference atmosphere, not contemporaneous measured weather.
- Local RH support does not invent a vertical humidity profile; a measured/imported full profile requires independent height-resolved data and provenance.
- The atmosphere is horizontally homogeneous and smooth; terrain, buildings, vegetation, diffraction, reflection, multipath, interference, antenna attitude patterns, and uncertainty propagation are absent.
- No gas/rain/cloud absorption backend is present.
- Geometric and EER results are approximation references only.
- The link budget uses endpoint distance and declared losses; it has no ray-integrated attenuation, refractive spreading, or field validation.
- No experimental dataset was supplied, so no measured accuracy bound or empirical validation claim is possible.

## 9. Explicitly unimplemented components

- General atmospheric ray-tracing BVP extensions and verified branch handling (Phase 2).
- Ray-based UAV communication coverage, range search, or coverage maps (Phase 3).
- Terrain/geoid/weather ingestion, attenuation generation, diffraction, multipath, or full-wave modeling.
- Production desktop GUI, controllers/workers, and scientific pages.
- Release executable, installer, or deployment certification.
- CubeSat-specific feature expansion.

The tagged legacy `raytrace.py` remains preserved source evidence. Its shooting implementation is not called by the Phase 1 package and is not presented as verified UAV-CAS ray tracing.

## 10. Next step: Phase 2 UAV ray-tracing BVP verification and extension

Phase 2 should begin only with the now-bounded `n(h)` profile and endpoint/status contracts. Required work is an additive reusable BVP/path API; independent Cartesian Fermat integration/shooting; vacuum, constant-index, equal/unequal-height, reversed, near-tangent, and internal-minimum fixtures; endpoint/tangent residuals; invariant conservation; profile/quadrature/shooting/sampling convergence; ground-clearance uncertainty; explicit branch completeness limits; and failure taxonomy tests. Old APIs and all 38 regression tests must remain unchanged. Only after this gate passes may Phase 3 consume ray results for coverage.

## Tóm tắt tiến độ bằng tiếng Việt

Giai đoạn 1 đã hoàn thành phần nền tảng khoa học cho bài toán liên lạc UAV–trạm mặt đất: mô hình khí quyển chuẩn ISA (nhiệt độ, áp suất, mật độ, độ nhớt động lực học, vận tốc âm thanh), chuyển đổi độ cao hình học/thế năng, tính chiết suất vô tuyến theo ITU-R P.453-14, hồ sơ `n(h)` có miền dữ liệu hữu hạn, hợp đồng MSL/AGL, phần cứng phát/thu độc lập, đường lên/đường xuống, tham chiếu LOS hình học/EER và ngân sách liên kết FSPL cơ bản. Chương trình minh họa đã tạo bảng CSV/JSON và các hình PNG 300 dpi từ phép tính thực.

Kết quả kiểm thử thực tế: 38/38 kiểm thử CubeSat nguyên bản đạt; 26 kiểm thử Phase 1 mới đạt; toàn bộ kho mã đạt 64 kiểm thử và 15 subtest, không có lỗi. Đây là **xác minh số và phần mềm**, chưa phải kiểm chứng thực nghiệm ngoài hiện trường.

Hiện chưa có bộ giải BVP truy vết tia UAV đã được xác minh, chưa có vùng phủ sóng dựa trên tia, chưa có mô hình suy hao hấp thụ khí quyển đã kiểm chứng, chưa có địa hình, dữ liệu đo thực địa, GUI hoàn chỉnh hoặc tệp `.exe` phát hành. Các đường chân trời `k=1`, `k=4/3` và `k` suy ra từ gradient chỉ là tham chiếu giải tích, không phải dự đoán truy vết tia. Bước tiếp theo được đề xuất là Phase 2: xây dựng và kiểm chứng độc lập bộ giải BVP, nghiệm nhánh, sai số đầu mút, bảo toàn bất biến và hội tụ số trước khi tính vùng phủ sóng.

