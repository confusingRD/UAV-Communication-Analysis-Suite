"""app.py - GUI Streamlit cho solver UAV.   Chạy:  streamlit run app.py"""
import json
import numpy as np
import pandas as pd
import streamlit as st

from config import Inputs, LinkInputs, GeometryInputs, SiteInputs, SolverConfig, H_MAX_V0
import service, plots, refractivity

st.set_page_config(page_title="UAV Link Solver", page_icon="📡", layout="wide")

CITIES = {"TP. Hồ Chí Minh": 10.8, "Hà Nội": 21.03, "Đà Nẵng": 16.05, "Cần Thơ": 10.03, "Tuỳ chỉnh": None}
FREQS = {"ELRS 868 MHz": 868.0, "ELRS 915 MHz": 915.0, "ELRS 2.4 GHz": 2400.0, "Tuỳ chỉnh": None}


def itur_available():
    try:
        import itur  # noqa
        return True
    except Exception:
        return False


@st.cache_resource(show_spinner=False)
def cached_run(key: str):
    """Cache theo nội dung input (JSON). Dùng cache_resource vì kết quả chứa hàm nội suy."""
    return service.run(service.inputs_from_dict(json.loads(key)))


# ---------------------------------------------------------------- Sidebar
sb = st.sidebar
sb.title("📡 UAV Link Solver")
sb.caption("v0 · tầng đối lưu (h ≤ 11 km) · ITU-R P.835 / P.453 / P.676")

with sb.expander("📻 Sóng & phần cứng", expanded=True):
    fp = st.selectbox("Tần số", list(FREQS), index=2)
    f_MHz = st.number_input("f (MHz)", 100.0, 10000.0, FREQS[fp] or 2400.0, 1.0,
                            key=f"f_{fp}", disabled=FREQS[fp] is not None)
    f_MHz = FREQS[fp] or f_MHz
    P_tx = st.number_input("Công suất TX (dBm)", -10.0, 40.0, 30.0, 1.0)
    G_tx = st.number_input("Độ lợi anten TX (dBi)", -5.0, 30.0, 2.0, 0.5)
    G_rx = st.number_input("Độ lợi anten RX (dBi)", -5.0, 30.0, 2.0, 0.5)
    L_cab = st.number_input("Tổn hao cáp/connector (dB)", 0.0, 10.0, 1.0, 0.5)
    sens = st.number_input("Độ nhạy RX (dBm)", -140.0, -60.0, -105.0, 1.0,
                           help="Lấy từ datasheet đúng module ELRS và đúng packet rate.")
    fade = st.number_input("Margin yêu cầu (dB)", 0.0, 40.0, 10.0, 1.0)

with sb.expander("📍 Vị trí & hình học", expanded=True):
    city = st.selectbox("Vị trí trạm", list(CITIES))
    lat = st.number_input("Vĩ độ (°)", -90.0, 90.0, CITIES[city] or 10.8, 0.01,
                          key=f"lat_{city}", disabled=CITIES[city] is not None)
    lat = CITIES[city] or lat
    h_g = st.number_input("Độ cao mặt đất tại trạm (m)", 0.0, 3000.0, 0.0, 10.0)
    h_ant = st.number_input("Chiều cao anten trạm (m)", 0.0, 200.0, 10.0, 1.0)
    h_u = st.slider("Độ cao UAV (m)", 100, int(H_MAX_V0), 11000, 100)
    d_km = st.slider("Khoảng cách mặt đất d (km)", 5, 600, 300, 5)

with sb.expander("⚙️ Nâng cao"):
    has_itur = itur_available()
    src = st.radio("Nguồn khí quyển", ["itur", "fallback"], index=0 if has_itur else 1,
                   format_func=lambda s: {"itur": "ITU-R P.835 (itur)", "fallback": "Dự phòng ISA (không theo vĩ độ)"}[s])
    sb.caption("itur: " + ("✅ đã cài" if has_itur else "❌ chưa cài → tự dùng dự phòng"))
    en_gas = st.checkbox("Hấp thụ khí (P.676)", True)
    en_dfc = st.checkbox("Defocusing", True)
    dh = st.select_slider("Bước lưới độ cao (m)", [25, 50, 100, 200], 50)

