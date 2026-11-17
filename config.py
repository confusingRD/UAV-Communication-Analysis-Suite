"""config.py - hằng số và dataclass đầu vào của solver v0.

Đơn vị quy ước toàn bộ project:
  độ cao/khoảng cách trong ODE: mét (m); nhiệt độ: K; áp suất: hPa;
  mật độ hơi nước: g/m^3; tần số: MHz (ở input), GHz (khi gọi itur).
"""
from dataclasses import dataclass, field

C = 299_792_458.0          # m/s
A_EARTH = 6_371_000.0      # m, bán kính Trái Đất (hình cầu)
H_MAX_V0 = 11_000.0        # m, giới hạn v0 (tầng đối lưu)


@dataclass
class LinkInputs:
    f_MHz: float = 2400.0
    P_tx_dBm: float = 30.0          # 1 W
    G_tx_dBi: float = 2.0
    G_rx_dBi: float = 2.0
    L_cable_dB: float = 1.0
    sensitivity_dBm: float = -105.0  # LẤY TỪ DATASHEET đúng module/packet rate
    fade_margin_req_dB: float = 10.0


@dataclass
class GeometryInputs:
    h_g_m: float = 0.0       # độ cao mặt đất tại trạm (so với mực nước biển)
    h_ant_m: float = 10.0    # chiều cao anten trạm so với mặt đất
    h_u_m: float = 11_000.0  # độ cao UAV (so với mực nước biển)
    d_km: float = 300.0      # khoảng cách dọc mặt đất


@dataclass
class SiteInputs:
    lat_deg: float = 10.8    # TP.HCM
    lon_deg: float = 106.7


@dataclass
class SolverConfig:
    dh_m: float = 50.0
    enable_gas: bool = True
    enable_defocus: bool = True
    atmosphere_source: str = "itur"   # "itur" hoặc "fallback"
    rtol: float = 1e-9
    atol_r: float = 1e-6              # m
    s_max_m: float = 3.0e6


@dataclass
class Inputs:
    link: LinkInputs = field(default_factory=LinkInputs)
    geom: GeometryInputs = field(default_factory=GeometryInputs)
    site: SiteInputs = field(default_factory=SiteInputs)
    cfg: SolverConfig = field(default_factory=SolverConfig)

    def validate(self):
        g = self.geom
        if self.link.f_MHz <= 0:
            raise ValueError("f_MHz phải > 0")
        if g.h_u_m > H_MAX_V0:
            raise ValueError(f"v0 chỉ hỗ trợ h_u <= {H_MAX_V0} m (tầng đối lưu)")
        if g.h_g_m + g.h_ant_m >= g.h_u_m:
            raise ValueError("UAV phải cao hơn anten trạm")
        if g.d_km <= 0:
            raise ValueError("d_km phải > 0")
