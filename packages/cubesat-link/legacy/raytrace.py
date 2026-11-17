"""raytrace.py - ray tracing trong khí quyển phân tầng cầu (luật Bouguer) + shooting.

Bất biến: n(r) * r * cos(theta) = const dọc tia.
ODE theo độ dài cung s (theta = góc ngẩng cục bộ so với phương ngang tại vị trí tia):
    dr/ds   = sin(theta)
    dphi/ds = cos(theta) / r
    dtheta/ds = cos(theta) * (1/r + (1/n) dn/dr)
Tích luỹ kèm theo: L (độ dài thật), delay = ∫(n-1)ds, A_gas = ∫γ(h) ds.
"""
from dataclasses import dataclass, field
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
from config import A_EARTH


@dataclass
class RayResult:
    theta0: float                 # rad, góc phóng tại trạm
    theta_arr: float              # rad, góc ngẩng cục bộ tại UAV
    phi: float                    # rad, góc tâm giữa trạm và UAV
    d_surface_m: float            # m, khoảng cách dọc mặt đất (r_surf * phi)
    L_m: float                    # m, độ dài đường truyền thật
    excess_delay_m: float         # m, ∫(n-1)ds
    A_gas_dB: float
    eps_geo: float                # rad, góc ngẩng hình học trạm->UAV
    bend_total: float             # rad, tổng độ uốn tia = θ0 - θ_arr + φ
    reached: bool = True          # có chạm độ cao UAV không (không cắt đất)
    path_r: np.ndarray = field(default=None, repr=False)
    path_phi: np.ndarray = field(default=None, repr=False)


def trace_ray(medium, r0, theta0, r_target, r_surf, cfg, n_path=300):
    """Tích phân một tia từ (r0, phi=0) với góc ngẩng theta0 tới r = r_target."""
    use_gas = medium.gamma is not None

    def rhs(s, y):
        r, phi, th = y[0], y[1], y[2]
        h = r - A_EARTH
        n = medium.n(h)
        dn = medium.dn_dh(h)
        st, ct = np.sin(th), np.cos(th)
        g = medium.gamma(h) / 1000.0 if use_gas else 0.0   # dB/m
        return [st, ct / r, ct * (1.0 / r + dn / n), 1.0, n - 1.0, g]

    def ev_target(s, y):
        return y[0] - r_target
    ev_target.terminal, ev_target.direction = True, +1

    def ev_ground(s, y):
        return y[0] - (r_surf - 0.5)
    ev_ground.terminal, ev_ground.direction = True, -1

    atol = [cfg.atol_r, 1e-13, 1e-13, 1e-3, 1e-6, 1e-9]
    sol = solve_ivp(rhs, (0.0, cfg.s_max_m), [r0, 0.0, theta0, 0.0, 0.0, 0.0],
                    method="DOP853", rtol=cfg.rtol, atol=atol,
                    events=[ev_target, ev_ground], dense_output=True)
    hit_target = len(sol.t_events[0]) > 0
    if not hit_target:
        return None
    s_end = sol.t_events[0][0]
    y = sol.sol(s_end)
    r, phi, th, L, dly, A = y
    ss = np.linspace(0.0, s_end, n_path)
    P = sol.sol(ss)
    eps_geo = np.arctan2(r * np.cos(phi) - r0, r * np.sin(phi))
    return RayResult(
        theta0=theta0, theta_arr=th, phi=phi, d_surface_m=r_surf * phi,
        L_m=L, excess_delay_m=dly, A_gas_dB=A, eps_geo=eps_geo,
        bend_total=theta0 - th + phi, path_r=P[0], path_phi=P[1])


def grazing_angle(medium, r0, r_surf):
    """Góc phóng nhỏ nhất (âm) để tia vừa tiếp xúc mặt đất (Bouguer)."""
    ns = medium.n(r_surf - A_EARTH)
    n0 = medium.n(r0 - A_EARTH)
    c = ns * r_surf / (n0 * r0)
    return -np.arccos(min(1.0, c))


def shoot_to_target(medium, geom, cfg, d_target_m=None):
    """Tìm tia từ trạm tới UAV ở khoảng cách mặt đất d. Trả (RayResult, info dict)."""
    r_surf = A_EARTH + geom.h_g_m
    r0 = r_surf + geom.h_ant_m
    r_u = A_EARTH + geom.h_u_m
    d_t = geom.d_km * 1000.0 if d_target_m is None else d_target_m

    th_min = grazing_angle(medium, r0, r_surf) + 1e-7
    th_max = np.deg2rad(89.9)

    def dist(th):
        res = trace_ray(medium, r0, th, r_u, r_surf, cfg, n_path=2)
        return np.nan if res is None else res.d_surface_m

    d_far = dist(th_min)
    info = {"d_max_ray_km": d_far / 1000.0, "beyond_horizon": False}
    if np.isnan(d_far) or d_t > d_far:
        info["beyond_horizon"] = True
        res = trace_ray(medium, r0, th_min, r_u, r_surf, cfg)
        return res, info

    d_near = dist(th_max)
    if d_t < d_near:
        info["too_close"] = True
        return trace_ray(medium, r0, th_max, r_u, r_surf, cfg), info

    th = brentq(lambda t: dist(t) - d_t, th_min, th_max, xtol=1e-11, rtol=1e-12)
    return trace_ray(medium, r0, th, r_u, r_surf, cfg), info


def ray_fan(medium, geom, cfg, angles_deg):
    """Nhiều tia (để vẽ) từ trạm tới độ cao UAV. Bỏ qua tia cắt đất."""
    r_surf = A_EARTH + geom.h_g_m
    r0 = r_surf + geom.h_ant_m
    r_u = A_EARTH + geom.h_u_m
    out = []
    for a in angles_deg:
        res = trace_ray(medium, r0, np.deg2rad(a), r_u, r_surf, cfg, n_path=200)
        if res is not None:
            out.append(res)
    return out
