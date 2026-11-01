# Hệ Thống Tài Liệu Kỹ Thuật MUSE2API

Chào mừng bạn đến với kho tài liệu kỹ thuật toàn diện của dự án **MUSE2API**. Hệ thống tài liệu này được biên soạn theo chuẩn công nghiệp, cung cấp góc nhìn sâu sắc từ tổng thể kiến trúc đến từng dòng mã nguồn và quy trình vận hành.

---

## 🗺️ Hướng Dẫn Lộ Trình Đọc (Reading Path)

Tùy theo vai trò và nhu cầu của bạn, hãy chọn lộ trình đọc phù hợp dưới đây:

### 🚀 Dành cho Người Mới Bắt Đầu & Người Dùng Cuối (User / Quick Start)
1. [01. Giới thiệu Dự án](01-tong-quan/gioi-thieu.md) - Hiểu rõ mục tiêu và tính năng của hệ thống.
2. [02. Yêu cầu Hệ thống](02-cai-dat/yeu-cau-he-thong.md) - Kiểm tra tài nguyên phần cứng và mạng.
3. [03. Hướng dẫn Cài đặt](02-cai-dat/huong-dan-cai-dat.md) - Triển khai nhanh bằng Docker Compose.
4. [04. Cấu hình Biến Môi trường](02-cai-dat/cau-hinh.md) - Thiết lập file `.env` an toàn.
5. [05. Câu hỏi Thường gặp (FAQ)](08-phu-luc/faq.md) - Xử lý các vấn đề thường gặp.

### 💻 Dành cho Kỹ Sư Tích Hợp (API Integration Developer)
1. [01. Tổng quan Giao diện API](06-api/tong-quan-api.md) - Base URL, xác thực Bearer token, bảng mã lỗi.
2. [02. API Chat Completions](06-api/chat-completions.md) - Giao thức trò chuyện và SSE streaming.
3. [03. API Tạo & Sửa Hình Ảnh](06-api/images-generations-edits.md) - Text-to-Image và Image-to-Image.
4. [04. API Tạo Video Bất Đồng Bộ](06-api/videos-generations.md) - Tạo task và polling kết quả video.
5. [05. API Quản Trị Hệ Thống](06-api/admin-management-api.md) - Thao tác hồ chứa tài khoản và bảo hoạt.

### 🏗️ Dành cho Kỹ Sư Phát Triển & Kiến Trúc Sư (Core Developers & Architects)
1. [01. Kiến trúc Tổng thể & Sơ đồ](01-tong-quan/kien-truc.md) - Mô hình phân tầng và cô lập Sandbox.
2. [02. Cấu trúc Thư mục](01-tong-quan/cau-truc-thu-muc.md) - Tổ chức file và thư mục.
3. [03. Công nghệ Sử dụng](01-tong-quan/cong-nghe.md) - Runtime, framework và giao thức CDP.
4. [04. Phân tích Các Module](03-module/app-api.md) - Khảo sát các module `app`, `engine`, `cdp`, `store`.
5. [05. Các Luồng Xử Lý Chính](05-luong-xu-ly/chat-streaming.md) - Sequence diagrams cho từng luồng nghiệp vụ.
6. [06. Chi tiết Từng File Mã Nguồn](04-chi-tiet-ma-nguon/app-py.md) - Đối chiếu sâu từng file code.
7. [07. Quy chuẩn & Đóng góp](07-huong-dan-phat-trien/coding-convention.md) - Quy ước code, Git flow và kiểm thử.
8. [08. Đề xuất Cải tiến](08-phu-luc/de-xuat-cai-tien.md) - Kế hoạch xử lý technical debt và roadmap.

---

## 📚 Mục Lục Toàn Bộ Tài Liệu

### 01. Tổng Quan Dự Án
- [01-1. Giới thiệu Mục tiêu & Phạm vi](01-tong-quan/gioi-thieu.md)
- [01-2. Kiến trúc Tổng thể & Sơ đồ Mermaid](01-tong-quan/kien-truc.md)
- [01-3. Cấu trúc Cây Thư mục Chi tiết](01-tong-quan/cau-truc-thu-muc.md)
- [01-4. Công nghệ, Thư viện & Công cụ Build](01-tong-quan/cong-nghe.md)

### 02. Cài Đặt & Cấu Hình
- [02-1. Yêu cầu Hệ thống & Phần cứng](02-cai-dat/yeu-cau-he-thong.md)
- [02-2. Hướng dẫn Cài đặt Từng Bước (Docker / VPS / Local)](02-cai-dat/huong-dan-cai-dat.md)
- [02-3. Bảng Cấu hình Biến Môi trường (.env)](02-cai-dat/cau-hinh.md)
- [02-4. Lệnh Chạy, Kiểm Thử & Vận Hành](02-cai-dat/chay-du-an.md)

