"""plots.py - đồ thị v0. Mỗi hàm TRẢ VỀ matplotlib Figure; nếu có path thì lưu thêm PNG."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from config import A_EARTH
import refractivity


def _finish(fig, path):
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=130)
    return fig


def plot_atmosphere(prof, path=None, h_mark_m=None):
    h = prof.h_m / 1000.0
    N = refractivity.N_from_atm(prof.p_hPa, prof.T_K, prof.e_hPa)
    M = refractivity.modified_refractivity(N, prof.h_m)
    fig, ax = plt.subplots(1, 4, figsize=(14, 4.5), sharey=True)
    ax[0].plot(prof.T_K, h); ax[0].set_xlabel("T (K)")
    ax[1].plot(prof.p_hPa, h); ax[1].set_xlabel("p (hPa)")
    ax[2].plot(prof.rho_wv, h); ax[2].set_xlabel("ρ_wv (g/m³)")
    ax[3].plot(N, h, label="N"); ax[3].plot(M, h, "--", label="M"); ax[3].set_xlabel("N, M"); ax[3].legend()
    ax[0].set_ylabel("Độ cao (km)")
    for a in ax:
        a.grid(alpha=.3)
        if h_mark_m is not None:
            a.axhline(h_mark_m / 1000.0, c="r", ls=":", lw=1)
    fig.suptitle(f"Profile khí quyển ({prof.source})")
    return _finish(fig, path)


def plot_gradient(prof, path=None, h_mark_m=None):
    h = prof.h_m / 1000.0
    N = refractivity.N_from_atm(prof.p_hPa, prof.T_K, prof.e_hPa)
    dN = np.gradient(N, h)
    fig, a = plt.subplots(figsize=(5, 4.5))
    a.plot(dN, h)
    a.axvline(-40, ls=":", c="gray", label="-40 N/km (chuẩn)")
    a.axvline(-157, ls=":", c="r", label="-157 N/km (ngưỡng duct)")
    if h_mark_m is not None:
        a.axhline(h_mark_m / 1000.0, c="r", ls=":", lw=1)
    a.set_xlabel("dN/dh (N/km)"); a.set_ylabel("Độ cao (km)"); a.legend(); a.grid(alpha=.3)
    return _finish(fig, path)


def plot_rays(fan, main_ray, geom, path=None):
    """Quỹ đạo tia trên mặt đất cong (trục đứng tính theo mặt phẳng tiếp tuyến tại trạm)."""
    r_surf = A_EARTH + geom.h_g_m
    fig, ax = plt.subplots(figsize=(11, 5.5))
    xy = lambda res: (r_surf * np.sin(res.path_phi) / 1000.0,
                      (res.path_r * np.cos(res.path_phi) - r_surf) / 1000.0)
    allr = fan + ([main_ray] if main_ray is not None else [])
    phis = np.linspace(0, max(r.phi for r in allr) * 1.05, 400)
    ax.fill_between(r_surf * np.sin(phis) / 1000.0, r_surf * (np.cos(phis) - 1) / 1000.0,
                    -20, color="#b8a98a", label="Mặt đất (cong)")
    for res in fan:
        x, y = xy(res); ax.plot(x, y, lw=.8, c="tab:blue", alpha=.6)
    if main_ray is not None:
        x, y = xy(main_ray)
        ax.plot(x, y, c="tab:red", lw=2, label=f"Tia tới UAV (θ₀={np.degrees(main_ray.theta0):.3f}°)")
        ax.plot(x[-1], y[-1], "r*", ms=14, label="UAV")
    ax.plot(0, geom.h_ant_m / 1000, "k^", ms=9, label="Trạm")
    ax.set_xlabel("Khoảng cách ngang (km)"); ax.set_ylabel("Độ cao so với mặt phẳng tiếp tuyến (km)")
    ax.set_ylim(-20, geom.h_u_m / 1000 * 1.1)
    ax.set_title("Quỹ đạo tia"); ax.legend(loc="upper left"); ax.grid(alpha=.3)
    return _finish(fig, path)


def plot_losses(rows, req_margin, path=None, d_mark_km=None):
    d = [r.d_km for r in rows]
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
    ax[0].plot(d, [r.FSPL_dB for r in rows], label="FSPL")
    ax[0].plot(d, [r.A_gas_dB for r in rows], label="A_gas")
    ax[0].plot(d, [r.A_defocus_dB for r in rows], label="A_defocus")
    ax[0].set_xlabel("d (km)"); ax[0].set_ylabel("Tổn hao (dB)"); ax[0].legend(); ax[0].grid(alpha=.3)
    ax[1].plot(d, [r.margin_dB for r in rows], c="tab:green", label="Margin")
    ax[1].axhline(0, c="k", lw=.8); ax[1].axhline(req_margin, c="r", ls="--", label="Margin yêu cầu")
    ax[1].set_xlabel("d (km)"); ax[1].set_ylabel("Margin (dB)"); ax[1].legend(); ax[1].grid(alpha=.3)
    if d_mark_km:
        for a in ax: a.axvline(d_mark_km, c="gray", ls=":")
    return _finish(fig, path)
