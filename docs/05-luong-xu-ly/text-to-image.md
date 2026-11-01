# Luồng Xử Lý: Văn Bản Sinh Hình Ảnh (`/v1/images/generations`)

---

## 1. Mô Tả Luồng Nghiệp Vụ

Endpoint `/v1/images/generations` tiếp nhận câu nhắc (prompt) và kích thước mong muốn (`1024x1024`, `1792x1024`, `1024x1792`...), sau đó:
1. Chuẩn hóa câu nhắc kèm tỉ lệ khung hình (`1:1`, `16:9`, `9:16`...).
2. Dọn dẹp các ảnh đính kèm cũ trong khung soạn thảo (`_clear_attachments`).
3. Gửi prompt lên muse.ai và chờ phần tử ảnh hoàn thiện xuất hiện.
4. Trích xuất dữ liệu ảnh nhị phân trực tiếp từ DOM qua JavaScript Blob Fetching.
5. Lưu tệp cục bộ và trả về URL hoặc chuỗi Base64 cho client.

---

## 2. Sơ Đồ Tuần Tự (Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    actor Client as Ứng dụng Khách
    participant API as app.py (/v1/images/generations)
    participant Lock as ConcurrencyLock
    participant Pool as AccountPoolManager
    participant Engine as engine.py (MuseEngine)
    participant CDP as Chromium CDP Tab
    participant Storage as Thư mục data/media/

    Client->>API: POST /v1/images/generations {prompt, size, response_format}
    API->>API: Xác thực API Key
    API->>API: build_image_prompt(prompt, size)
    API->>Lock: acquire() [Giữ slot nặng]
    API->>Pool: acquire()
    Pool-->>API: Gán tài khoản khả dụng

    API->>Engine: generate(cookies, prompt, expect='image')
    Engine->>CDP: reset_thread(for_chat=False)
    Engine->>CDP: _clear_attachments() [Xóa thumbnail cũ]
    Engine->>CDP: _send(prompt)

    loop Lắng nghe phần tử ảnh (_wait_attachment)
        Engine->>CDP: attachments() query DOM
        alt Phát hiện ảnh mới có w > 0, h > 0
            CDP-->>Engine: Trả về phần tử ảnh hoàn thiện
        else Model từ chối (Refusal Text)
            Engine-->>API: Ném MuseModelRefusalError
            API->>Pool: Xoay tua sang tài khoản khác (Refusal Rotation)
        end
    end

    Engine->>CDP: extract_bytes(src, expect='image')
    CDP-->>Engine: Trả mảng byte ảnh PNG/WebP
    Engine->>Storage: Ghi file UUID vào data/media/<name>.png
    Engine-->>API: Trả về metadata {path, filename, size, url}

    API->>Pool: release()
    API->>Lock: release()

    alt response_format == 'b64_json'
        API-->>Client: {"data": [{"b64_json": "..."}]}
    else response_format == 'url'
        API-->>Client: {"data": [{"url": "http://.../v1/media/<name>.png"}]}
    end
```

---

## 3. Liên kết Liên quan
- [Luồng Xử Lý Chỉnh Sửa Ảnh Tham Chiếu](image-to-image.md)
- [Chi Tiết API Images](../06-api/images-generations-edits.md)
- [Mục lục Tài liệu](../README.md)
