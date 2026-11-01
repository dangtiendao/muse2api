# Chi Tiết Mã Nguồn: `config.py`

---

## 1. Thông Tin Cơ Bản
- **Đường dẫn file gốc**: [../../config.py](../../config.py)
- **Số dòng mã**: ~159 dòng.
- **Ngôn ngữ**: Python 3.10+.
- **Chức năng chính**: Quản lý tập trung toàn bộ cấu hình hệ thống, tự động nạp file `.env`, tự động dò tìm đường dẫn nhị phân Chromium và cung cấp các thuộc tính đường dẫn thư mục chuẩn hóa.

---

## 2. Vai Trò Trong Hệ Thống
- **Thuộc tầng**: Tầng Cấu Hình (Configuration Layer).
- **Được gọi bởi**: Toàn bộ hệ thống (`app.py`, `engine.py`, `store.py`).
- **Gọi đến**: Môi trường hệ thống (`os.environ`, file hệ thống `.env`).

---

## 3. Danh Sách Các Lớp & Hàm Quan Trọng

| Tên lớp / hàm | Chức năng chi tiết |
| :--- | :--- |
| `_load_dotenv()` | Tự động đọc và nạp file `.env` vào `os.environ` (không ghi đè biến đã có). |
| `_detect_chromium()` | Dò tìm nhị phân Chromium/Chrome/Edge trên Linux, Windows và macOS. |
| `Config` | DataClass chứa toàn bộ cấu hình: cổng, bảo mật, timeouts, concurrency và cờ tính năng. |
| `Config.data_dir` | Trả về đường dẫn tuyệt đối tới `data/`. |
| `Config.media_dir` | Trả về đường dẫn tuyệt đối tới `data/media/`. |
| `Config.profile_dir` | Trả về đường dẫn profile của Chromium (`~/muse2api-profiles/generate`). |
| `Config.ensure_dirs()` | Tạo tự động các thư mục cần thiết nếu chưa tồn tại. |

---

## 4. Phụ Thuộc (Dependencies)
- **Thư viện bên ngoài**: Không (Dùng `os`, `shutil`, `dataclasses`).
- **Module nội bộ**: Không.

---

## 5. Liên kết Liên quan
- [Module Config Env](../03-module/config-env.md)
- [Bảng Biến Môi Trường](../02-cai-dat/cau-hinh.md)
- [Mục lục Tài liệu](../README.md)
