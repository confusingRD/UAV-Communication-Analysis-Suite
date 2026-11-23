"""Professional single-screen Streamlit dashboard for UAV-CAS reporting."""

from __future__ import annotations

import csv
from dataclasses import asdict
import io
import json

from matplotlib import pyplot as plt
import streamlit as st

from uav_cas.reporting import (
    AtmosphereModel,
    REFERENCE_LATITUDE_DEG,
    REFERENCE_LONGITUDE_DEG,
    ReportingInputs,
    altitude_coverage_curve,
    analyze_reporting_case,
    dashboard_state,
    estimate_maximum_connection,
    maximum_distance_label,
)
from uav_cas.visualization.reporting import (
    atmosphere_profile_figure,
    communication_performance_figure,
    maximum_connection_region_figure,
    ray_cross_section_figure,
)


def _figure_png(figure) -> bytes:
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", dpi=300, bbox_inches="tight")
    return buffer.getvalue()


def _performance_csv(maximum, result) -> bytes:
    buffer = io.StringIO()
    fieldnames = [
        "surface_distance_km",
        "ray_status",
        "ray_visible",
        "link_margin_db",
        "feasible",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    rows = [asdict(point) for point in maximum.points]
    if not any(
        abs(row["surface_distance_km"] - result.inputs.surface_distance_km) < 1.0e-12
        for row in rows
    ):
        rows.append(
            {
                "surface_distance_km": result.inputs.surface_distance_km,
                "ray_status": result.ray_outputs.solver_status,
                "ray_visible": result.ray_outputs.ray_visibility,
                "link_margin_db": result.link_outputs.link_margin_db,
                "feasible": result.link_outputs.communication_feasible,
            }
        )
    writer.writerows(sorted(rows, key=lambda row: row["surface_distance_km"]))
    return buffer.getvalue().encode("utf-8")


def _summary_json(result, maximum) -> str:
    summary = {
        "application": "UAV Communication Analysis Suite",
        "reference_scenario": {
            "description": "Low-latitude reference-atmosphere example",
            "latitude_deg_n": REFERENCE_LATITUDE_DEG,
            "longitude_deg_e": REFERENCE_LONGITUDE_DEG,
            "warning": "Coordinates are metadata; no location-specific weather is generated.",
        },
        "inputs": asdict(result.inputs),
        "atmosphere": asdict(result.atmosphere),
        "ray": asdict(result.ray_outputs),
        "link": asdict(result.link_outputs),
        "maximum_connection": {
            key: value for key, value in asdict(maximum).items() if key != "points"
        },
        "profile": {
            "source": result.profile.source,
            "model_version": result.profile.model_version,
            "profile_sha256": result.profile.profile_hash,
        },
    }
    return json.dumps(summary, indent=2, default=str)


def _altitude_candidates(inputs: ReportingInputs) -> list[float]:
    candidates = {
        100.0,
        250.0,
        500.0,
        1_000.0,
        2_000.0,
        3_000.0,
        5_000.0,
        inputs.uav_altitude_msl_m,
    }
    return sorted(
        value for value in candidates if value > inputs.ground_station_height_msl_m
    )


st.set_page_config(
    page_title="UAV Communication Analysis Suite",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1500px;}
      .app-title {font-size: 2.05rem; font-weight: 760; letter-spacing: -0.025em; margin: 0;}
      .app-subtitle {font-size: 1.08rem; color: #52606d; margin: 0.15rem 0 0.65rem 0;}
      .app-meta {font-size: 0.84rem; color: #657786; margin-bottom: 0.8rem;}
      .status-panel {border-radius: 0.6rem; padding: 1rem 1.2rem; margin: 0.2rem 0 1rem 0;}
      .status-available {background: #e9f7ef; border-left: 0.45rem solid #16835f; color: #0d503a;}
      .status-unavailable {background: #fff4e5; border-left: 0.45rem solid #d97706; color: #7a3e00;}
      .status-unresolved {background: #f3effb; border-left: 0.45rem solid #6b21a8; color: #4b176f;}
      .status-title {font-size: 1.35rem; font-weight: 760; margin-bottom: 0.2rem;}
      .status-text {font-size: 0.96rem;}
      div[data-testid="stMetric"] {border: 1px solid #d8dee4; border-radius: 0.55rem; padding: 0.8rem 0.9rem;}
      div[data-testid="stMetricLabel"] {white-space: normal;}
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown('<p class="app-title">UAV Communication Analysis Suite</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="app-subtitle">UAV Communication &amp; Radio Propagation Simulator</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="app-meta">Atmosphere: ITU-R P.835-7 + P.453-14 by default &nbsp;•&nbsp; '
    'Simulation: smooth-Earth direct-ray propagation &nbsp;•&nbsp; '
    'Scenario: configurable reference-atmosphere analysis</p>',
    unsafe_allow_html=True,
)

st.subheader("Simulation setup")
with st.form("simulation_setup", clear_on_submit=False):
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("**Geometry & atmosphere**")
        ground_height = st.number_input(
            "Ground station antenna altitude (m MSL)",
            min_value=0.0,
            max_value=19_999.0,
            value=10.0,
            help=(
                "Radial antenna altitude above mean sea level. This is not antenna height "
                "above local terrain; terrain is not modeled."
            ),
        )
        uav_altitude = st.number_input(
            "UAV altitude (m MSL)",
            min_value=0.1,
            max_value=20_000.0,
            value=1_000.0,
            help="UAV radial altitude above the smooth mean-sea-level sphere.",
        )
        distance = st.number_input(
            "Surface distance (km)",
            min_value=0.0,
            max_value=2_200.0,
            value=50.0,
            help=(
                "Distance along Earth's surface from the ground station to the point "
                "directly below the UAV."
            ),
        )
        atmosphere = st.selectbox(
            "Atmospheric model",
            (AtmosphereModel.ITU.value, AtmosphereModel.ISA.value),
            index=0,
            help=(
                "ITU uses the P.835-7 annual low-latitude reference atmosphere with "
                "P.453-14 refractivity. ISA is a dry comparison model."
            ),
        )
    with right:
        st.markdown("**Radio system**")
        frequency = st.number_input(
            "Radio frequency (MHz)",
            min_value=0.001,
            value=2_400.0,
            help="Carrier frequency used by the endpoint-chord ITU-R P.525 FSPL calculation.",
        )
        tx_power = st.number_input(
            "Transmit power (dBm)",
            value=30.0,
            help="Power delivered by the transmitter before the declared TX system loss.",
        )
        sensitivity = st.number_input(
            "Receiver sensitivity (dBm)",
            value=-100.0,
            help="Use the datasheet value for the actual receiver mode and packet rate.",
        )
        st.info(
            "The default radio values are a synthetic demonstration, not a universal "
            "radio specification."
        )

    with st.expander("Advanced settings", expanded=False):
        gain_col, loss_col, sweep_col = st.columns(3, gap="large")
        with gain_col:
            tx_gain = st.number_input("Transmitter gain (dBi)", value=2.0)
            rx_gain = st.number_input("Receiver gain (dBi)", value=2.0)
            required_margin = st.number_input(
                "Required fade margin (dB)", min_value=0.0, value=0.0
            )
        with loss_col:
            tx_loss = st.number_input(
                "TX feeder/system loss (dB)", min_value=0.0, value=1.0
            )
            rx_loss = st.number_input(
                "RX feeder/system loss (dB)", min_value=0.0, value=1.0
            )
        with sweep_col:
            sweep_min = st.number_input(
                "Sweep minimum distance (km)", min_value=0.0, value=0.0
            )
            sweep_max = st.number_input(
                "Sweep maximum distance (km)",
                min_value=0.1,
                max_value=2_200.0,
                value=500.0,
            )
            sweep_step = st.number_input(
                "Coarse sweep step (km)", min_value=0.05, value=5.0
            )
            st.caption(
                "The first feasible-to-infeasible transition is refined. If no transition "
                "is found, the configured sweep limit is reported—not a physical maximum."
            )
    submitted = st.form_submit_button(
        "Run Simulation", type="primary", use_container_width=True
    )

if submitted:
    try:
        inputs = ReportingInputs(
            ground_station_height_msl_m=ground_height,
            uav_altitude_msl_m=uav_altitude,
            surface_distance_km=distance,
            frequency_mhz=frequency,
            transmit_power_dbm=tx_power,
            transmitter_gain_dbi=tx_gain,
            receiver_gain_dbi=rx_gain,
            tx_loss_db=tx_loss,
            rx_loss_db=rx_loss,
            receiver_sensitivity_dbm=sensitivity,
            required_margin_db=required_margin,
            atmosphere_model=atmosphere,
            sweep_min_km=sweep_min,
            sweep_max_km=sweep_max,
            sweep_step_km=sweep_step,
        )
        with st.status("Running direct-ray simulation...", expanded=True) as run_status:
            st.write("Solving the requested endpoint ray and link budget...")
            result = analyze_reporting_case(inputs)
            st.write("Sweeping the configured distance interval...")
            maximum = estimate_maximum_connection(inputs)
            st.write("Calculating altitude sensitivity for the coverage figure...")
            coverage = altitude_coverage_curve(inputs, _altitude_candidates(inputs))
            run_status.update(label="Simulation complete", state="complete", expanded=False)
        st.session_state["completed_simulation"] = (result, maximum, coverage)
    except ValueError as exc:
        st.error(f"Input validation failed: {exc}")

if "completed_simulation" not in st.session_state:
    st.caption("Run the simulation to calculate link status, limiting range, and plots.")
else:
    result, maximum, coverage = st.session_state["completed_simulation"]
    state = dashboard_state(result)
    ray = result.ray_outputs
    link = result.link_outputs
    st.divider()
    st.subheader("Communication result")
    st.markdown(
        f'<div class="status-panel status-{state.status_kind}">'
        f'<div class="status-title">{state.status_label}</div>'
        f'<div class="status-text">{state.explanation}</div></div>',
        unsafe_allow_html=True,
    )

    maximum_value = maximum_distance_label(maximum)
    metric_columns = st.columns(4, gap="medium")
    metric_columns[0].metric("Estimated max distance", maximum_value)
    metric_columns[1].metric(
        "Link margin",
        "Unavailable" if link.link_margin_db is None else f"{link.link_margin_db:.2f} dB",
    )
    metric_columns[2].metric(
        "Received power",
        "Unavailable"
        if link.received_power_dbm is None
        else f"{link.received_power_dbm:.2f} dBm",
    )
    metric_columns[3].metric("Ray visibility", state.ray_visibility_label)
    st.markdown(f"**Limiting factor:** {maximum.limiting_condition}")
    st.caption(
        f"{maximum.limiting_reason} Boundary-search resolution: "
        f"{maximum.resolution_km:.3f} km."
    )

    st.subheader("Communication performance")
    performance_figure = communication_performance_figure(
        maximum.points,
        requested_distance_km=result.inputs.surface_distance_km,
        maximum=maximum,
        requested_result=result,
    )
    st.pyplot(performance_figure, use_container_width=True)
    performance_png = _figure_png(performance_figure)
    plt.close(performance_figure)

    coverage_col, ray_col = st.columns(2, gap="large")
    with coverage_col:
        st.markdown("**Maximum connection region**")
        coverage_figure = maximum_connection_region_figure(coverage)
        st.pyplot(coverage_figure, use_container_width=True)
        coverage_png = _figure_png(coverage_figure)
        plt.close(coverage_figure)
    with ray_col:
        st.markdown("**Ray-tracing cross-section**")
        ray_figure = ray_cross_section_figure(result)
        st.pyplot(ray_figure, use_container_width=True)
        ray_png = _figure_png(ray_figure)
        plt.close(ray_figure)

    with st.expander("Atmospheric & Scientific Details", expanded=False):
        st.caption(
            "The selected atmosphere is a horizontally homogeneous reference profile, not "
            "measured weather. The retained 10.82° N, 106.63° E example coordinates are "
            "metadata and do not make the profile location-specific."
        )
        atmospheric_values = st.columns(5)
        atmospheric_values[0].metric("Temperature", f"{result.atmosphere.temperature_k:.2f} K")
        atmospheric_values[1].metric("Pressure", f"{result.atmosphere.pressure_pa:.1f} Pa")
        atmospheric_values[2].metric("Density", f"{result.atmosphere.density_kg_m3:.5f} kg/m³")
        atmospheric_values[3].metric(
            "Refractivity N", f"{result.atmosphere.radio_refractivity_n_units:.3f}"
        )
        atmospheric_values[4].metric(
            "Refractive index n", f"{result.atmosphere.refractive_index:.9f}"
        )
        st.caption(f"Profile source: {result.profile.source}")
        atmosphere_figure = atmosphere_profile_figure(result.profile)
        st.pyplot(atmosphere_figure, use_container_width=True)
        atmosphere_png = _figure_png(atmosphere_figure)
        plt.close(atmosphere_figure)

    with st.expander("Detailed Engineering Results", expanded=False):
        st.markdown("**Visibility classification**")
        st.dataframe(
            {
                "Quantity": ["Geometric line of sight", "Refracted direct ray", "Communication"],
                "Result": [
                    "Visible" if ray.geometric_visibility else "Blocked",
                    state.ray_visibility_label,
                    state.status_label,
                ],
            },
            hide_index=True,
            use_container_width=True,
        )
        detail_left, detail_right = st.columns(2, gap="large")
        with detail_left:
            st.markdown("**Ray solver**")
            st.dataframe(
                {
                    "Output": [
                        "Solver status",
                        "Reason code",
                        "Ray branch",
                        "Minimum clearance",
                        "Geometric path length",
                        "Optical path length",
                        "Excess propagation delay",
                    ],
                    "Value": [
                        ray.solver_status,
                        ray.reason_code,
                        ray.ray_branch,
                        None
                        if ray.minimum_clearance_m is None
                        else f"{ray.minimum_clearance_m:.3f} m",
                        None
                        if ray.geometric_path_length_m is None
                        else f"{ray.geometric_path_length_m:.3f} m",
                        None
                        if ray.optical_path_length_m is None
                        else f"{ray.optical_path_length_m:.3f} m",
                        None
                        if ray.excess_delay_s is None
                        else f"{ray.excess_delay_s * 1e9:.3f} ns",
                    ],
                },
                hide_index=True,
                use_container_width=True,
            )
        with detail_right:
            st.markdown("**Conditional link budget**")
            st.dataframe(
                {
                    "Output": [
                        "Received power",
                        "P.525 endpoint-chord FSPL",
                        "Total modeled TX + FSPL + RX losses",
                        "Link margin after required reserve",
                        "Feasibility reason",
                    ],
                    "Value": [
                        None
                        if link.received_power_dbm is None
                        else f"{link.received_power_dbm:.3f} dBm",
                        None
                        if link.free_space_path_loss_db is None
                        else f"{link.free_space_path_loss_db:.3f} dB",
                        None
                        if link.total_losses_db is None
                        else f"{link.total_losses_db:.3f} dB",
                        None
                        if link.link_margin_db is None
                        else f"{link.link_margin_db:.3f} dB",
                        link.reason,
                    ],
                },
                hide_index=True,
                use_container_width=True,
            )
        st.markdown("**Coverage search diagnostics**")
        st.dataframe(
            {
                "Quantity": [
                    "Analyzed interval",
                    "Coarse sweep step",
                    "Boundary resolution",
                    "Limiting condition",
                    "Limiting reason",
                ],
                "Value": [
                    f"{result.inputs.sweep_min_km:.3f}–{result.inputs.sweep_max_km:.3f} km",
                    f"{result.inputs.sweep_step_km:.3f} km",
                    f"{maximum.resolution_km:.3f} km",
                    maximum.limiting_condition,
                    maximum.limiting_reason,
                ],
            },
            hide_index=True,
            use_container_width=True,
        )
        st.caption(
            "The power model uses endpoint-chord ITU-R P.525 free-space spreading. "
            "No refractive focusing, gas/rain loss, terrain, or fading statistics are included."
        )

    st.subheader("Downloads")
    download_columns = st.columns(5)
    download_columns[0].download_button(
        "Summary JSON",
        _summary_json(result, maximum),
        file_name="simulation_summary.json",
        mime="application/json",
        use_container_width=True,
    )
    download_columns[1].download_button(
        "Performance CSV",
        _performance_csv(maximum, result),
        file_name="communication_performance.csv",
        mime="text/csv",
        use_container_width=True,
    )
    download_columns[2].download_button(
        "Coverage PNG",
        coverage_png,
        file_name="maximum_connection_region.png",
        mime="image/png",
        use_container_width=True,
    )
    download_columns[3].download_button(
        "Ray plot PNG",
        ray_png,
        file_name="ray_tracing.png",
        mime="image/png",
        use_container_width=True,
    )
    download_columns[4].download_button(
        "Atmosphere PNG",
        atmosphere_png,
        file_name="atmospheric_profile.png",
        mime="image/png",
        use_container_width=True,
    )
    st.warning(
        "Idealized reporting model only: smooth spherical Earth, reference atmosphere, "
        "direct ray, and endpoint-chord free-space spreading. Terrain, clutter, diffraction, "
        "reflection, multipath, interference, fading, gas/rain loss, and field validation "
        "are not included."
    )
