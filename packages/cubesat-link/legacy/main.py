"""main.py - CLI v0.   python main.py --help   (GUI: streamlit run app.py)"""
import argparse, os
import numpy as np
from config import Inputs
import service, plots


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--f", type=float, default=2400.0, help="MHz")
    ap.add_argument("--lat", type=float, default=10.8)
    ap.add_argument("--hu", type=float, default=11000.0, help="độ cao UAV (m)")
    ap.add_argument("--hg", type=float, default=0.0)
    ap.add_argument("--hant", type=float, default=10.0)
    ap.add_argument("--d", type=float, default=300.0, help="km")
    ap.add_argument("--ptx", type=float, default=30.0, help="dBm")
    ap.add_argument("--sens", type=float, default=-105.0, help="dBm (datasheet)")
    ap.add_argument("--source", default="itur", choices=["itur", "fallback"])
    ap.add_argument("--out", default="out")
    a = ap.parse_args()

    inp = Inputs()
    inp.link.f_MHz, inp.link.P_tx_dBm, inp.link.sensitivity_dBm = a.f, a.ptx, a.sens
    inp.geom.h_u_m, inp.geom.h_g_m, inp.geom.h_ant_m, inp.geom.d_km = a.hu, a.hg, a.hant, a.d
    inp.site.lat_deg, inp.cfg.atmosphere_source = a.lat, a.source
    res = service.run(inp)
    os.makedirs(a.out, exist_ok=True)

    print(f"\n=== Khí quyển ({res.prof.source}) tại độ cao UAV ===")
    for k, v in res.atm_uav.items():
        print(f"  {k:<26}{v:>16.6g}")
    print(f"\n=== Đường truyền ===\n  Chân trời vô tuyến k=4/3: {res.horizon_km:.1f} km; "
          f"d_max ray tracing: {res.info['d_max_ray_km']:.1f} km")
    r, b = res.ray, res.budget
    if r is not None:
        print(f"  θ0 {np.degrees(r.theta0):.4f}° | góc ngẩng hình học {np.degrees(r.eps_geo):.4f}° | "
              f"L {r.L_m/1000:.3f} km | trễ thừa {r.excess_delay_m:.1f} m")
        print(f"\n=== Link budget ===\n  FSPL {b.FSPL_dB:.2f} | A_gas {b.A_gas_dB:.4f} | A_defocus {b.A_defocus_dB:.3f} dB")
        print(f"  P_rx {b.P_rx_dBm:.2f} dBm | Margin {b.margin_dB:.2f} dB | {'ĐẠT' if b.ok else 'KHÔNG ĐẠT'}")
        print(f"  Tầm xa tối đa: {service.max_range(res, inp.link.fade_margin_req_dB):.0f} km")
        plots.plot_rays(res.fan, r, inp.geom, f"{a.out}/rays.png")
        plots.plot_losses(res.rows, inp.link.fade_margin_req_dB, f"{a.out}/losses_margin.png")
    plots.plot_atmosphere(res.prof, f"{a.out}/atmosphere.png", inp.geom.h_u_m)
    for n in res.notes:
        print("  ! " + n)


if __name__ == "__main__":
    main()
