"""service.py - một hàm run(inputs) dùng chung cho CLI (main.py) và GUI (app.py)."""
from dataclasses import dataclass, field, asdict
import warnings
import numpy as np
from config import Inputs, LinkInputs, GeometryInputs, SiteInputs, SolverConfig, A_EARTH
import atmosphere, refractivity, raytrace, losses, linkbudget


def inputs_from_dict(d):
    return Inputs(LinkInputs(**d["link"]), GeometryInputs(**d["geom"]),
                  SiteInputs(**d["site"]), SolverConfig(**d["cfg"]))


def inputs_to_dict(inp):
    return asdict(inp)


@dataclass
class Result:
    prof: object
    med: object
    atm_uav: dict
    ray: object = None
    info: dict = field(default_factory=dict)
    budget: object = None
    rows: list = field(default_factory=list)
    fan: list = field(default_factory=list)
    horizon_km: float = 0.0
    gas_available: bool = False
    notes: list = field(default_factory=list)


def run(inp, n_sweep=30, fan_n=20):
    inp.validate()
    cfg, g, lk = inp.cfg, inp.geom, inp.link
    notes = []
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        prof = atmosphere.build_profile(inp.site.lat_deg, g.h_g_m, g.h_u_m + 500.0,
                                        cfg.dh_m, cfg.atmosphere_source)
        gamma = losses.gamma_gas_table(prof, lk.f_MHz, cfg.atmosphere_source) if cfg.enable_gas else None
        notes += [str(x.message) for x in w]
    if prof.source.startswith("fallback"):
        notes.append("Đang dùng profile dự phòng ISA: KHÔNG phụ thuộc vĩ độ.")
    if cfg.enable_gas and gamma is None:
        notes.append("Không có γ_gas (cần itur): A_gas = 0.")

    med = refractivity.medium_from_profile(prof, gamma)
    res = Result(prof=prof, med=med,
                 atm_uav=refractivity.atmosphere_at(prof, g.h_u_m, lk.f_MHz),
                 horizon_km=losses.radio_horizon_km(g.h_ant_m, g.h_u_m),
                 gas_available=gamma is not None, notes=notes)

    ray, info = raytrace.shoot_to_target(med, g, cfg)
    res.info = info
    r_s = A_EARTH + g.h_g_m
    th_gr = np.degrees(raytrace.grazing_angle(med, r_s + g.h_ant_m, r_s))
    res.fan = raytrace.ray_fan(med, g, cfg, np.linspace(th_gr + 1e-4, 3.0, fan_n))

    if info["beyond_horizon"]:
        notes.append(f"d = {g.d_km:g} km vượt chân trời vô tuyến (tối đa ~{info['d_max_ray_km']:.0f} km): "
                     "v0 không có nhiễu xạ nên không tính link budget cho điểm này.")
        res.ray = None
    else:
        res.ray = ray
        res.budget = linkbudget.compute_budget(inp, med, ray)
    d_grid = np.linspace(5.0, min(info["d_max_ray_km"] * 0.999, 2000.0), n_sweep)
    res.rows = linkbudget.sweep_distance(inp, med, d_grid)
    notes.append("Giới hạn v0: không có phản xạ mặt đất/multipath và nhiễu xạ; "
                 "kết quả có thể lạc quan ở góc ngẩng thấp.")
    return res


def max_range(res, margin_req):
    return linkbudget.max_range_km(res.rows, margin_req)
