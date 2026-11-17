# Vật lý, dữ liệu và kiểm chứng — 0.2.0

Đây là công cụ có phạm vi giới hạn, không tuyên bố toàn chương trình ITU compliant.
Computed nghĩa đã tính theo giả định/input đã khai báo, không đồng nghĩa đã
đối chiếu đo thực địa. [Báo cáo release](RELEASE.md) ghi kiểm tra thực sự đã chạy.

## Bốn lớp và nguồn dữ liệu

1. Core: geometry, neutral ray, plasma effects, ledger link budget.
2. Providers: bảng trung hòa, tham chiếu P.834, Ne/TEC/B có metadata/binding.
3. Public interfaces: Python API, CLI JSON/schema; không kéo GUI dependencies.
4. Examples: UAV/CubeSat synthetic. Adapter shop/game nằm ngoài repository này.

Provider ghi source, version, UTC epoch, applicability, units, temporal_kind.
Observation chỉ dùng đúng epoch; reference/synthetic không giả là quan trắc.
Bảng trung hòa đồng nhất theo phương ngang; phạm vi địa lý do nhà cung cấp
khai báo. Binding electron đối chiếu endpoint, Earth, epoch, nhánh và chiều dài;
không chứng minh mẫu đã được đo ở tọa độ đó. Raw core tables vẫn được hỗ trợ
cho nghiên cứu; không có kiểm tra metadata đầy đủ như provider.

## Hình học và cửa sổ

WGS-84: a=6378137 m, f=1/298.257223563. Geodetic lat/lon → ECEF, sau đó
quay ENU để tính azimuth/elevation. Height là phase centre trên ellipsoid.
SPHERE có R=6371000 m; custom sphere dùng đúng R do người gọi truyền.
Mặc định tất cả entry point hình học/evaluate/trace là WGS-84; tracer cầu
trả not_computable với ellipsoid, không đổi tọa độ hay bán kính âm thầm.

Earth occultation: cực tiểu bình phương bán kính chuẩn hóa của segment trên
ellipsoid; tiếp tuyến coi clear với tolerance 1e-12 (~3 micrometres trên bề mặt).
Không có terrain/building/Fresnel clearance. Geometric visibility giữ riêng
occultation và mask. Station altitude>=0, mask 0–90 độ. Antenna cao có thể có
đường thẳng không cắt đất nhưng elevation âm; API mask không âm vẫn loại nó.

contact_windows chỉ có mode geometric; từ chối mode refracted. Nội suy tuyến
tính ECEF giữa mẫu UTC và giải giao cone-mask, kể cả pass nằm giữa hai mẫu
ngoài cone. Không extrapolate, không dự đoán orbit, không giả nửa vòng quỹ đạo.
Clipped đánh dấu biên do thiếu mẫu. Gap<=60 s chỉ là guard, không đảm bảo độ
chính xác orbit. Tia khúc xạ có thể usable ngoài chân trời hình học, nhưng
không được dùng để diễn giải các cửa sổ hình học này.

Ví dụ pass: circular equatorial synthetic, radius=6871000 m, mu=3.986004418e14
m3/s2, tốc độ quay Trái Đất=7.292115e-5 rad/s, omega=sqrt(mu/r^3)-omega_E.
Không drag/J2/EOP. Mask10 độ có half-angle alpha=acos(R*cos(mask)/r)-mask.
Thời điểm giải tích là t_peak ± alpha/omega, t_peak=600 s.
Test bước60,30,10,5 s: biên cuối sai <0.02 s và cải thiện >20 lần so với60 s.
Đây là kiểm tra hội tụ quỹ đạo mẫu, không phải bound cho mọi quỹ đạo.

## Khúc xạ trung hòa và trễ

Bouguer invariant b=n(r)*r*cos(elevation), dựa trên P.834-9 Annex1 (6)–(8).
Solver tích phân theo r với biến t=sqrt(r-r_station), Simpson thích nghi,
shooting52 vòng bisection, residual endpoint<=1e-8 rad. Chỉ nhánh đi lên,
n*r tăng nghiêm ngặt; từ chối duct/turning/endpoint ngoài nhánh. Chưa có ray
ellipsoid, nhánh đi xuống, nhiều đường hay gradient ngang. Failure không
chứng minh mọi đường truyền vật lý đều không tồn tại.

Đặt L_ray=integral ds, D=norm(endpoint-station), Q=integral(n-1)ds:

- refractivity_excess_m = Q.
- geometric_excess_m = L_ray-D (roundoff âm <=1 mm được đưa về0).
- total_excess_m = (L_ray-D)+Q.
- neutral_excess_delay_s = total_excess_m/c, c=299792458 m/s chính xác SI.

