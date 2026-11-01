# Công Nghệ Sử Dụng Trong MUSE2API

---

## 1. Ngôn Ngữ & Môi Trường Runtime

- **Python 3.10+ (Khuyến nghị 3.11 hoặc 3.12)**:
  - Sử dụng các tính năng hiện đại: Type Hinting nâng cao (`from __future__ import annotations`, kiểu `union` với toán tử `|`), `asyncio` cho các endpoint bất đồng bộ và tác vụ nền.
  - Tận dụng `threading.local()` để tách biệt trạng thái kết nối tab theo từng luồng làm việc.
- **JavaScript (ES6+)**:
  - Viết các đoạn mã JavaScript injection chạy trực tiếp trong ngữ cảnh trang web qua lệnh `Runtime.evaluate` của CDP.
  - Sử dụng các Web APIs tiêu chuẩn: `DataTransfer`, `Blob`, `File`, `atob`, `fetch`, `HTMLTextAreaElement.prototype`.
  - Mã nguồn cho Chrome Extension (Manifest V3) và Tampermonkey Userscript.
- **HTML5 & CSS3**:
  - Giao diện Admin Web Console (`admin.html`) sử dụng Single Page Application (SPA), tích hợp Tailwind CSS qua CDN và phông chữ tùy biến.

---

## 2. Frameworks & Thư Viện Phụ Thuộc (Dependencies)

Các thư viện chính được khai báo trong [requirements.txt](file:///e:/Project/muse2api/requirements.txt):

```text
fastapi>=0.115
uvicorn[standard]>=0.32
pydantic>=2.9
requests>=2.32
websocket-client>=1.8
python-multipart>=0.0.9
```

| Thư viện | Phiên bản tối thiểu | Mục đích sử dụng trong hệ thống |
| :--- | :--- | :--- |
| **`fastapi`** | `>= 0.115` | Framework Web hiệu năng cao, xây dựng RESTful API và cơ chế Dependency Injection (`Depends(auth)`). |
| **`uvicorn[standard]`** | `>= 0.32` | Máy chủ ASGI tiêu chuẩn công nghiệp hỗ trợ HTTP/1.1, WebSocket và EventLoop tốc độ cao (`uvloop`). |
| **`pydantic`** | `>= 2.9` | Xác thực dữ liệu đầu vào (Data Validation) và chuẩn hóa schema cho các Request/Response tương thích OpenAI. |
| **`requests`** | `>= 2.32` | Thực hiện các lệnh gọi HTTP đồng bộ tới API nội bộ `/api/session` và `/api/hatch/vm/wake` của muse.ai. |
| **`websocket-client`** | `>= 1.8` | Thiết lập kết nối hai chiều ổn định tới cổng gỡ lỗi từ xa của Chromium (CDP WebSocket Server). |
| **`python-multipart`** | `>= 0.0.9`| Hỗ trợ giải mã dữ liệu multipart/form-data cho endpoint upload ảnh chỉnh sửa `/v1/images/edits`. |

---

## 3. Trình Duyệt & Giao Thức Tự Động Hóa (Browser Automation Engine)

- **Chromium / Google Chrome**:
  - Chạy ở chế độ vô đầu mới: `--headless=new` (đảm bảo hiển thị đầy đủ layout và canvas chính xác như trình duyệt thật).
  - Cờ tối ưu hóa: `--no-sandbox`, `--disable-gpu`, `--disable-dev-shm-usage`, `--disable-background-networking`.
- **Chrome DevTools Protocol (CDP)**:
  - Điều khiển trình duyệt thông qua giao thức gỡ lỗi JSON-RPC qua WebSocket.
  - Các domain CDP chủ chốt được kích hoạt:
    - `Target`: Quản lý tạo/hủy Incognito BrowserContext (`Target.createBrowserContext`, `Target.disposeBrowserContext`).
    - `Network`: Xóa cookie (`clearBrowserCookies`), bơm cookie (`setCookie`), đọc cookie HttpOnly (`getCookies`).
    - `Page`: Điều hướng URL (`Page.navigate`), kích hoạt sự kiện tải trang.
    - `Runtime`: Thực thi mã JavaScript (`Runtime.evaluate`).
    - `Input`: Phát sự kiện chuột trái (`Input.dispatchMouseEvent`) và phím bấm (`Input.dispatchKeyEvent`).
    - `Browser`: Thiết lập thư mục tải xuống tự động (`Browser.setDownloadBehavior`).

---

## 4. Công Cụ Đóng Gói & Triển Khai (DevOps & Build Tools)

- **Docker**:
  - Image nền tảng sử dụng Linux Debian/Ubuntu (tích hợp sẵn Chromium, phông chữ `fonts-wqy-zenhei` hiển thị tiếng Trung/tiếng Việt và Python 3).
  - Tối ưu hóa kích thước image và thiết lập phân quyền an toàn.
- **Docker Compose**:
  - Quản lý khởi chạy dịch vụ chỉ bằng 1 lệnh `docker compose up -d`.
  - Thiết lập mount thư mục `data/` và file `.env` ra ngoài máy chủ vật lý để đảm bảo dữ liệu không bị mất khi cập nhật container.
- **Systemd & Nginx**:
  - Cung cấp sẵn file cấu hình dịch vụ chạy ngầm trên VPS Linux và mẫu cấu hình Nginx Reverse Proxy hỗ trợ chứng chỉ SSL (Let's Encrypt) và tắt đệm luồng (`proxy_buffering off`) cho Server-Sent Events.

---

## 5. Liên kết Liên quan

- [Giới thiệu Dự án](gioi-thieu.md)
- [Kiến trúc Tổng thể](kien-truc.md)
- [Hướng dẫn Cài đặt](../02-cai-dat/huong-dan-cai-dat.md)
- [Mục lục Tài liệu](../README.md)
