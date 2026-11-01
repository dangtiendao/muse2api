# Module Công Cụ Phụ Trợ & Scripts (`tools/`)

---

## 1. Tổng Quan Thư Mục `tools/`

Thư mục `tools/` chứa các tiện ích dòng lệnh (CLI) độc lập và kịch bản người dùng phục vụ cho việc vận hành, onboarding tài khoản và chẩn đoán kỹ thuật.

---

## 2. Chi Tiết Các Công Cụ

### 2.1. `get_muse_cookie.py` – Trích Xuất Cookie Qua CDP
- **Đường dẫn**: [tools/get_muse_cookie.py](file:///e:/Project/muse2api/tools/get_muse_cookie.py)
- **Mục đích**: Vì các cookie phiên của muse.ai (`hatch_sess`, `hatch_vml`) mang cờ `httpOnly`, các script JavaScript thông thường trên console không đọc được. Công cụ này khởi chạy một cửa sổ Chromium tạm với cổng gỡ lỗi CDP (`9333`), lắng nghe qua WebSocket tự viết và gọi `Storage.getCookies` để đọc cookie HttpOnly, sau đó tự động gửi POST lên endpoint `/admin/accounts` của muse2api.
- **Ưu điểm**: Hoàn toàn không phụ thuộc thư viện bên ngoài (Zero-dependency, 100% Python Standard Library).

### 2.2. `mailtm_otp.py` – Email Tạm & Polling Mã OTP
- **Đường dẫn**: [tools/mailtm_otp.py](file:///e:/Project/muse2api/tools/mailtm_otp.py)
- **Mục đích**: Khi đăng ký hoặc đăng nhập tài khoản muse.ai bằng email, hệ thống gửi mã xác nhận OTP 6 số. Công cụ này tương tác với REST API của `Mail.tm`:
  - Tạo hòm thư ngẫu nhiên hoặc tái sử dụng địa chỉ cũ.
  - Vòng lặp polling hòm thư mỗi 3 giây.
  - Dùng Regular Expression trích xuất mã OTP từ 4-8 số và in ra màn hình.

### 2.3. `verify_engine_selectors.py` – Chẩn Đoán & Xác Minh DOM Selectors
- **Đường dẫn**: [tools/verify_engine_selectors.py](file:///e:/Project/muse2api/tools/verify_engine_selectors.py)
- **Mục đích**: Hỗ trợ kỹ sư kiểm tra xem giao diện muse.ai có thay đổi bộ chọn DOM hay không. Kết nối vào cổng CDP (19210) của server đang chạy, thực thi đoạn mã trích xuất đính kèm `_ATT_JS`, kiểm tra nút Remove attachment và in danh sách tất cả các nút `button[aria-label]`.

### 2.4. `muse2api_cookie_importer.user.js` – Tampermonkey Userscript
- **Đường dẫn**: [tools/muse2api_cookie_importer.user.js](file:///e:/Project/muse2api/tools/muse2api_cookie_importer.user.js)
- **Mục đích**: Chạy trực tiếp trên trình duyệt khi người dùng duyệt web `https://muse.ai/`.
  - Hiển thị một nút tròn nổi (Floating Trigger) ở góc phải màn hình.
  - Cho phép mở bảng điều khiển nhập thông tin URL server và API key.
  - Sử dụng `GM_cookie` API để đọc các cookie HttpOnly và gửi thẳng sang server bằng `GM_xmlhttpRequest`.

---

## 3. Liên kết Liên quan

- [Tài liệu Chi tiết Từng File Tools](../04-chi-tiet-ma-nguon/tools-get-muse-cookie-py.md)
- [Module Chrome Extension](chrome-extension.md)
- [Mục lục Tài liệu](../README.md)
