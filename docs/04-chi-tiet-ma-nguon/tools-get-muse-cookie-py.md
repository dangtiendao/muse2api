# Chi Tiết Mã Nguồn: `tools/get_muse_cookie.py`

---

## 1. Thông Tin Cơ Bản
- **Đường dẫn file gốc**: [../../tools/get_muse_cookie.py](../../tools/get_muse_cookie.py)
- **Số dòng mã**: ~476 dòng.
- **Ngôn ngữ**: Python 3.8+ (Zero Dependency, 100% Standard Library).
- **Chức năng chính**: Script CLI khởi chạy cửa sổ Chrome độc lập, lắng nghe qua giao thức CDP WebSocket tự viết để đọc toàn bộ Cookie phiên có cờ `httpOnly` của `muse.ai` và tự động đẩy sang API `/admin/accounts` của máy chủ muse2api.

---

## 2. Vai Trò Trong Hệ Thống
- **Thuộc tầng**: Công Cụ Dòng Lệnh Trợ Giúp (Onboarding Helper CLI).
- **Được gọi bởi**: Người dùng / Quản trị viên trên máy tính cá nhân.
- **Gọi đến**: Cổng DevTools của trình duyệt Chrome cục bộ (cổng 9333) và API Admin của muse2api.

---

## 3. Danh Sách Các Lớp & Hàm Quan Trọng

| Tên lớp / hàm | Chức năng chi tiết |
| :--- | :--- |
| `WS` | Client WebSocket RFC6455 tối giản tự viết (hỗ trợ bắt tay HTTP Upgrade, đóng gói khung tin có mask và phản hồi ping-pong). |
| `_win_registry_paths()` | Tìm kiếm đường dẫn cài đặt của Chrome/Edge/Brave từ Windows Registry `App Paths`. |
| `find_chrome()` | Tự động dò tìm file thực thi của trình duyệt trên Windows, macOS và Linux. |
| `wait_cdp(port, timeout)` | Polling cổng debug cho đến khi endpoint `/json/version` sẵn sàng. |
| `read_cookies(ws)` | Gọi lệnh CDP `Storage.getCookies` để đọc cookie kể cả `httpOnly`. |
| `upload(base, key, label, cookies)` | Gửi HTTP POST đẩy cookie đã lấy lên `/admin/accounts`. |
| `main()` | Điều phối toàn bộ quy trình: khởi chạy trình duyệt, chờ đăng nhập, đọc cookie và báo cáo kết quả. |

---

## 4. Liên kết Liên quan
- [Module Tools](../03-module/tools-helpers.md)
- [Mục lục Tài liệu](../README.md)
