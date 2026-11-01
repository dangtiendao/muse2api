# Module Quản Lý Cấu Hình (`config.py`)

---

## 1. Tổng Quan Module

- **File nguồn**: [config.py](file:///e:/Project/muse2api/config.py)
- **Vai trò**: Điểm quản lý tập trung toàn bộ cấu hình runtime của dự án, tự động nạp file `.env`, tự động dò tìm đường dẫn nhị phân của trình duyệt Chromium trên đa nền tảng và cung cấp các đường dẫn thư mục chuẩn hóa.

---

## 2. Các Thành Phần Xử Lý

### 2.1. Hàm `_load_dotenv()`
- Tìm file `.env` tại thư mục gốc dự án (hoặc thư mục chỉ định qua `MUSE2API_HOME`).
- Phân tích cú pháp từng dòng dạng `KEY=VALUE`, bỏ qua các dòng chú thích `#` hoặc dòng trống.
- Chỉ đưa vào `os.environ` nếu biến đó **chưa tồn tại** trong môi trường hệ thống.

### 2.2. Hàm Tự Động Dò Tìm Trình Duyệt `_detect_chromium()`
- Kiểm tra biến môi trường `MUSE2API_CHROMIUM` trước tiên.
- Nếu không tìm thấy, hàm duyệt qua danh sách các đường dẫn nhị phân tiêu chuẩn:
  - Linux: `/usr/bin/chromium`, `/usr/bin/google-chrome`, `/snap/bin/chromium`...
  - Windows: `C:\Program Files\Google\Chrome\Application\chrome.exe`, `msedge.exe`...
  - macOS: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`...
- Dùng `os.path.isfile` và `shutil.which` để xác thực file thực thi tồn tại.

### 2.3. Lớp Cấu Hình `Config` DataClass
Chứa các thuộc tính cấu hình và các property đường dẫn:
- `data_dir`: Thư mục chứa dữ liệu (`data/`).
- `media_dir`: Thư mục chứa ảnh, video đã tạo (`data/media/`).
- `download_dir`: Thư mục trung gian nhận file tải về từ trình duyệt (`data/downloads/`).
- `profile_dir`: Thư mục profile dành riêng cho Chromium (`~/muse2api-profiles/generate`).
- `accounts_file`: File JSON lưu tài khoản (`data/accounts.json`).
- `tasks_file`: File JSON lưu nhiệm vụ (`data/tasks.json`).
- Hàm `ensure_dirs()`: Tự động tạo toàn bộ các thư mục trên nếu chưa có.

---

## 3. Liên kết Liên quan

- [Tài liệu Chi tiết File config.py](../04-chi-tiet-ma-nguon/config-py.md)
- [Bảng Biến Môi Trường](../02-cai-dat/cau-hinh.md)
- [Mục lục Tài liệu](../README.md)
