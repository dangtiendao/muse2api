# Chi Tiết Mã Nguồn: `app.py`

---

## 1. Thông Tin Cơ Bản
- **Đường dẫn file gốc**: [../../app.py](../../app.py)
- **Số dòng mã**: ~2552 dòng.
- **Ngôn ngữ**: Python 3.10+.
- **Chức năng chính**: Điểm vào ứng dụng (Entry Point), khởi tạo máy chủ FastAPI, cung cấp toàn bộ RESTful API tương thích OpenAI (`/v1/chat/completions`, `/v1/responses`, `/v1/images/*`, `/v1/videos/*`), hệ thống quản trị tài khoản Admin, điều phối concurrency và luồng daemon bảo hoạt.

---

## 2. Vai Trò Trong Hệ Thống
- **Thuộc tầng**: Tầng Trình diễn và Điều khiển (Presentation & Controller Layer).
- **Được gọi bởi**:
  - Máy chủ ASGI (Uvicorn / Docker container).
  - Client bên ngoài (NextChat, LobeChat, OpenAI SDK, ứng dụng người dùng).
  - Quản trị viên thông qua giao diện Web Console (`admin.html`).
- **Gọi đến**:
  - `config.CFG`: Nạp cấu hình runtime.
  - `store.Store`: Truy xuất và lưu trữ tài khoản, nhiệm vụ.
  - `engine.MuseEngine`: Khởi động Chromium, mở tab, điều khiển sinh ảnh, video và stream chat.

---

## 3. Luồng Xử Lý Dữ Liệu (Data Flow)

```text
HTTP Request (Client)
  ↓
FastAPI Router & Dependency `auth()` (Xác thực Bearer API Key)
  ↓
Kiểm soát đồng thời qua `ConcurrencyLock` (Semaphore slot)
  ↓
Thuê tài khoản qua `AccountPoolManager.acquire()`
  ↓
Gọi `engine.generate()` hoặc `engine.chat_stream()`
  ↓
Trích xuất dữ liệu hoàn thiện (Base64 / URL / SSE Chunks)
  ↓
Giải phóng tài khoản qua `AccountPoolManager.release()` & cập nhật cookie mới vào `Store`
  ↓
HTTP Response (Chuẩn OpenAI JSON hoặc SSE Stream)
```

---

## 4. Danh Sách Các Lớp & Hàm Quan Trọng

| Tên lớp / hàm | Chức năng chi tiết |
| :--- | :--- |
| `ConcurrencyLock` | Bộ khóa giới hạn số luồng đồng thời dựa trên `threading.Semaphore`. |
| `AccountPoolManager` | Bộ quản lý cấp phát tài khoản thông minh, đảm bảo nguyên tắc 1 tài khoản chỉ phục vụ 1 tác vụ tại 1 thời điểm. |
| `auth` | Dependency kiểm tra API Key từ header `Authorization: Bearer <KEY>`. |
| `build_chat_prompt` | Gộp ngữ cảnh đa lượt (multi-turn messages) thành câu nhắc gửi lên muse.ai. |
| `build_image_prompt` | Bổ sung chỉ thị tỉ lệ khung hình (`size`) vào nội dung câu lệnh. |
| `build_video_prompt` | Thêm tham số thời lượng (`duration`) và tỉ lệ dọc/ngang vào câu lệnh sinh video. |
| `_run_generation_locked` | Hàm bao bọc thực thi sinh ảnh/video với đầy đủ cơ chế khóa, thuê tài khoản và tự động đổi tài khoản nếu gặp lỗi từ chối (Refusal Rotation). |
| `chat_completions` | Handler cho endpoint `/v1/chat/completions`, hỗ trợ cả đồng bộ và SSE Stream. |
| `images_generations` | Handler cho endpoint `/v1/images/generations` (Text-to-Image). |
| `images_edits` | Handler cho endpoint `/v1/images/edits` (Image-to-Image / Tham chiếu đa ảnh). |
| `create_video` / `get_video` | Handlers cho endpoint tạo và tra cứu tác vụ sinh video bất đồng bộ. |
| `_probe_account_sync` | Hàm ngầm kiểm tra sức khỏe tài khoản, gia hạn session qua HTTP và wake VM. |

---

## 5. Phụ Thuộc (Dependencies)
- **Thư viện bên ngoài**: `fastapi`, `pydantic`, `uvicorn`, `requests`, `python-multipart`.
- **Module nội bộ**: `config`, `engine`, `store`.

---

## 6. Lưu Ý Kỹ Thuật & Rủi Ro Tiềm Ẩn
1. **Quản lý RAM**: Mỗi tác vụ đồng thời kích hoạt một tab Chromium Incognito. Nếu đặt `MUSE2API_CONCURRENCY` quá cao trên máy chủ ít RAM, có thể gây tràn bộ nhớ.
2. **Khối lượng File Tasks**: Hàm `_write()` trong store ghi toàn bộ file JSON mỗi khi cập nhật trạng thái nhiệm vụ, nên định kỳ gọi API xóa task cũ.

---

## 7. Liên kết Liên quan
- [Module App API](../03-module/app-api.md)
- [Tài liệu API Chi tiết](../06-api/tong-quan-api.md)
- [Mục lục Tài liệu](../README.md)
