# Nhật Ký Thay Đổi (Changelog)

Toàn bộ các thay đổi đáng chú ý của dự án **MUSE2API** sẽ được ghi nhận tại tệp này theo chuẩn [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) và tuân thủ [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.7.0] - 2026-11-01

### Added
- **Hệ thống tài liệu kỹ thuật toàn diện (Technical Documentation)**:
  - Khởi tạo thư mục `docs/` với hơn 35 tệp tài liệu chi tiết, phân chia khoa học từ tổng quan, kiến trúc, phân tích từng file code, sơ đồ tuần tự Mermaid đến tài liệu tra cứu API đầy đủ.
  - Tích hợp công cụ sinh tài liệu trực quan `mkdocs.yml` với giao diện Material for MkDocs.
  - Thiết lập mẫu CI/CD `.github/workflows/docs-ci.yml` kiểm tra liên kết và tự động triển khai tài liệu lên GitHub Pages.
  - Thêm tài liệu hướng dẫn đóng góp `CONTRIBUTING.md` và mẫu PR template `.github/PULL_REQUEST_TEMPLATE.md`.
- **Bổ sung Comment Tiếng Việt**:
  - Bổ sung 100% docstring chuẩn PEP 257 và JSDoc tiếng Việt vào toàn bộ mã nguồn: `config.py`, `cdp.py`, `store.py`, `engine.py`, `app.py`, `tools/` và `extension/`.

---

## [1.6.1] - 2026-10-13

### Fixed
- Sửa lỗi truy vấn hạn mức đa tài khoản bị lẫn lộn dữ liệu giữa các tab Chromium.
- Giữ lại bộ nhớ đệm cũ khi đọc hạn mức thất bại, tránh báo cáo sai lệch dung lượng.
- Sửa lỗi báo cáo sai trạng thái đánh thức VM: phân biệt rõ ràng giữa tín hiệu đánh thức được chấp nhận và trạng thái VM thực sự đạt `RUNNING`.
- Thêm kiểm thử hồi quy độc lập cho việc cô lập quota và xác nhận trạng thái VM.

---

## [1.5.3] - 2026-09-28

### Added
- Cơ chế chẩn đoán lỗi chi tiết cho các phản hồi `/api/session` HTTP 401, 403, 429, 5xx.
- Giữ nguyên trạng thái tài khoản khi mạng máy chủ không ổn định thay vì đánh dấu hỏng sai lệch.

---

## [1.5.2] - 2026-09-15

### Added
- Hỗ trợ tác vụ sinh ảnh bất đồng bộ qua endpoint `POST /v1/images/tasks` và polling qua `GET /v1/images/tasks/{task_id}` để tránh bị CDN/Reverse Proxy ngắt kết nối khi sinh ảnh lâu.

---

## [1.0.0] - 2026-08-01

### Added
- Bản phát hành ban đầu của dự án muse2api:
  - Hỗ trợ đầy đủ OpenAI Chat Completions với SSE streaming.
  - Hỗ trợ Text-to-Image và Image-to-Video.
  - Quản lý hồ chứa tài khoản và giao diện Admin Web Console.
