# Chi Tiết Mã Nguồn: `cdp.py`

---

## 1. Thông Tin Cơ Bản
- **Đường dẫn file gốc**: [../../cdp.py](../../cdp.py)
- **Số dòng mã**: ~73 dòng.
- **Ngôn ngữ**: Python 3.10+.
- **Chức năng chính**: Cung cấp client giao tiếp Chrome DevTools Protocol tối giản qua kết nối WebSocket, hỗ trợ gửi lệnh RPC đồng bộ, thực thi JavaScript trong trang và lắng nghe sự kiện.

---

## 2. Vai Trò Trong Hệ Thống
- **Thuộc tầng**: Tầng Giao thức Trình duyệt Cấp thấp (Low-level Browser Protocol Layer).
- **Được gọi bởi**: `engine.py`, `tools/verify_engine_selectors.py`.
- **Gọi đến**: Cổng Remote Debugging Port của trình duyệt Chromium (mặc định 19210).

---

## 3. Luồng Xử Lý Dữ Liệu (Data Flow)

```text
Lệnh CDP (Method, Params)
  ↓
Khóa `threading.Lock()` bảo vệ an toàn đa luồng
  ↓
Tăng `_id` & Gửi JSON qua WebSocket
  ↓
Vòng lặp nhận gói tin qua `ws.recv()` & So khớp `msg["id"] == _id`
  ↓
Kiểm tra trường "error" (ném CDPError nếu có) hoặc trả về `msg["result"]`
```

---

## 4. Danh Sách Các Lớp & Hàm Quan Trọng

| Tên lớp / hàm | Chức năng chi tiết |
| :--- | :--- |
| `CDPError` | Lớp ngoại lệ khi Chromium phản hồi lỗi cho một lệnh CDP. |
| `CDP` | Lớp client WebSocket RPC quản lý kết nối và thực thi lệnh. |
| `CDP.send(method, params, timeout)` | Gửi lệnh CDP đồng bộ theo ID và chờ kết quả. |
| `CDP.js(expr, await_promise, timeout)`| Thực thi đoạn mã JavaScript trong context của trang (`Runtime.evaluate`). |
| `CDP.pump(seconds, on_event)` | Lắng nghe liên tục các sự kiện bất đồng bộ phát ra từ trình duyệt. |
| `CDP.close()` | Đóng kết nối WebSocket an toàn. |
| `http_json(url, timeout)` | Helper gửi HTTP GET để lấy thông tin phiên bản/mục tiêu từ cổng debug. |

---

## 5. Phụ Thuộc (Dependencies)
- **Thư viện bên ngoài**: `websocket-client`, `requests`.
- **Module nội bộ**: Không.

---

## 6. Liên kết Liên quan
- [Module CDP Driver](../03-module/cdp-driver.md)
- [Module Engine Core](../03-module/engine-core.md)
- [Mục lục Tài liệu](../README.md)
