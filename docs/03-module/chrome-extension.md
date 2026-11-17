# Module Tiện Ích Mở Rộng Chrome Extension (`extension/`)

---

## 1. Tổng Quan Module

- **File nguồn**: Thư mục [extension/](file:///e:/Project/muse2api/extension)
- **Chuẩn công nghệ**: Manifest V3 (Chrome Extension Manifest Specification).
- **Mục đích**: Cung cấp giải pháp 1-click cho người dùng trích xuất phiên đăng nhập từ trình duyệt Chrome cá nhân sang máy chủ muse2api mà không cần cài đặt Tampermonkey hay chạy lệnh CLI.

---

## 2. Cấu Trúc Các Tệp Trong Extension

- `manifest.json`: Khai báo thông tin tiện ích, các quyền bắt buộc (`cookies`, `storage`, `tabs`) và quyền truy cập host (`https://*.muse.ai/*`).
- `popup.html`: Giao diện cửa sổ nhỏ hiện lên khi click biểu tượng extension trên thanh công cụ trình duyệt.
- `popup.js`: Toàn bộ logic giao diện, đọc cookie bằng `chrome.cookies.getAll`, kiểm tra thiếu sót cookie cốt lõi (`hatch_sess`, `hatch_vml`) và gọi API `fetch()` đẩy sang server `/admin/accounts`.
- `_locales/`: Bản dịch đa ngôn ngữ giao diện (i18n), hỗ trợ Tiếng Việt (`vi` - mặc định), Tiếng Anh (`en`) và Tiếng Trung (`zh_CN`).

---

## 3. Cách Phân Phối Cho Người Dùng

Máy chủ muse2api tích hợp sẵn endpoint:
```text
GET /admin/extension
```
Endpoint này tự động nén toàn bộ thư mục `extension/` thành tệp `muse2api-extension.zip` và cho phép người dùng tải về trực tiếp từ giao diện Admin Console.

Người dùng chỉ cần:
1. Tải file zip về máy và giải nén.
2. Mở trình duyệt Chrome, truy cập `chrome://extensions/`.
3. Bật **Developer mode** (Chế độ dành cho nhà phát triển).
4. Nhấn **Load unpacked** (Tải tiện ích đã giải nén) và chọn thư mục `extension/`.

---

## 4. Liên kết Liên quan

- [Tài liệu Chi tiết File popup.js](../04-chi-tiet-ma-nguon/extension-popup-js.md)
- [Module Tools](tools-helpers.md)
- [Mục lục Tài liệu](../README.md)
