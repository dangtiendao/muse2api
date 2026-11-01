# Chi Tiết Mã Nguồn: `engine.py`

---

## 1. Thông Tin Cơ Bản
- **Đường dẫn file gốc**: [../../engine.py](../../engine.py)
- **Số dòng mã**: ~1573 dòng.
- **Ngôn ngữ**: Python 3.10+.
- **Chức năng chính**: Trực tiếp quản lý tiến trình Chromium vô đầu, điều khiển giao tiếp qua Chrome DevTools Protocol (CDP), mở các Incognito BrowserContext độc lập, tự động hóa thao tác người dùng trên giao diện web muse.ai (sinh ảnh, sinh video, hội thoại stream, đọc hạn mức quota).

---

## 2. Vai Trò Trong Hệ Thống
- **Thuộc tầng**: Động cơ Tự động hóa Thực thi (Core Automation Engine Layer).
- **Được gọi bởi**: `app.py` (trong các hàm `chat_completions`, `_run_generation_locked`, `_probe_account_sync`).
- **Gọi đến**:
  - `cdp.CDP`: Gửi các lệnh RPC qua WebSocket tới trình duyệt.
  - `config.CFG`: Nạp đường dẫn binary Chromium và thư mục lưu trữ media.
  - API HTTP nội bộ của `muse.ai` (`/api/session`, `/api/hatch/vm/wake`).

---

## 3. Luồng Xử Lý Dữ Liệu (Data Flow)

```text
Yêu cầu sinh nội dung (Cookies, Prompt, Tham chiếu ảnh)
  ↓
Khởi tạo hoặc kiểm tra Tab Incognito (`ensure_page`)
  ↓
Bơm Cookies vào tab (`_apply_cookies`) & Điều hướng tới `/thread/new`
  ↓
Nếu có ảnh tham chiếu: Tạo Blob qua File API và inject bằng `DataTransfer` (`_attach_images`)
  ↓
Điền prompt vào React textarea qua prototype setter & Click Send (`_send`)
  ↓
Lắng nghe phần tử kết quả `[data-testid^=hatch-chat-attachment-presentation-]` (`_wait_attachment`)
  ↓
Rút trích Blob nhị phân từ thẻ img/video (`extract_bytes`) hoặc Fallback click Download (`_download_fallback`)
  ↓
Ghi tệp vào `data/media/<uuid>.<ext>` & Trả về metadata chi tiết
```

---

## 4. Danh Sách Các Lớp & Hàm Quan Trọng

| Tên lớp / hàm | Chức năng chi tiết |
| :--- | :--- |
| `MuseEngine` | Lớp điều khiển chính, quản lý vòng đời tiến trình Chromium và các context. |
| `start()` / `stop()` | Khởi chạy hoặc dừng tiến trình Chromium vô đầu. |
| `renew_session_http(...)` | Gia hạn cookie `hatch_vml` (+48h) và gọi đánh thức VM qua HTTP trực tiếp mà không cần mở tab. |
| `ensure_page(...)` | Đảm bảo tab làm việc sẵn sàng, tái sử dụng tab cũ nếu cùng tài khoản và tab khỏe. |
| `_send(...)` | Điền prompt siêu tốc vào React 18 textarea và phát sự kiện gửi. |
| `_wait_attachment(...)` | Vòng lặp chờ tệp đính kèm kết quả mới, kiểm tra kích thước `w, h > 0` và phát hiện lỗi từ chối của mô hình. |
| `chat_stream(...)` | Gửi tin nhắn và yield từng token văn bản với chu kỳ polling 60ms. |
| `extract_bytes(...)` | Chạy JavaScript trong trang để fetch Blob nhị phân và mã hóa Base64 trả về. |
| `_download_fallback(...)` | Phương án dự phòng click nút Download trên DOM nếu không fetch được Blob. |
| `_normalize_image(...)` | Chuẩn hóa ảnh đầu vào (URL, Base64, Data URL), kiểm tra kích thước và kiểm tra an toàn SSRF. |
| `_attach_images(...)` | Bơm tối đa 4 ảnh tham chiếu vào input file thông qua DataTransfer API. |
| `quota(...)` | Mở trang Settings và đọc dung lượng gói cước trong một ngữ cảnh dùng 1 lần (disposable context). |

---

## 5. Phụ Thuộc (Dependencies)
- **Thư viện bên ngoài**: `websocket-client`, `requests`.
- **Module nội bộ**: `cdp.CDP`, `cdp.http_json`, `config.CFG`.

---

## 6. Lưu Ý Kỹ Thuật & Rủi Ro Tiềm Ẩn
1. **Phụ thuộc vào giao diện muse.ai**: Nếu muse.ai thay đổi các thuộc tính `data-testid`, class name hoặc cấu trúc form, engine cần được cập nhật bộ chọn tương ứng (sử dụng script `verify_engine_selectors.py` để hỗ trợ).
2. **Khóa chống giẫm chân**: Engine sử dụng `threading.local()` để lưu biến `page` theo luồng, kết hợp `AccountPoolManager` ở tầng trên để đảm bảo không bị lẫn lộn dữ liệu giữa các tài khoản song song.

---

## 7. Liên kết Liên quan
- [Module Engine Core](../03-module/engine-core.md)
- [Module CDP Driver](../03-module/cdp-driver.md)
- [Luồng Xử Lý Sinh Video](../05-luong-xu-ly/video-generation.md)
- [Mục lục Tài liệu](../README.md)