run = sb.button("▶ Tính toán", type="primary", use_container_width=True)

# ---------------------------------------------------------------- Chạy
inp = Inputs(LinkInputs(f_MHz, P_tx, G_tx, G_rx, L_cab, sens, fade),
             GeometryInputs(h_g, h_ant, float(h_u), float(d_km)),
             SiteInputs(lat, 106.7),
             SolverConfig(dh_m=float(dh), enable_gas=en_gas, enable_defocus=en_dfc, atmosphere_source=src))
key = json.dumps(service.inputs_to_dict(inp), sort_keys=True)

if run or "last_key" not in st.session_state:
    st.session_state["last_key"] = key
shown_key = st.session_state["last_key"]
if shown_key != key:
    st.info("Bạn đã đổi tham số. Bấm **▶ Tính toán** để cập nhật kết quả (đang hiển thị kết quả cũ).")

try:
    with st.spinner("Đang ray tracing và tính link budget…"):
        res = cached_run(shown_key)
except ValueError as e:
    st.error(f"Đầu vào không hợp lệ: {e}")
    st.stop()
except Exception as e:  # noqa
    st.error(f"Lỗi khi tính: {e!r}")
    st.stop()

cur = service.inputs_from_dict(json.loads(shown_key))   # đúng input của kết quả đang hiển thị
lk, g = cur.link, cur.geom

# ---------------------------------------------------------------- Tiêu đề + chỉ số chính
st.title("Solver đường truyền UAV tầm cao")
st.caption(f"{lk.f_MHz:g} MHz · vĩ độ {cur.site.lat_deg:g}° · UAV {g.h_u_m:g} m · d = {g.d_km:g} km · "
           f"khí quyển: {res.prof.source}")

b, r = res.budget, res.ray
if r is None:
    st.error(f"⛔ UAV nằm ngoài chân trời vô tuyến (d tối đa theo tia ≈ {res.info['d_max_ray_km']:.0f} km). "
             "v0 chưa có nhiễu xạ nên không tính link budget cho khoảng cách này. "
             "Hãy giảm d (đồ thị 'Tổn hao & margin' vẫn cho thấy vùng tính được).")
else:
    max_r = service.max_range(res, lk.fade_margin_req_dB)
    (st.success if b.ok else st.error)(
        f"{'✅ ĐẠT' if b.ok else '❌ KHÔNG ĐẠT'}: margin {b.margin_dB:.1f} dB "
        f"(yêu cầu {lk.fade_margin_req_dB:g} dB)")
    c = st.columns(5)
    c[0].metric("P_rx", f"{b.P_rx_dBm:.1f} dBm")
    c[1].metric("Margin", f"{b.margin_dB:.1f} dB")
    c[2].metric("FSPL", f"{b.FSPL_dB:.1f} dB")
    c[3].metric("Độ dài đường thật", f"{b.L_km:.1f} km")
    c[4].metric("Tầm xa tối đa", f"{max_r:.0f} km", help="Margin ≥ yêu cầu; nội suy từ lưới quét d.")

tabs = st.tabs(["🛰️ Quỹ đạo tia", "📉 Tổn hao & margin", "🌡️ Khí quyển", "📋 Chi tiết đường truyền", "⚠️ Ghi chú"])

with tabs[0]:
    st.pyplot(plots.plot_rays(res.fan, r, g))
    st.caption("Trục đứng tính từ mặt phẳng tiếp tuyến tại trạm nên mặt đất cong xuống. "
               "Chùm xanh: các góc phóng khác nhau; đỏ: tia tới UAV.")

