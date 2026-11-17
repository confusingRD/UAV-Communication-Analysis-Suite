# Radio Link Solver — cubesat-link 0.2.0

Thư viện Python độc lập và CLI JSON cho tuyến mặt đất–UAV / mặt đất–CubeSat.
Không chứa quy tắc gameplay, shop hay phụ thuộc GUI. NASA Space Apps là một
ứng dụng có thể tích hợp; adapter thuộc nhóm ứng dụng.

Python >=3.10, không có runtime dependency ngoài standard library.
Kiểm tra thực tế trên Python 3.15.2, Windows; chưa kiểm tra toàn bộ ma trận
Python/OS. **Không tuyên bố toàn chương trình ITU compliant.**

## Chạy từ thư mục giải nén

```sh
python -m pip install --no-index --no-deps dist/cubesat_link-0.2.0-py3-none-any.whl
python -m cubesat_link examples/uav.json
python -m cubesat_link examples/cubesat.json
python -m cubesat_link examples/cubesat_ideal.json
python -m cubesat_link examples/pass.json
python -I examples/pass_demo.py
python -I -m unittest discover -s tests -v
```

`cubesat-link examples/uav.json` là entry point tương đương sau khi cài wheel.
CLI đọc một JSON từ file hoặc stdin, xuất một JSON ra stdout. Exit 0 nghĩa là
request hợp lệ, không có nghĩa budget đầy đủ hoặc liên lạc thành công.

- [Tích hợp, schema, lỗi và API ổn định](docs/INTEGRATION.md).
- [Phương trình, phạm vi và mức kiểm chứng](docs/PHYSICS.md).
- [Kết quả xác minh bản phát hành](docs/RELEASE.md).
- [Kiểm kê source cũ](docs/AUDIT.md).
- [UAV](examples/uav.json), [CubeSat](examples/cubesat.json),
  [chân không lý tưởng](examples/cubesat_ideal.json), [pass vào–ra](examples/pass.json).

Ví dụ đều là **synthetic example**. CubeSat dùng profile tham chiếu P.834 và
mật độ electron tổng hợp, không phải dự báo thời tiết/không gian. Chưa có
P.676 generator đã kiểm chứng: gas, mưa, mây và hiệu ứng thiếu dữ liệu trả
`not_computable`, `value: null`; không tự điền 0. Ví dụ chân không khai báo
rõ giả định để minh họa budget hoàn chỉnh. Không suy throughput từ margin.

Bốn lớp: physics, providers có provenance, Python API/CLI/schema, và examples.
Source UAV cũ còn trong repository để tra cứu; ZIP đầy đủ đặt nó trong
`legacy/`. Nó thiếu bốn module và không phải entry point được hỗ trợ.
Không cài dependencies GUI để sử dụng package mới.
