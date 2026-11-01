# API: Tạo & Chỉnh Sửa Hình Ảnh (`/v1/images/*`)

---

## 1. Tạo Ảnh Từ Văn Bản (`POST /v1/images/generations`)

### 1.1. Request Body
```json
{
  "prompt": "Một chú mèo phi hành gia bay trong vũ trụ, phong cách cyberpunk rực rỡ, độ phân giải 8k",
  "n": 1,
  "size": "1792x1024",
  "response_format": "url"
}
```

- `prompt` *(string, bắt buộc)*: Mô tả hình ảnh cần tạo.
- `size` *(string, tùy chọn)*: Kích thước mong muốn: `1024x1024` (1:1), `1792x1024` (16:9), `1024x1792` (9:16), `1024x768` (4:3), `768x1024` (3:4).
- `response_format` *(string, tùy chọn)*: `url` (mặc định) hoặc `b64_json`.

### 1.2. Response Body
```json
{
  "created": 1740000000,
  "data": [
    {
      "url": "http://127.0.0.1:18610/v1/media/a1b2c3d4e5f6.png"
    }
  ]
}
```

---

## 2. Chỉnh Sửa & Tham Chiếu Hình Ảnh (`POST /v1/images/edits`)

Hỗ trợ 2 hình thức truyền dữ liệu: `multipart/form-data` (theo chuẩn OpenAI) hoặc `application/json`.

### 2.1. Request dạng `multipart/form-data`
- `image`: Tệp ảnh nhị phân (.png, .jpg, .webp).
- `prompt`: Câu lệnh chỉ đạo chỉnh sửa.
- `size`: Kích thước xuất bản.

### 2.2. Request dạng `application/json` (Hỗ trợ đa ảnh tham chiếu)
```json
{
  "prompt": "Biến nhân vật trong ảnh thành phong cách anime Nhật Bản thời kỳ Edo",
  "image": "https://example.com/character.png",
  "images": [
    "data:image/png;base64,iVBORw0KGgo...",
    "https://example.com/style-reference.png"
  ],
  "size": "1024x1024",
  "response_format": "b64_json"
}
```

### 2.3. Response Body
```json
{
  "created": 1740000000,
  "data": [
    {
      "b64_json": "iVBORw0KGgoAAAANSUhEUgAA..."
    }
  ]
}
```

---

## 3. Liên kết Liên quan
- [Tổng Quan API](tong-quan-api.md)
- [Sơ Đồ Luồng Sinh Ảnh](../05-luong-xu-ly/text-to-image.md)
- [Sơ Đồ Luồng Sửa Ảnh](../05-luong-xu-ly/image-to-image.md)
- [Mục lục Tài liệu](../README.md)