Trễ này so với **đường thẳng chân không giữa cùng hai endpoint**. Trước0.2.0,
API chỉ trả Q/c nên thiếu geometric excess; ca central-angle20 độ, R6371 km,
h_sat500 km có geometric excess khoảng0.850092 m. Trường excess_path_m cũ
vẫn giữ nghĩa Q để tránh đổi đơn vị/nghĩa; dùng tên mới cho tổng trễ.
Neutral coi nondispersive; không cộng delay vào ledger dB.

NeutralProfile piecewise linear theo height. UAV dùng outside=unavailable,
profile không cần n(top)=1 nhưng endpoint phải nằm trong miền. CubeSat có thể
dùng outside=vacuum_above_top khi đã khai báo truncation và n(top)=1,
gamma(top)=0 nếu có gas. Không kéo bảng UAV11 km lên orbit.
P.834 reference: n=1+0.000315*exp(-0.1361*h_km), grid250 m tới100 km,
điểm cuối đặt1, bỏ N~0.000387. Đó là approximation/truncation tường minh;
không phải thời tiết theo tọa độ, chưa có bound sai số mọi ray.

## Suy hao và radio

FSPL theo P.525-5 (5): 20log10(4*pi*D*f/c), D mét, f Hz.
D là endpoint chord; Jacobian/focusing do tia cong thuộc beam_spreading riêng,
chưa tính. Bên gọi kiểm tra điều kiện far-field của anten.
Gaseous loss khi có bảng gamma đúng f: integral gamma(h)*ds/1000 dB với ds m.
Nội suy height, không nội suy/clamp frequency. Gamma là dữ liệu bên ngoài;
ví dụ UAV dùng gamma synthetic và không gọi là P.676.

P676GasProvider hiện là capability báo unavailable, không phải implementation
phổ khí. Pin mục tiêu P.676-13 Annex1 (2022), scope1–1000 GHz; Annex2 là xấp xỉ
1–350 GHz với điều kiện riêng. Thiếu: catalogue vạch O2/H2O được kiểm tra,
line shapes/continuum, profile pressure/temperature/water vapour, và reference
cases độc lập. Tại2.4 GHz vẫn not_computable; 868/915 MHz ngoài scope Annex1,
không kẹp lên1 GHz. Không tự đặt gas0.

P_rx = P_tx+G_tx+G_rx - L_point_tx-L_point_rx-L_cable - sum(named losses).
Margin = P_rx - receiver threshold đúng mode. Budget chỉ tính nếu path usable,
radio và toàn bộ component đủ. Required margin là input; không tự suy policy.
Gain theo hướng ray phải khai báo pointing0 và basis để không trừ hai lần.
Không có throughput/BER/packet model. Nếu bổ sung cần modulation/coding,
bandwidth/noise/rate/overhead và mục tiêu BER; không suy từ margin.

Giữ riêng free_space, gas, rain, cloud, neutral_scintillation,
ionospheric_scintillation, ionospheric_absorption, beam_spreading, polarization.
Chặn component trùng/composite. P.618-14 (2023) là framework earth-space và
phương pháp thống kê; không cộng độc lập các percentile vào ledger tức thời.
Chưa triển khai rain P.838/P.837/P.618, cloud P.840 hoặc scintillation P.618.
Có thể cấp từng loss từ model ngoài với provenance trong reason, hoặc giả
định thiết kế tường minh status=assumed; thư viện không tự chứng nhận model đó.

## Electron, TEC, phase và Faraday

Ne(s) dọc đúng ray từ station tới endpoint, s là arc length mét. Tích phân
piecewise-linear, cắt tại satellite, không thêm tail tới vô hạn. Nếu có B(s),
tích phân tích Ne*B bậc hai chính xác trong mỗi interval. Không VTEC mapping.
1 TECU=1e16 el/m2. Không có dữ liệu B thì Faraday chưa tính.

First-order cold plasma, package scope0.1–12 GHz, phải f lớn hơn nhiều plasma
và gyro frequencies; không collision/higher-order/strong storm correction:

- group range = +40.3*STEC/f^2 m; delay = range/c s.
- phase path = -group range; phase advance = +2*pi*range*f/c rad,
  convention exp(i*(omega*t-k*s)).
- Faraday = 2.36e4*integral(Ne*B_parallel ds)/f^2 rad, B tesla.

B_parallel có dấu theo hướng truyền; provider phải khai đúng convention.
Ne, delay, phase, Faraday không phải suy hao công suất. Scintillation,
absorption, ray deflection chưa triển khai; scalar TEC không đủ cho chúng.
Polarization lý tưởng: linear loss=-20log10|cos(alignment+Faraday)|;
linear/circular=3.0103 dB; circular matched thuần Faraday=0. Null lý tưởng trả
not_computable (không tạo số loss hữu hạn giả); chưa mô hình axial ratio.

