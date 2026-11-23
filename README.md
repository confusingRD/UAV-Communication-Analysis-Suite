# UAV Communication Analysis Suite

UAV-CAS is an offline Python engineering application for refractivity-aware
UAV radio-link analysis. It combines bounded atmospheric profiles, a verified
spherical boundary-value ray solver, analytical geometric/EER references, an
ITU-R P.525 free-space link budget, deterministic reports, and a Streamlit UI
in one installable `uav_cas` package.

## Scientific scope

The production ray solver uses the Bouguer invariant in a spherical,
horizontally stratified, piecewise-linear refractive-index profile. It supports
short-arc radial, radial-monotonic, and single-minimum direct-ray branches.
Blocked, grazing, unsupported, missing-data, invalid-input, and numerical
failure states remain explicit. Geometric LOS and effective-Earth-radius
results are independent references; they never replace a failed ray solve.

Atmosphere options include dry ISA-1976 and the ITU-R P.835-7 annual
low-latitude reference atmosphere with ITU-R P.453-14 radio refractivity. The
link ledger uses ITU-R P.525-5 free-space loss at the endpoint chord distance.
Current results exclude terrain, clutter, diffraction, reflection, multipath,
gas/rain loss, focusing, interference, fading statistics, and field
validation.

## Install

UAV-CAS supports Python 3.11 through 3.13.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[reporting,test]"
```

The root project is the only distribution required.

## Run

Generate the deterministic report bundle:

```powershell
.venv\Scripts\python.exe -m uav_cas.reporting_cli --output-dir outputs/reporting
```

Start the Streamlit application:

```powershell
.venv\Scripts\python.exe -m streamlit run reporting_app.py
```

Additional reproducible workflows are available through
`uav-cas-atmosphere-demo`, `uav-cas-phase2a-demo`, and
`uav-cas-phase2b-demo` after installation.

## Verify

```powershell
.venv\Scripts\python.exe -m pytest -q
```

The verification suite covers atmosphere and refractivity models,
constant-index rays, branch classification, clearance and failure states,
convergence, reciprocity, an independent Cartesian Fermat reference, link
budgets, report exports, maximum connection estimates, and UI-facing
presentation contracts.

## References

- ITU-R P.453-14, *The radio refractive index: its formula and refractivity data*.
- ITU-R P.525-5, *Calculation of free-space attenuation*.
- ITU-R P.835-7, *Reference standard atmospheres*.
- ITU-R P.834-9, *Effects of tropospheric refraction on radiowave propagation*.
- U.S. Standard Atmosphere, 1976.

Software verification establishes consistency with the stated models and
tests. It is not experimental validation or an operational range guarantee.
