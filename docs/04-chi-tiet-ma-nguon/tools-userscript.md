# Chi Tiết Mã Nguồn: `tools/muse2api_cookie_importer.user.js`

---

## 1. Thông Tin Cơ Bản
- **Đường dẫn file gốc**: [../../tools/muse2api_cookie_importer.user.js](../../tools/muse2api_cookie_importer.user.js)
- **Số dòng mã**: ~398 dòng.
- **Ngôn ngữ**: JavaScript (ES6+), Tampermonkey / Violentmonkey Userscript.
- **Chức năng chính**: Tiện ích chạy trên trang `https://muse.ai/`, cung cấp nút tròn nổi và bảng điều khiển trực quan để người dùng kiểm tra trạng thái phiên và 1-click xuất cookie gửi sang muse2api.

---

## 2. Vai Trò Trong Hệ Thống
- **Thuộc tầng**: Tiện Ích Trình Duyệt Phía Người Dùng (Client-side Userscript).
- **Được gọi bởi**: Tiện ích mở rộng Tampermonkey / Violentmonkey khi người dùng truy cập `muse.ai`.
- **Gọi đến**: API Quản trị muse2api (`/admin/accounts`).

---

## 3. Danh Sách Hàm Quan Trọng

| Tên hàm | Chức năng chi tiết |
| :--- | :--- |
| `getCookies()` | Sử dụng `GM_cookie.list()` để đọc toàn bộ cookie của miền `muse.ai` (bao gồm cả `httpOnly`), kết hợp `document.cookie`. |
| `checkSessionStatus()` | Xác minh sự hiện diện của `hatch_sess` và `hatch_vml`, trả về trạng thái phiên hoàn chỉnh hay chưa. |
| `executePush(btnEl)` | Đóng gói JSON payload, gửi HTTP POST sang server bằng `GM_xmlhttpRequest`, đồng thời sao chép chuỗi cookie vào Clipboard để dự phòng. |
| `showPanel()` | Tạo phần tử DOM và hiển thị bảng cấu hình nổi với hiệu ứng kính mờ (Glassmorphism). |
| `mountFloatingTrigger()` | Gắn nút tròn nổi ⚡ ở góc dưới bên phải màn hình. |

---

## 4. Liên kết Liên quan
- [Module Tools](../03-module/tools-helpers.md)
- [Module Chrome Extension](../03-module/chrome-extension.md)
- [Mục lục Tài liệu](../README.md)