Pin hệ số Faraday/P.531 comparison theo P.531-15 (2023), không gọi là đã
kiểm chứng bản16. Catalogue ITU có P.531-16 (09/2025), đã xác nhận từ trang
được chia sẻ trong phiên này. IRI adapter/IGRF chưa triển khai. Nếu tích hợp
IRI, lưu phiên bản, epoch, tọa độ sampling, indices và phạm vi độ cao thực;
IRI background/monthly climatology không phải dự báo thời tiết không gian
thời gian thực hay mô hình irregularity/scintillation.

## Kiểm chứng đã có và mức bằng chứng

| Thành phần | Bằng chứng | Giới hạn |
|---|---|---|
| Geometry | Zenith, cực WGS-84, ENU, tangent, antipode, elevated station | Hình học smooth Earth |
| Windows | Cone crossing giữa mẫu, clipping/gap; orbit giải tích và hội tụ thời gian | Chỉ geometric |
| Ray/delay | Cartesian Fermat RK4 độc lập, d(n*u)/ds=grad(n), ds10→5 m | Cùng input medium, khác formulation/integrator; chưa đo thực |
| RK4 comparison | 500 km ray, launch10 độ: path<5 mm, Q<1 mm, delay<6 mm/c | Test regression số, không conformance suite |
| Neutral zenith | Profile3 điểm: Q=2.5 m, gas=0.2 dB; vacuum tail | Tích phân giải tích |
| P.834 | R6370 km, central20 độ: bending0.3215524 độ; Eq9~0.3310832 độ | Khác~0.00953 độ, grid250→125 m <0.0001 độ |
| FSPL | P.525(6) MHz/km cho500 km/2.4 GHz:153.9836249 dB | Exact SI154.0314081 dB; chênh0.0477832 dB do32.4 làm tròn |
| Plasma | 10 TECU/1 GHz: delay13.442633 ns; P.531 rounded13.45 ns | Công thức công bố, không measurement |
| Faraday | 10 TECU, B50 microtesla,1 GHz →0.118 rad | Không IGRF/IRI run |
| Public API | CLI/API equality, schema, unknowns, invalid inputs, duplicate ledger | Release report ghi số tests thực chạy |

Các test tự dùng lại công thức không đủ validation; ở đây phân biệt analytic
limits, numerical convergence, đối chiếu approximation công bố, và Cartesian
ODE độc lập. Chưa có dữ liệu đo, independent production ray tracer, P.676
spectral reference suite, P.618 maps hoặc IRI official run.

## Nguồn được pin

- [ITU-R P.525-5 (2024)](https://www.itu.int/dms_pubrec/itu-r/rec/p/R-REC-P.525-5-202411-I!!PDF-E.pdf), (5),(6).
- [ITU-R P.834-9 (2017)](https://www.itu.int/dms_pubrec/itu-r/rec/p/R-REC-P.834-9-201712-I!!PDF-E.pdf), Annex1 (6)–(9); Eq9 chỉ tham chiếu h0–3 km, góc thấp tới10 độ.
- [ITU-R P.676-13 (2022)](https://www.itu.int/dms_pubrec/itu-r/rec/p/R-REC-P.676-13-202208-I!!PDF-E.pdf), Scope/Annex1/2; implementation chưa có.
- [ITU-R P.618-14 (2023)](https://www.itu.int/dms_pubrec/itu-r/rec/p/R-REC-P.618-14-202308-I!!PDF-E.pdf), framework/combination; chưa triển khai.
- [ITU-R P.531-15 (2023)](https://www.itu.int/dms_pubrec/itu-r/rec/p/R-REC-P.531-15-202308-S!!PDF-E.pdf), (2), (4).
- [Catalogue P.531](https://www.itu.int/rec/R-REC-P.531/en), bản16 hiện có; chưa đối chiếu toàn bộ.
- [ESA Navipedia: Ionospheric Delay](https://gssc.esa.int/navipedia/index.php/Ionospheric_Delay), first-order plasma/40.3/sign.
- [NASA CCMC IRI2020](https://ccmc.gsfc.nasa.gov/models/IRI~2020/), background model; chưa có adapter.

## Phạm vi còn thiếu

P.676 generator/weather providers; rain/cloud/scintillation; statistical P.618;
beam spreading/Jacobian; terrain/diffraction/multipath/Fresnel; ECI/TEME/EOP;
ellipsoid/descending/duct rays; refracted/budget windows; ray coordinate export;
IRI/IGRF; ionospheric absorption/bending/scintillation; Doppler; modem/throughput.
