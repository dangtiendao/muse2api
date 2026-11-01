# Đề Xuất Cải Tiến Kỹ Thuật (Technical Debt & Roadmap)

---

## 1. Nợ Kỹ Thuật & Tối Ưu Hóa Lưu Trữ (Technical Debt)

### 1.1. Chuyển Đổi Tầng Lưu Trữ Sang SQLite
- **Hiện trạng**: [store.py](../../store.py) đang lưu trữ toàn bộ dữ liệu vào 2 file JSON (`accounts.json` và `tasks.json`) với cơ chế rewrite toàn bộ file qua file tạm mỗi khi có thay đổi.
- **Rủi ro**: Khi số lượng tác vụ đạt hàng chục nghìn records, việc nạp và serialize toàn bộ JSON gây lãng phí bộ nhớ RAM và làm tăng thời gian I/O đĩa.
- **Giải pháp đề xuất**:
  - Tích hợp **SQLite** với chế độ **WAL (Write-Ahead Logging)**.
  - Sử dụng thư viện chuẩn `sqlite3` của Python (không cần thêm dependency ngoài).
  - Tách bảng `accounts` và `tasks`, đánh index trên các trường `status`, `created_at`, `expires_at`.

---

## 2. Quản Lý Vòng Đời Trình Duyệt (Browser Memory Management)

### 2.1. Cơ Chế Auto-Recycle Browser Định Kỳ
- **Hiện trạng**: Tiến trình Chromium chạy liên tục trong suốt thời gian server hoạt động. Mặc dù các `BrowserContext` đã được tiêu hủy sau mỗi tác vụ, Chromium vẫn có thể bị rò rỉ bộ nhớ nhẹ ở tầng V8 Engine sau hàng nghìn thao tác.
- **Giải pháp đề xuất**:
  - Bổ sung bộ đếm số lượng tác vụ đã hoàn thành.
  - Sau mỗi 200 tác vụ hoặc khi phát hiện dung lượng RAM của Chromium vượt quá 1.5 GB, hệ thống sẽ chờ các tác vụ đang bận hoàn tất rồi tự động khởi động lại tiến trình Chromium một cách mượt mà (Graceful Browser Restart).

---

## 3. Khả Năng Chịu Lỗi & Cân Bằng Tải (Resilience & Circuit Breaker)

### 3.1. Mô Hình Circuit Breaker Cho Tài Khoản
- **Hiện trạng**: Khi một tài khoản bị lỗi hoặc bị Cloudflare hạn chế tạm thời, hệ thống đánh dấu `ok=False` nhưng có thể cần quản trị viên kiểm tra lại.
- **Giải pháp đề xuất**:
  - Tự động chuyển tài khoản gặp lỗi sang trạng thái "Tạm phạt" (Cool-down) trong 15 đến 30 phút.
  - Sau thời gian cool-down, tự động gọi `renew_session_http` để thử kích hoạt lại trước khi đưa lại vào hồ chứa hoạt động.

---

## 4. Tự Động Hóa CI/CD & Kiểm Thử Hồi Quy

- **Hiện trạng**: Bộ test rất phong phú nhưng chạy thủ công.
- **Giải pháp đề xuất**:
  - Tạo GitHub Actions workflow để tự động chạy `unittest` và kiểm tra link hỏng trong tài liệu `docs/` mỗi khi có commit hoặc Pull Request mới.

---

## 5. Liên kết Liên quan
- [Kiến Trúc Tổng Thể](../01-tong-quan/kien-truc.md)
- [Bảng Thuật Ngữ](thuat-ngu.md)
- [Mục lục Tài liệu](../README.md)
