# API: Tạo Video Bất Đồng Bộ (`/v1/videos/*`)

---

## 1. Khởi Tạo Tác Vụ Sinh Video (`POST /v1/videos`)

Tạo nhiệm vụ sinh video và trả về ngay mã tác vụ `task_id` trong hàng đợi.

### 1.1. Request Body
```json
{
  "prompt": "Một chiếc xe thể thao màu đỏ chạy tốc độ cao trên đường cao tốc ven biển lúc hoàng hôn",
  "duration": 6,
  "aspect_ratio": "16:9",
  "images": [
    "https://example.com/first-frame.png"
  ]
}
```

- `prompt` *(string, bắt buộc)*: Mô tả hành động và bối cảnh video.
- `duration` *(integer, tùy chọn)*: Thời lượng mong muốn: `5`, `6`, `8`, hoặc `10` giây (kết quả thực tế phụ thuộc mô hình upstream muse.ai).
- `aspect_ratio` *(string, tùy chọn)*: Tỉ lệ khung hình: `"16:9"` (ngang) hoặc `"9:16"` (dọc cho TikTok / Shorts / Reels).
- `images` *(array, tùy chọn)*: Ảnh tham chiếu. Ảnh đầu tiên được dùng làm khung hình bắt đầu (First-frame Image-to-Video).

### 1.2. Response Body (HTTP 200)
```json
{
  "id": "task_9f8e7d6c5b4a3210fe",
  "object": "task",
  "kind": "video",
  "status": "queued",
  "created_at": 1740000000,
  "updated_at": 1740000000,
  "result": null,
  "error": null
}
```

---

## 2. Tra Cứu Trạng Thái & Lấy Video (`GET /v1/videos/{task_id}`)

Client định kỳ gửi request kiểm tra tiến độ của tác vụ.

### 2.1. Phản hồi khi tác vụ đang xử lý
```json
{
  "id": "task_9f8e7d6c5b4a3210fe",
  "object": "task",
  "kind": "video",
  "status": "processing",
  "progress": 75,
  "created_at": 1740000000,
  "updated_at": 1740000085,
  "result": null,
  "error": null
}
```

### 2.2. Phản hồi khi tác vụ đã hoàn thành
```json
{
  "id": "task_9f8e7d6c5b4a3210fe",
  "object": "task",
  "kind": "video",
  "status": "completed",
  "progress": 100,
  "created_at": 1740000000,
  "updated_at": 1740000180,
  "result": {
    "url": "http://127.0.0.1:18610/v1/media/d4c3b2a1f0e9.mp4",
    "filename": "d4c3b2a1f0e9.mp4",
    "size": 8452100,
    "ext": ".mp4",
    "mime": "video/mp4",
    "kind": "video"
  },
  "error": null
}
```

---

## 3. Lấy Tệp Đa Phương Tiện Trực Tiếp (`GET /v1/media/{filename}`)

Phục vụ phát trực tiếp hoặc tải tệp video MP4 / ảnh PNG:
```http
GET /v1/media/d4c3b2a1f0e9.mp4
```
Trả về stream nhị phân của tệp kèm header `Content-Type: video/mp4` và hỗ trợ tua video qua HTTP Range requests.

---

## 4. Liên kết Liên quan
- [Tổng Quan API](tong-quan-api.md)
- [Sơ Đồ Luồng Sinh Video](../05-luong-xu-ly/video-generation.md)
- [Mục lục Tài liệu](../README.md)
