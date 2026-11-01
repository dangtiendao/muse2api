# Các Lệnh Chạy, Kiểm Thử & Vận Hành Dự Án

---

## 1. Khởi Chạy Môi Trường Phát Triển (Development Mode)

Chạy ứng dụng với chế độ tự động reload khi mã nguồn thay đổi:

```bash
# Kích hoạt môi trường ảo nếu có
source venv/bin/activate   # Trên Linux / macOS
# .\venv\Scripts\Activate.ps1  # Trên Windows PowerShell

# Chạy với Uvicorn reload
uvicorn app:app --host 0.0.0.0 --port 18610 --reload
```

---

## 2. Khởi Chạy Môi Trường Sản Xuất (Production Mode)

### Cách 1: Sử dụng Docker Compose (Khuyên dùng)
```bash
# Khởi động dịch vụ ở chế độ chạy ngầm
docker compose up -d

# Xem log thời gian thực
docker compose logs -f --tail=100

# Khởi động lại dịch vụ
docker compose restart

# Dừng dịch vụ
docker compose down
```

### Cách 2: Chạy trực tiếp qua Uvicorn tiêu chuẩn
```bash
python app.py
```

### Cách 3: Quản lý qua Systemd Service (Linux)
```bash
sudo systemctl start muse2api     # Khởi động
sudo systemctl stop muse2api      # Dừng
sudo systemctl restart muse2api   # Khởi động lại
sudo systemctl status muse2api    # Kiểm tra trạng thái
journalctl -u muse2api -f         # Xem nhật ký log
```

---

## 3. Lệnh Kiểm Thử Hệ Thống (Testing)

Dự án trang bị bộ test tự động toàn diện trong thư mục `tests/`:

```bash
# Chạy toàn bộ các bài test với unittest của Python
python -m unittest discover tests

# Chạy từng file test cụ thể:
python -m unittest tests.test_concurrency
python -m unittest tests.test_session_health
python -m unittest tests.test_ref_image_safety
python -m unittest tests.test_keepalive_scheduling

# Chạy test thông điệp lỗi API Admin bằng Node.js:
node tests/test_admin_api_error_messages.mjs
```

---

## 4. Sử Dụng Các Script Công Cụ (Tools)

### 4.1. Công cụ lấy Cookie tự động qua CDP (`get_muse_cookie.py`)
Mở một cửa sổ Chrome riêng biệt để người dùng đăng nhập, script tự đọc cookie và gửi lên server:
```bash
python tools/get_muse_cookie.py --base http://127.0.0.1:18610 --key m2a_xxx --label my-acc-01
```

### 4.2. Công cụ tạo Email tạm và nhận mã OTP (`mailtm_otp.py`)
```bash
# Đăng ký email mới và lắng nghe mã xác thực
python tools/mailtm_otp.py

# Hoặc tái sử dụng email cũ:
python tools/mailtm_otp.py --addr your-email@domain.com --pass your-password
```

### 4.3. Công cụ kiểm tra DOM Selectors của muse.ai (`verify_engine_selectors.py`)
Khi nghi ngờ muse.ai thay đổi giao diện làm hỏng việc bắt kết quả:
```bash
python tools/verify_engine_selectors.py
```

---

## 5. Sinh & Xem Tài Liệu Kỹ Thuật (Documentation)

Dự án hỗ trợ sinh trang web tài liệu hoàn chỉnh qua **MkDocs**:

```bash
# Cài đặt MkDocs và giao diện Material
pip install mkdocs mkdocs-material

# Xem trực tiếp trên máy cục bộ (Live Reload)
mkdocs serve
# Truy cập: http://127.0.0.1:8000

# Đóng gói xuất bản HTML tĩnh
mkdocs build
```

---

## 6. Liên kết Liên quan

- [Yêu Cầu Hệ Thống](yeu-cau-he-thong.md)
- [Hướng Dẫn Cài Đặt](huong-dan-cai-dat.md)
- [Cấu Hình](cau-hinh.md)
- [Quy Trình Kiểm Thử](../07-huong-dan-phat-trien/kiem-thu.md)
- [Mục lục Tài liệu](../README.md)
