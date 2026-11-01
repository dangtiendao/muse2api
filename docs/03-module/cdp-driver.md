# Module Giao Thức DevTools Cấp Thấp (`cdp.py`)

---

## 1. Tổng Quan Module

- **File nguồn**: [cdp.py](file:///e:/Project/muse2api/cdp.py)
- **Vai trò**: Cung cấp lớp điều khiển Chrome DevTools Protocol tối giản (Lightweight CDP Client), đóng gói việc giao tiếp RPC qua WebSocket mà không cần phụ thuộc vào các framework nặng nề như Playwright hay Puppeteer.

---

## 2. Chi Tiết Lớp `CDP`

### 2.1. Khởi Tạo & Kết Nối (`__init__`)
```python
CDP(ws_url: str, timeout: float = 90.0, max_size: int = 256 << 20)
```
- Sử dụng thư viện `websocket.create_connection` để mở kết nối TCP/WebSocket trực tiếp tới URL DevTools do Chromium cung cấp.
- Đặt `max_size` lên tới **256 MiB** để có thể nhận các chuỗi Base64 dữ liệu lớn từ lệnh `Runtime.evaluate` (chẳng hạn khi trích xuất video hoặc ảnh chất lượng cao dạng data blob).

### 2.2. Gửi Lệnh JSON-RPC (`send`)
```python
send(method: str, params: dict | None = None, timeout: float | None = None) -> dict
```
- Tăng biến đếm `self._id` để tạo ID request duy nhất.
- Đóng gói thông điệp JSON: `{"id": mid, "method": method, "params": params}`.
- Lắng nghe qua socket cho đến khi nhận được thông điệp trả về có `msg["id"] == mid`.
- Được bao bọc bởi `threading.Lock()` để đảm bảo an toàn tuyệt đối khi nhiều luồng cùng gọi các lệnh CDP trên cùng một tab (Thread-safe).

### 2.3. Thực Thi JavaScript (`js`)
```python
js(expr: str, await_promise: bool = False, timeout: float | None = None) -> Any
```
- Gọi lệnh `Runtime.evaluate` với cờ `returnByValue: True` và `awaitPromise: await_promise`.
- Tự động bóc tách và trả về giá trị trực tiếp nằm trong `res["value"]` giúp mã nguồn tầng trên gọn gàng.

### 2.4. Lắng Nghe Sự Kiện (`pump`)
```python
pump(seconds: float, on_event=None, sock_timeout: float = 2.0)
```
- Lắng nghe liên tục trong `seconds` giây các sự kiện bất đồng bộ phát ra từ trình duyệt (như sự kiện `Network.responseReceived` hay `Page.loadEventFired`).

---

## 3. Hàm Bổ Trợ `http_json`

```python
http_json(url: str, timeout: float = 5.0) -> dict | list
```
- Helper nhanh dùng `requests.get` để lấy thông tin mục tiêu từ endpoint HTTP của Chromium (như `http://127.0.0.1:19210/json/version` hoặc `/json/new`).

---

## 4. Liên kết Liên quan

- [Tài liệu Chi tiết File cdp.py](../04-chi-tiet-ma-nguon/cdp-py.md)
- [Module Engine Core](engine-core.md)
- [Mục lục Tài liệu](../README.md)
