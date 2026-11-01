# Luồng Xử Lý: Sinh Video Bất Đồng Bộ (`/v1/videos`)

---

## 1. Mô Tả Luồng Nghiệp Vụ

Thời gian tạo một video chất lượng cao từ muse.ai thường mất từ 1 đến 5 phút. Để tránh tình trạng client bị HTTP Timeout khi giữ kết nối lâu, hệ thống triển khai kiến trúc **Tác vụ Hàng đợi Bất đồng bộ (Async Task Architecture)**:
1. **Khởi tạo tác vụ (`POST /v1/videos`)**: Nhận câu lệnh, tạo một bản ghi `task_id` với trạng thái `queued` và trả về ngay mã nhiệm vụ cho client trong vòng 0.2 giây.
2. **Xử lý ngầm (Background Worker)**: Một tiểu trình ngầm sẽ thực thi tác vụ qua `_run_generation_locked`: nạp ảnh bắt đầu (nếu có), gửi prompt và đợi container video render xong.
3. **Truy vấn trạng thái (`GET /v1/videos/{task_id}`)**: Client định kỳ polling mỗi vài giây để nhận tiến độ phần trăm và lấy link xem video khi hoàn tất.

---

## 2. Sơ Đồ Tuần Tự (Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    actor Client as Ứng dụng Khách
    participant API as app.py
    participant Store as store.py (tasks.json)
    participant Worker as Tiểu trình Xử lý Ngầm
    participant Engine as engine.py (MuseEngine)
    participant CDP as Chromium CDP Tab
    participant MediaFS as data/media/

    Client->>API: POST /v1/videos {prompt, duration: 6, aspect_ratio: '16:9'}
    API->>Store: create_task('video', prompt)
    Store-->>API: Trả về task_id (vd: task_abc123)
    API-->>Client: HTTP 200 {"id": "task_abc123", "status": "queued"}

    API-)Worker: Kích hoạt tiểu trình chạy ngầm (Background Task)
    Worker->>Store: update_task(task_id, status='processing')

    Worker->>Engine: generate(expect='video', timeout=600)
    Engine->>CDP: _send(prompt)
    
    loop Chờ video render (tối đa 10 phút)
        Engine->>CDP: attachments()
        CDP-->>Engine: Kiểm tra thẻ <video> hoặc vSrc
        Engine->>Store: update_task(task_id, progress=current_pct)
    end

    Engine->>CDP: extract_bytes(selected_src, expect='video')
    CDP-->>Engine: Dữ liệu nhị phân MP4
    Engine->>MediaFS: Lưu file vào data/media/<uuid>.mp4
    Worker->>Store: update_task(task_id, status='completed', result={url: '...'})

    loop Client Polling trạng thái
        Client->>API: GET /v1/videos/task_abc123
        API->>Store: get_task(task_abc123)
        alt Đang xử lý
            Store-->>API: {"status": "processing", "progress": 65}
            API-->>Client: {"status": "processing", "progress": 65}
        else Đã hoàn tất
            Store-->>API: {"status": "completed", "result": {"url": "http://.../media/xyz.mp4"}}
            API-->>Client: HTTP 200 {"status": "completed", "result": {"url": "..."}}
        end
    end
```

---

## 3. Liên kết Liên quan
- [Chi Tiết API Video](../06-api/videos-generations.md)
- [Module Engine Core](../03-module/engine-core.md)
- [Mục lục Tài liệu](../README.md)