### 03. Tài Liệu Phân Tích Module
- [03-1. Module Web Server & API (`app.py`)](03-module/app-api.md)
- [03-2. Module Động cơ Tự động hóa (`engine.py`)](03-module/engine-core.md)
- [03-3. Module Giao thức CDP (`cdp.py`)](03-module/cdp-driver.md)
- [03-4. Module Lưu trữ & Hồ chứa (`store.py`)](03-module/store-storage.md)
- [03-5. Module Cấu hình (`config.py`)](03-module/config-env.md)
- [03-6. Module Công cụ Phụ trợ (`tools/`)](03-module/tools-helpers.md)
- [03-7. Module Tiện ích Chrome Extension (`extension/`)](03-module/chrome-extension.md)

### 04. Chi Tiết Từng File Mã Nguồn
- [04-01. File `app.py`](04-chi-tiet-ma-nguon/app-py.md)
- [04-02. File `engine.py`](04-chi-tiet-ma-nguon/engine-py.md)
- [04-03. File `cdp.py`](04-chi-tiet-ma-nguon/cdp-py.md)
- [04-04. File `store.py`](04-chi-tiet-ma-nguon/store-py.md)
- [04-05. File `config.py`](04-chi-tiet-ma-nguon/config-py.md)
- [04-06. File `tools/get_muse_cookie.py`](04-chi-tiet-ma-nguon/tools-get-muse-cookie-py.md)
- [04-07. File `tools/mailtm_otp.py`](04-chi-tiet-ma-nguon/tools-mailtm-otp-py.md)
- [04-08. File `tools/verify_engine_selectors.py`](04-chi-tiet-ma-nguon/tools-verify-engine-selectors-py.md)
- [04-09. File `tools/muse2api_cookie_importer.user.js`](04-chi-tiet-ma-nguon/tools-userscript.md)
- [04-10. File `extension/popup.js`](04-chi-tiet-ma-nguon/extension-popup-js.md)

### 05. Sơ Đồ Luồng Xử Lý Nghiệp Vụ (Sequence Diagrams)
- [05-1. Luồng Hội thoại Chat & Stream SSE](05-luong-xu-ly/chat-streaming.md)
- [05-2. Luồng Văn bản Sinh Hình ảnh (Text-to-Image)](05-luong-xu-ly/text-to-image.md)
- [05-3. Luồng Chỉnh sửa Ảnh Tham chiếu (Image-to-Image)](05-luong-xu-ly/image-to-image.md)
- [05-4. Luồng Sinh Video Bất đồng bộ (Async Video)](05-luong-xu-ly/video-generation.md)
- [05-5. Luồng Tự động Duy trì Phiên & Wake VM (Keepalive)](05-luong-xu-ly/session-keepalive.md)
- [05-6. Luồng Đồng bộ & Nhập Cookie Tài khoản](05-luong-xu-ly/cookie-import.md)

### 06. Tài Liệu Tra Cứu API (RESTful Endpoints)
- [06-1. Tổng quan Chuẩn API & Xác thực](06-api/tong-quan-api.md)
- [06-2. Endpoint `/v1/chat/completions`](06-api/chat-completions.md)
- [06-3. Endpoint `/v1/responses` (Codex)](06-api/responses-codex.md)
- [06-4. Endpoints `/v1/images/*` (Generations & Edits)](06-api/images-generations-edits.md)
- [06-5. Endpoints `/v1/videos/*` (Generations & Tasks)](06-api/videos-generations.md)
- [06-6. Endpoints `/admin/*` (Quản trị & Hồ chứa)](06-api/admin-management-api.md)

### 07. Hướng Dẫn Phát Triển & Đóng Góp
- [07-1. Quy chuẩn Lập trình & Viết Comment](07-huong-dan-phat-trien/coding-convention.md)
- [07-2. Quy trình Đóng góp Mã Nguồn (Git Flow & PR)](07-huong-dan-phat-trien/quy-trinh-dong-gop.md)
- [07-3. Hướng dẫn Viết & Chạy Kiểm Thử (Testing)](07-huong-dan-phat-trien/kiem-thu.md)

### 08. Phụ Lục & Mở Rộng
- [08-1. Bảng Thuật Ngữ Kỹ Thuật (Glossary)](08-phu-luc/thuat-ngu.md)
- [08-2. Các Câu Hỏi Thường Gặp (FAQ)](08-phu-luc/faq.md)
- [08-3. Đề Xuất Cải Tiến Kỹ Thuật (Technical Debt & Roadmap)](08-phu-luc/de-xuat-cai-tien.md)

---

## 🛠️ Công Cụ Xem Tài Liệu Cục Bộ (MkDocs)

Để đọc tài liệu với giao diện Material for MkDocs hiện đại và tự động render sơ đồ Mermaid:

```bash
# Cài đặt công cụ
pip install mkdocs mkdocs-material

# Khởi chạy máy chủ tài liệu cục bộ
mkdocs serve
```
Sau đó truy cập: `http://127.0.0.1:8000` trên trình duyệt.
