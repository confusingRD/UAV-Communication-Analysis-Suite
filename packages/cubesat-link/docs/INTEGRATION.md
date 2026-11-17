# Tích hợp Radio Link Solver 0.2.0 — JSON schema 1.0

Python API và CLI gọi cùng orchestration; adapter ứng dụng nằm ngoài thư viện.
Không import source game, shop, Streamlit, NumPy hoặc SciPy.

## Cài và gọi

Từ thư mục giải nén, với Python có pip:

```sh
python -m pip install --no-index --no-deps dist/cubesat_link-0.2.0-py3-none-any.whl
python -m cubesat_link examples/cubesat.json
cubesat-link examples/uav.json
python -I examples/pass_demo.py
python -I -m unittest discover -s tests -v
```

PowerShell stdin: `Get-Content -Raw examples/cubesat.json | python -m cubesat_link -`.
POSIX: `python -m cubesat_link < examples/cubesat.json`.
Một request/process, một response JSON trên stdout. UTF-8; nhận BOM đầu file.
Không nhận NaN/Infinity, key lặp, key không biết hoặc boolean thay số.

Schema máy đọc: [request](../schemas/request.schema.json),
[response](../schemas/response.schema.json); bản giống hệt được đóng trong wheel.
Draft 2020-12 mô tả cấu trúc. API kiểm tra thêm UTC, miền vật lý, coverage,
mảng cùng chiều/tăng đơn điệu và trùng loss. Runtime validator chỉ hỗ trợ
những keyword có trong schema này, không phải validator tổng quát.

## API ổn định dòng 0.2.x

Import từ `cubesat_link`. Giữ tên, đơn vị, ý nghĩa trong 0.2.x; thay đổi phá vỡ
hợp đồng cần minor release mới và JSON breaking change cần schema version mới.
Các hàm bắt đầu `_` và source prototype ở gốc không thuộc hợp đồng.

```python
run_request(request: dict) -> dict
load_request(text: str) -> dict
evaluate_link(station, state, frequency_hz, *, earth=WGS84, radio=None,
              neutral_profile=None, electrons=None, polarization=None,
              supplied_losses=None, vacuum=False, neutral_provider=None,
              electron_provider=None) -> LinkResult
geometry(station, state, earth=WGS84) -> Geometry
station_ecef(station, earth=WGS84) -> tuple
contact_windows(station, states, earth=WGS84, *, max_gap_s=60,
                mode="geometric") -> list[ContactWindow]
trace_spherical(station, state, frequency_hz, profile, earth=WGS84) -> NeutralRay
fspl_db(distance_m, frequency_hz) -> float
integrate_electrons(profile, satellite_path_length_m) -> SlantTEC
ionospheric_effects(frequency_hz, tec) -> dict[str, Effect]
polarization_loss(polarization, faraday_rad) -> Effect
compute_budget(losses, radio, *, path_available) -> Budget
```

Kiểu công khai: Earth, WGS84, SPHERE, GroundStation, SatelliteState (dùng được
cho UAV), Radio, Polarization, Effect, NeutralProfile, ElectronPath, SlantTEC,
Geometry, ContactWindow, NeutralRay, Budget, LinkResult, InputError.
Provider: ProviderMetadata, ProviderResult, NeutralProvider, ElectronProvider,
NeutralTableProvider, P834ReferenceProvider, P676GasProvider, PathBinding,
BoundElectronProvider. `p834_reference_profile()` tạo bảng tham chiếu cấp thấp.

Python cấp thấp gây ValueError cho input sai. `run_request` chuẩn hóa thành
InputError có code/path. Thiếu dữ liệu hợp lệ trả not_computable, không phải
exception. `LinkResult.to_dict()` trả dict JSON-safe.

## Schema input và đơn vị

| Trường | Ý nghĩa |
|---|---|
| schema_version | Bắt buộc "1.0" |
| operation | evaluate_link hoặc contact_windows |
| earth | Bắt buộc {"model":"WGS84"} hoặc {"model":"sphere","radius_m":6371000} |
| station | lat_deg, lon_deg, altitude_m; min_elevation_deg mặc định 0 |
| state | position_m gồm 3 số mét ECEF, frame="ECEF", epoch_utc có Z/+00:00 |
| frequency_hz | Số Hz dương; không MHz/GHz, không clamp |
| states | Mảng state cho cửa sổ, UTC tăng nghiêm ngặt, gap mặc định <=60 s |
| vacuum | Mặc định false; true là giả định lý tưởng tường minh, không kết hợp profile |
| radio | TX dBm, gain dBi, pointing/cable dB, threshold dBm, mode và antenna_basis |
| polarization | linear/circular; alignment rad hoặc circular_match trong cùng basis truyền sóng |

WGS-84 dùng latitude geodetic, phase-centre height trên ellipsoid, không phải MSL.
Sphere dùng latitude/height trên mặt cầu đã chọn. Không đổi ngầm ECEF WGS-84
sang sphere; không có ECI/TEME/EOP converter. Azimuth Bắc qua Đông [0,360),
zenith/nadir null. Mask [0,90]. UTC không hỗ trợ leap-second :60.

Mặc định Python geometry/evaluate/trace đều WGS-84. Trace cầu với WGS-84 trả
not_computable; phải truyền SPHERE hoặc Earth(radius,0), xây endpoint đúng cùng
mô hình. JSON luôn bắt khai báo Earth.

## Providers

`neutral.kind` là p834_reference hoặc table. Table cần profile và metadata.
Profile có height_m, refractive_index (không đơn vị), frequency_range_hz, source;
gas tùy chọn có gamma_db_per_km, gas_frequency_hz và gas_source.
`outside="unavailable"`: bảng hữu hạn UAV, vượt top chưa tính được.
`outside="vacuum_above_top"`: giả định chủ động, bắt n(top)=1 và gamma(top)=0
nếu có gas. Không tự sửa profile hay kéo bảng 11 km lên vệ tinh.

