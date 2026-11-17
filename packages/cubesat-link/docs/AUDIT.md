# Kiểm kê và quyết định — release 0.2.0

Đã đọc toàn bộ source, tests và tài liệu repository trước khi sửa ở phần A.
Source build/lib được xác nhận trùng hash với package cũ; không coi bytecode
là source. Không tìm hoặc sửa source game. Không có AGENTS.md trong project
được kiểm tra. Không có Git CLI khả dụng trong môi trường kiểm tra ban đầu;
release không gắn commit giả.

## Source cũ

Prototype ở gốc: config.py, raytrace.py, service.py, main.py, app.py, plots.py,
run_gui.bat/run_gui.sh và requirements.txt. service.py import atmosphere,
refractivity, losses, linkbudget nhưng bốn module không có trong repository.
Test được README cũ nhắc đến, test_core.py, cũng không có. GUI cũ không được
khôi phục trong release này; các nhãn P.835/P.453/P.676 trong GUI không chứng
minh các implementation đó tồn tại. Không cài dependency GUI để dùng package.

Các bản api.py/budget.py/geometry.py/neutral.py/ionosphere.py ở gốc là snapshot
trùng module cũ, dùng relative imports không tạo thành package độc lập. Bản
được hỗ trợ nằm trong cubesat_link/. Không import module gốc để tích hợp.
Full ZIP đặt các source gốc dưới legacy/ và giữ nguyên nội dung. Không đưa
legacy vào wheel. Bản integration ZIP không chứa legacy.

Cơ sở ODE Bouguer của raytrace.py được giữ về mặt vật lý trong core đã tách.
Không áp dụng giới hạn h_u<=11 km của config cũ lên CubeSat. Những giả định
cũ như thiếu gamma=>0, k=4/3, ray không tới đích vẫn có kết quả, clamp868/915 MHz
không thuộc hợp đồng package mới.

## Thay đổi 0.2.0

- Mặc định Earth nhất quán WGS-84; tracing cầu phải chọn cầu tường minh.
- Trễ trung hòa so với dây cung chân không gồm geometric excess và Q=integral(n-1)ds.
- Cửa sổ được gắn mode geometric; hội tụ mẫu orbit có test giải tích độc lập.
- Bảng UAV bounded không kéo lên orbit. Metadata/provider và finite-path binding
  tách khỏi physics. Missing data trả not_computable.
- P.676 capability báo thiếu implementation cụ thể, không gán zero/clamp.
- CLI JSON, schemas, lỗi, examples và stable API 0.2.x.
- Giữ receiver mode/antenna basis trong output dù budget chưa tính được.
- Raw electrons khi chưa có usable ray trả unknown thay vì tích phân trên
  đường chưa xác định. Không đổi phương trình physics đã kiểm chứng.

Các lần bị giới hạn/quyền terminal trước đó không được tính là verification.
[Báo cáo release](RELEASE.md) ghi kiểm tra sau cùng, wheel và quy trình ZIP.