with tabs[1]:
    if res.rows:
        st.pyplot(plots.plot_losses(res.rows, lk.fade_margin_req_dB, d_mark_km=g.d_km))
        df = pd.DataFrame([vars(x) for x in res.rows]).rename(columns={
            "d_km": "d (km)", "L_km": "L (km)", "FSPL_dB": "FSPL (dB)", "A_gas_dB": "A_gas (dB)",
            "A_defocus_dB": "A_defocus (dB)", "L_cable_dB": "Cáp (dB)", "P_rx_dBm": "P_rx (dBm)",
            "margin_dB": "Margin (dB)", "ok": "Đạt"})
        with st.expander("Bảng số liệu"):
            st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("⬇ Tải CSV", df.to_csv(index=False).encode("utf-8"), "link_budget_sweep.csv", "text/csv")
    else:
        st.warning("Không có điểm nào trong vùng tính được.")

with tabs[2]:
    st.subheader("Tính chất không khí")
    h_sel = st.slider("Độ cao xem (m)", int(res.prof.h_m[0]), int(res.prof.h_m[-1] - 500), int(g.h_u_m), 50,
                      help="Mặc định là độ cao UAV.")
    tab = refractivity.atmosphere_at(res.prof, float(h_sel), lk.f_MHz)
    units = {"h (m)": "m", "T (K)": "K", "p (hPa)": "hPa", "rho_wv (g/m3)": "g/m³", "e (hPa)": "hPa",
             "rho_air (kg/m3)": "kg/m³", "N": "N-units", "n": "", "M": "M-units", "dN/dh (N/km)": "N/km",
             "k_eff": "", "v = c/n (m/s)": "m/s", "lambda0 (m)": "m", "lambda = lambda0/n (m)": "m"}
    st.dataframe(pd.DataFrame({"Đại lượng": list(tab), "Giá trị": [f"{v:.8g}" for v in tab.values()],
                               "Đơn vị": [units.get(k, "") for k in tab]}),
                 use_container_width=True, hide_index=True)
    st.pyplot(plots.plot_atmosphere(res.prof, h_mark_m=h_sel))
    st.pyplot(plots.plot_gradient(res.prof, h_mark_m=h_sel))

with tabs[3]:
    if r is None:
        st.info("Không có tia tới UAV ở khoảng cách này.")
    else:
        rows = {
            "Góc phóng θ₀ (°)": np.degrees(r.theta0),
            "Góc ngẩng hình học (°)": np.degrees(r.eps_geo),
            "Độ lệch góc do khúc xạ tại trạm (°)": np.degrees(r.theta0 - r.eps_geo),
            "Góc ngẩng cục bộ tại UAV (°)": np.degrees(r.theta_arr),
            "Tổng độ uốn tia (mdeg)": np.degrees(r.bend_total) * 1000,
            "Độ dài đường thật (km)": r.L_m / 1000,
            "Trễ thừa ∫(n−1)ds (m)": r.excess_delay_m,
            "Trễ thừa (ns)": r.excess_delay_m / 299792458 * 1e9,
            "Chân trời vô tuyến k=4/3 (km)": res.horizon_km,
            "d tối đa theo ray tracing (km)": res.info["d_max_ray_km"],
        }
        st.dataframe(pd.DataFrame({"Đại lượng": list(rows), "Giá trị": [f"{v:.6g}" for v in rows.values()]}),
                     use_container_width=True, hide_index=True)
        st.markdown(f"**Link budget:** P_rx = {lk.P_tx_dBm:g} + {lk.G_tx_dBi:g} + {lk.G_rx_dBi:g} − {lk.L_cable_dB:g} "
                    f"− ({b.FSPL_dB:.2f} + {b.A_gas_dB:.3f} + {b.A_defocus_dB:.3f}) = **{b.P_rx_dBm:.2f} dBm**")

with tabs[4]:
    for n in res.notes:
        st.warning(n)
    st.markdown("- Defocusing là ước lượng số, chưa đối chiếu P.834.\n"
                "- P.676 chỉ hợp lệ từ 1 GHz; 868/915 MHz được kẹp về 1 GHz.\n"
                "- Độ nhạy RX phải lấy từ datasheet đúng module/packet rate.")

# ---------------------------------------------------------------- Lưu/nạp cấu hình
with st.sidebar.expander("💾 Cấu hình"):
    st.download_button("Tải cấu hình (JSON)", key, "uav_config.json", "application/json")