Metadata bắt buộc source, version, epoch_utc, applicability, units, temporal_kind.
Observation đòi epoch bằng state; reference dùng epoch bản tham chiếu; synthetic
là epoch kịch bản. Phạm vi địa lý là khai báo của nhà cung cấp, không tự kiểm
chứng bằng dữ liệu ngoài. Profile trung hòa đồng nhất theo phương ngang.

`electrons.kind="path"`: Ne(s) và tùy chọn B_parallel(s), units m, el/m3, T.
`kind="tec"`: STEC hữu hạn và tùy chọn integral Ne*B ds, units m, el/m2, T el/m2.
Binding chứa station, state, earth, path_kind, path_length_m phải khớp tuyến;
tolerance chiều dài max(1 mm, 1e-9*L). Có thể chạy neutral trước để lấy L,
rồi cấp dữ liệu electron. Sai binding/thiếu coverage trả not_computable.
Binding xác minh khai báo; thư viện chưa xuất tọa độ mẫu ray để tự lấy IRI.
Bên gọi phải bảo đảm mẫu nằm trên chính ray đó; không dùng VTEC thay STEC.

Raw NeutralProfile/ElectronPath/SlantTEC vẫn được Python core nhận để giữ API
nghiên cứu độc lập. Chúng không phải provider đã kiểm tra metadata/binding;
bên gọi chịu trách nhiệm provenance và vị trí mẫu. Dùng provider hoặc
run_request cho tích hợp có kiểm tra provenance.

## Output và chống cộng trùng

Envelope: schema_version, release, ok=true, operation, result.
Link result: geometry, neutral_ray, refracted_visible, path_available,
path_basis, losses_db, ionosphere, neutral_excess_delay_s, budget, providers.
Window result: windows, mode=geometric, earth. Mỗi cửa sổ có UTC start/end,
start_clipped/end_clipped và method. Không ngoại suy ngoài khoảng mẫu.

Effect gồm value, unit, status, reason. Computed là tính có điều kiện theo
input; assumed là giả định tường minh; not_computable có value=null và lý do.
Không dùng `value or 0`. path_available=null là chưa xác định; false là không
qua điều kiện chế độ hiện tại; true không bảo đảm đủ công suất/nhận được gói.

neutral_ray.refractivity_excess_m = integral(n-1)ds;
geometric_excess_m = L_ray-L_chord; total_excess_m là tổng hai phần.
neutral_excess_delay_s = total_excess_m/c. Trường cũ excess_path_m vẫn chỉ
integral(n-1)ds để tương thích, không phải trễ tổng so với dây cung.

Ledger có free_space, gas, rain, cloud, neutral_scintillation,
ionospheric_scintillation, ionospheric_absorption, beam_spreading, polarization.
Supplied_losses chỉ điền component chưa có, không thay free_space hoặc mục
computed/assumed. Không nhận total_atmosphere hay tổng percentile P.618.
Delay/phase/Faraday không trực tiếp là loss dB. Hardware trừ riêng một lần;
budget.radio_assumptions giữ mode/basis, kể cả budget chưa đầy đủ.
Nếu gain đã theo hướng ray, đặt pointing loss=0 và ghi rõ antenna_basis.

| Code | Exit | Ý nghĩa |
|---|---:|---|
| INVALID_JSON | 2 | JSON sai cú pháp/key lặp/NaN/Infinity |
| SCHEMA_ERROR | 2 | Thiếu/sai kiểu/unknown field/range cấu trúc |
| UNSUPPORTED_SCHEMA | 2 | Không hỗ trợ version yêu cầu |
| INVALID_INPUT | 2 | Sai miền vật lý/UTC/mảng/trùng component |
| IO_ERROR | 2 | Không đọc được file/encoding |
| INTERNAL_ERROR | 3 | Lỗi solver ngoài dự kiến |

Lỗi: `{"schema_version":"1.0","release":"0.2.0","ok":false,"error":
{"code":"INVALID_JSON","message":"...","path":"$"}}`.
Message không là hợp đồng ổn định; tích hợp theo code/status.
Exit 0 nghĩa request hợp lệ, không nghĩa mô hình đã tính được tất cả hiệu ứng.

## Input/output mẫu

Input tối thiểu để minh họa geometry/FSPL trong chân không:

```json
{"schema_version":"1.0","operation":"evaluate_link",
 "earth":{"model":"sphere","radius_m":6371000},
 "station":{"lat_deg":0,"lon_deg":0,"altitude_m":0},
 "state":{"position_m":[6871000,0,0],"frame":"ECEF","epoch_utc":"2026-11-14T00:00:00Z"},
 "frequency_hz":2400000000,"vacuum":true}
```

Các trường chọn từ output (đã lược bớt reason và envelope):

```json
{"path_available":true,
 "geometry":{"slant_range_m":500000.0,"elevation_deg":90.0},
 "losses_db":{"free_space":{"value":154.03140814283586,"unit":"dB","status":"computed"}},
 "budget":{"margin_db":{"value":null,"unit":"dB","status":"not_computable"}}}
```

Input nhỏ này thiếu radio nên margin chưa biết. Input/output đầy đủ trong
[examples](../examples/), các file *.output.json được sinh từ bản kiểm tra.
Cubesat_ideal có radio tổng hợp cho P_rx=-112.031408 dBm, margin=7.968592 dB;
throughput vẫn chưa tính. Pass mẫu false → true → false; cửa sổ hình học khoảng
00:06:03.123Z–00:13:56.877Z ngày 2026-11-14, không suy nửa vòng quỹ đạo.
