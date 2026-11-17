# Báo cáo release 0.2.0 — 2026-11-14

## Kết quả đã xác minh

- Source: 38/38 unittest đạt, gồm hai hồi quy ở phần C.
- Wheel cài offline vào virtualenv sạch, include-system-site-packages=false:
  38/38 unittest đạt với Python -I, không lỗi/skip được báo trong suite.
- Python thực chạy: 3.15.2, Windows x64. Chưa kiểm tra ma trận Python>=3.10/OS.
- Import được xác nhận từ .release-check/Lib/site-packages/cubesat_link.
- So sánh byte từng file Python/schema trong wheel với source: khớp.
- Không runtime dependency; pip check đạt.
- Bốn request uav/cubesat/cubesat_ideal/pass: API=CLI, schema output đạt.
- Năm ví dụ Python uav, cubesat, pass_demo, overhead, validation chạy đạt.
- Console cubesat-link.exe và stdin chạy đạt; input lỗi/NaN/key lặp/UTC,
  missing data, trùng loss, Earth consistency được suite kiểm tra.

Bằng chứng máy đọc: [verification.json](verification.json).
Full output tham chiếu: [examples](../examples/), các file *.output.json.
Đây là kiểm tra phần mềm, analytic limits/convergence và numerical comparison;
không phải xác nhận bằng đo thực địa hay chứng nhận ITU cho toàn bộ chương trình.

## Artifacts

- dist/cubesat_link-0.2.0-py3-none-any.whl
- dist/cubesat-link-0.2.0-source.zip: source package, tests, docs, examples,
  schemas, pyproject.toml, scripts tái kiểm tra/đóng gói, wheel và legacy snapshot.
- dist/cubesat-link-0.2.0-integration.zip: wheel, docs, README, schemas, examples
  và tests để bên tích hợp chạy kiểm tra mà không cần source/GUI.
- dist/SHA256SUMS.txt: checksum của wheel và cả hai ZIP.

Mỗi ZIP có MANIFEST.sha256 cho mọi payload file. Packaging dùng allowlist,
không đưa .venv, .release-check, __pycache__, build, egg-info, log hoặc ZIP cũ
vào bản bàn giao. Source prototype được đặt trong legacy/ ở full ZIP;
không thay đổi các file gốc trong repository. Không chứa source game.

Wheel SHA256:
`4d1c4e57caf795e5981783105f756b768d7fb8b13ca14a45d348da47638062fb`.
Script verify_handoff kiểm tra CRC, manifest, đường dẫn an toàn, exclusions,
then chạy lại tests và CLI từ bản giải nén bằng wheel đã cài.
Kết quả hậu kiểm ZIP nằm cạnh artifacts: dist/handoff-verification.json.

## Lệnh người nhận chạy (từ thư mục giải nén)

```sh
python -m venv .verify
```

Windows PowerShell:

```powershell
.\.verify\Scripts\python.exe -m pip install --no-index --no-deps dist/cubesat_link-0.2.0-py3-none-any.whl
.\.verify\Scripts\python.exe -I -m cubesat_link examples/cubesat.json
.\.verify\Scripts\python.exe -I -m cubesat_link examples/uav.json
.\.verify\Scripts\python.exe -I examples/pass_demo.py
.\.verify\Scripts\python.exe -I -m unittest discover -s tests -v
```

POSIX: thay .\.verify\Scripts\python.exe bằng .verify/bin/python.
Các lệnh này chỉ cần Python/pip và wheel, không cần mạng hoặc compiler.

## Dành cho maintainer (full source ZIP)

Build backend dùng khi tạo release: setuptools84.2.1; không có native extension.
Source nguyên bản trong package được giữ tên cubesat_link để tương thích.

```sh
python scripts/build_schemas.py
python -m unittest discover -s tests -v
python -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist
python -m venv .release-check
```

Lệnh pip wheel yêu cầu build backend setuptools>=68 có sẵn; có thể bỏ
--no-build-isolation nếu muốn pip chuẩn bị backend (có thể cần mạng).
Với Python của .release-check, lần lượt:

```sh
python -m pip install --no-index --no-deps dist/cubesat_link-0.2.0-py3-none-any.whl
python -I scripts/verify_release.py
python -I scripts/package_release.py
python -I scripts/verify_handoff.py
```

verify_release từ chối import source thay vì installed wheel; ghi lại evidence
và example outputs. package_release dùng allowlist và xác minh CRC/manifest.
Không hứa ZIP/wheel byte-identical giữa build khác nhau vì timestamp ZIP/backend.

## Giới hạn còn lại và ba ưu tiên

Chỉ cửa sổ geometric. Ray cầu đi lên trong môi trường phân tầng đơn điệu;
chưa terrain/ellipsoid/duct/descending, chưa weather/IRI/IGRF adapters,
P.676 generator, rain/cloud/scintillation/beam spreading, Doppler hoặc modem.
Missing data vẫn not_computable. Raw Python tables do người gọi chịu trách
nhiệm provenance; provider/JSON kiểm tra metadata và binding rõ ràng.

1. P.676-13 line-by-line + weather profile provider và reference suite độc lập.
2. Xuất tọa độ ray, IRI/IGRF providers có provenance/coverage; phân biệt rõ
   climatology với dữ liệu không gian thực thời.
3. Cửa sổ refracted/budget dùng cùng predicate từng thời điểm, mở rộng ray
   families và kiểm tra đối chiếu độc lập; sau đó mới bổ sung modem/throughput.
