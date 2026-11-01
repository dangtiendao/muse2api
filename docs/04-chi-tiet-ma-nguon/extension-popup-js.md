# Chi Tiết Mã Nguồn: `extension/popup.js`

---

## 1. Thông Tin Cơ Bản
- **Đường dẫn file gốc**: [../../extension/popup.js](../../extension/popup.js)
- **Số dòng mã**: ~235 dòng.
- **Ngôn ngữ**: JavaScript (ES6+), Chrome Extension Manifest V3.
- **Chức năng chính**: Logic xử lý cho popup của Chrome Extension muse2api, tự động đọc cookie phiên của miền `muse.ai` qua `chrome.cookies API` và đồng bộ vào máy chủ muse2api.

---

## 2. Vai Trò Trong Hệ Thống
- **Thuộc tầng**: Tiện Ích Trình Duyệt Phía Khách Hàng (Official Chrome Extension).
- **Được gọi bởi**: Người dùng click biểu tượng tiện ích mở rộng trên thanh công cụ trình duyệt.
- **Gọi đến**: API Quản trị muse2api (`/admin/accounts`).

---

## 3. Danh Sách Hàm Quan Trọng

| Tên hàm | Chức năng chi tiết |
| :--- | :--- |
| `grabCookies()` | Gọi `chrome.cookies.getAll({ domain: 'muse.ai' })` để lấy toàn bộ cookie bao gồm cả các cookie `httpOnly`. |
| `normBase(v)` | Chuẩn hóa địa chỉ URL máy chủ (thêm https nếu thiếu, bỏ `/v1` và dấu gạch chéo cuối). |
| `loadCfg()` / `saveCfg()` | Nạp và lưu cấu hình từ `chrome.storage.local`. Tự động nhận diện URL nếu tab hiện tại là trang Admin muse2api. |
| `run()` | Kiểm tra cookie cốt lõi, gọi `fetch()` gửi POST sang server và cập nhật log hiển thị. |
| `applyLang()` | Cập nhật ngôn ngữ giao diện (Anh/Trung) dựa trên lựa chọn của người dùng. |

---

## 4. Liên kết Liên quan
- [Module Chrome Extension](../03-module/chrome-extension.md)
- [Module Tools](../03-module/tools-helpers.md)
- [Mục lục Tài liệu](../README.md)
