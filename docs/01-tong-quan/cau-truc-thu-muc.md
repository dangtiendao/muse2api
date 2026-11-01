# Cấu Trúc Thư Mục Dự Án MUSE2API

---

## 1. Sơ đồ Cây Thư Mục Chi Tiết

Dưới đây là cấu trúc tổ chức toàn bộ mã nguồn, cấu hình, dữ liệu và công cụ của dự án:

```text
muse2api/
├── .env.example                     # Mẫu cấu hình biến môi trường
├── .gitignore                       # Danh sách loại trừ tệp khỏi Git
├── LICENSE                          # Giấy phép mã nguồn mở MIT
├── README.md                        # Tài liệu giới thiệu tổng quan dự án
├── Dockerfile                       # Định nghĩa build Docker Image
├── docker-compose.yml               # Cấu hình triển khai cụm dịch vụ qua Docker Compose
├── requirements.txt                 # Khai báo các gói thư viện Python bắt buộc
├── version.json                     # Thông tin phiên bản và SHA commit hiện tại
├── admin.html                       # Giao diện Web Console quản trị (SPA)
│
├── config.py                        # Quản lý cấu hình toàn cục và nạp biến môi trường
├── store.py                         # Quản lý hồ chứa tài khoản và lưu trữ tác vụ JSON
├── cdp.py                           # Client giao tiếp Chrome DevTools Protocol qua WebSocket
├── engine.py                        # Động cơ tự động hóa điều khiển Chromium và muse.ai
├── app.py                           # Ứng dụng chính FastAPI, OpenAI-compatible API & Admin API
│
├── data/                            # Thư mục chứa dữ liệu runtime động
│   ├── accounts.example.json        # Mẫu file lưu trữ tài khoản
│   ├── accounts.json                # Danh sách tài khoản thực tế (tạo khi chạy)
│   ├── tasks.json                   # Danh sách nhiệm vụ bất đồng bộ (tạo khi chạy)
│   ├── downloads/                   # Tệp tạm do trình duyệt tải xuống
│   └── media/                       # Tệp hình ảnh và video đã tạo được lưu trữ lâu dài
│       └── .gitkeep
│
├── deploy/                          # Tài liệu & mẫu cấu hình triển khai hạ tầng
│   ├── muse2api.service             # File dịch vụ chạy ngầm trên Linux qua Systemd
│   └── nginx.example.conf           # Cấu hình Reverse Proxy Nginx, SSL và hỗ trợ SSE
│
├── extension/                       # Tiện ích mở rộng Chrome Extension (Manifest V3)
│   ├── manifest.json                # Metadata và quyền truy cập extension
│   ├── popup.html                   # Giao diện cửa sổ popup của extension
│   ├── popup.js                     # Mã xử lý đọc cookie httpOnly và đẩy về server
│   ├── README.md                    # Hướng dẫn cài đặt và sử dụng extension
│   └── _locales/                    # Tập tin bản dịch đa ngôn ngữ giao diện
│       ├── en/messages.json         # Tiếng Anh
│       └── zh_CN/messages.json      # Tiếng Trung
│
├── tools/                           # Bộ công cụ dòng lệnh (CLI) và tiện ích phụ trợ
│   ├── get_muse_cookie.py           # CLI tự mở Chromium tạm để trích xuất cookie qua CDP
│   ├── mailtm_otp.py                # CLI đăng ký hòm thư tạm Mail.tm và polling mã OTP
│   ├── muse2api_cookie_importer.user.js # Tampermonkey Userscript xuất cookie trực tiếp trên web
│   └── verify_engine_selectors.py   # Script kiểm thử và chẩn đoán bộ chọn DOM selector
│
├── tests/                           # Bộ kiểm thử tự động (Unit Test & Integration Test)
│   ├── test_admin_api_error_messages.mjs
│   ├── test_admin_base_url.py
│   ├── test_async_images.py
│   ├── test_concurrency.py
│   ├── test_cookie_requirements.py
│   ├── test_extension_zip.py
│   ├── test_keepalive_scheduling.py
│   ├── test_media_delete.py
│   ├── test_media_selection.py
│   ├── test_muse_video_delivery.py
│   ├── test_quota_account_binding.py
│   ├── test_quota_localization.py
│   ├── test_ref_image_safety.py
│   ├── test_reference_limits.py
│   ├── test_refusal_rotation.py
│   ├── test_session_health.py
│   ├── test_vm_wait.py
│   └── test_wake_confirmation.py
│
└── docs/                            # Hệ thống tài liệu kỹ thuật chuẩn công nghiệp
    ├── README.md                    # Mục lục và lộ trình đọc tài liệu
    ├── 01-tong-quan/                # Giới thiệu, kiến trúc, cây thư mục, công nghệ
    ├── 02-cai-dat/                  # Yêu cầu hệ thống, cài đặt, cấu hình, khởi chạy
    ├── 03-module/                   # Tài liệu phân tích từng module thành phần
    ├── 04-chi-tiet-ma-nguon/        # Báo cáo kỹ thuật chi tiết từng file mã nguồn
    ├── 05-luong-xu-ly/              # Sơ đồ tuần tự các luồng nghiệp vụ chính
    ├── 06-api/                      # Tài liệu tra cứu chi tiết các API endpoints
    ├── 07-huong-dan-phat-trien/     # Quy chuẩn code, quy trình đóng góp, kiểm thử
    └── 08-phu-luc/                  # Thuật ngữ, câu hỏi thường gặp, đề xuất cải tiến
```

---

## 2. Giải thích Vai trò Từng Thư mục Chính

| Tên thư mục | Vai trò | Lưu ý khi phát triển |
| :--- | :--- | :--- |
| **Gốc (`/`)** | Chứa các file mã nguồn lõi của server (`app.py`, `engine.py`...) | Giữ cấu trúc phẳng, hạn chế import vòng chéo. |
| **`data/`** | Chứa toàn bộ dữ liệu biến đổi trong quá trình chạy (Stateful) | Phải được đưa vào `.gitignore` để tránh rò rỉ cookie người dùng. Khi chạy Docker, cần mount volume vào thư mục này. |
| **`deploy/`** | Các file mẫu phục vụ cấu hình hạ tầng triển khai thực tế | Cần chỉnh sửa đường dẫn và tên miền phù hợp trước khi đưa vào sản xuất. |
| **`extension/`** | Mã nguồn tiện ích mở rộng Chrome dùng xuất cookie tiện lợi | Đóng gói thành tệp `.zip` phục vụ người dùng tải về trực tiếp từ endpoint `/admin/extension`. |
| **`tools/`** | Các công cụ script hỗ trợ quá trình onboarding tài khoản | Độc lập với backend chính, có thể chạy độc lập trên máy tính cá nhân. |
| **`tests/`** | Các bài kiểm thử tự động xác minh từng khía cạnh kỹ thuật | Chạy tự động để kiểm tra hồi quy khi sửa đổi mã nguồn. |
| **`docs/`** | Kho tài liệu kỹ thuật toàn diện của dự án | Phải được cập nhật đồng bộ mỗi khi có thay đổi logic hoặc API. |

---

## 3. Liên kết Liên quan

- [Giới thiệu Dự án](gioi-thieu.md)
- [Kiến trúc Tổng thể](kien-truc.md)
- [Công nghệ Sử dụng](cong-nghe.md)
- [Mục lục Tài liệu](../README.md)
