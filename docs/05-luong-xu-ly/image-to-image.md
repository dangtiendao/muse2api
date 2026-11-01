# Luồng Xử Lý: Chỉnh Sửa Ảnh Tham Chiếu (`/v1/images/edits`)

---

## 1. Mô Tả Luồng Nghiệp Vụ

Endpoint `/v1/images/edits` hỗ trợ tiếp nhận hình ảnh tham chiếu (Single-reference hoặc Multi-reference lên tới 4 ảnh) qua Multipart Form Data hoặc JSON Base64/URL, sau đó:
1. Thẩm định an toàn nguồn ảnh (chặn IP private / SSRF).
2. Chuẩn hóa ảnh về chuỗi Base64 và MIME type.
3. Bơm các file ảnh vào phần tử `input[type="file"]` của composer trên muse.ai qua JavaScript DataTransfer API.
4. Chờ giao diện hiển thị nút "Remove attachment / 移除附件" để đảm bảo upload đã thành công trước khi gửi lệnh.
5. Gửi câu nhắc chỉnh sửa và đón nhận hình ảnh kết quả mới sinh (loại trừ các thumbnail ảnh gốc đã upload).

---

## 2. Sơ Đồ Tuần Tự (Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    actor Client as Ứng dụng Khách
    participant API as app.py (/v1/images/edits)
    participant Safety as engine._normalize_image
    participant Engine as engine.py (MuseEngine)
    participant CDP as Chromium CDP Tab
    participant Storage as data/media/

    Client->>API: POST /v1/images/edits {image, prompt, size}
    API->>Safety: Chuẩn hóa và kiểm duyệt an toàn SSRF
    Safety-->>API: Trả về Base64 và MIME an toàn

    API->>Engine: generate(cookies, prompt, reference_images=[...])
    Engine->>CDP: _attach_images(images)
    CDP->>CDP: Tạo Blob -> File -> DataTransfer -> input.files
    CDP->>CDP: Dispatch event 'change' & 'input'
    
    loop Chờ xác nhận upload (tối đa 6s)
        CDP->>CDP: Đếm số lượng nút [aria-label*="Remove attachment"]
    end

    Engine->>CDP: _send(prompt)
    Engine->>CDP: _wait_attachment(baseline_src)
    CDP-->>Engine: Nhận diện ảnh mới (khác ảnh thumbnail upload)
    Engine->>CDP: extract_bytes(selected_src)
    CDP-->>Engine: Mảng byte kết quả
    Engine->>Storage: Lưu file ảnh thành phẩm
    Engine-->>API: Metadata ảnh thành phẩm
    API-->>Client: Trả về URL hoặc b64_json của ảnh mới tạo
```

---

## 3. Liên kết Liên quan
- [Luồng Xử Lý Văn Bản Sinh Ảnh](text-to-image.md)
- [Chi Tiết API Images](../06-api/images-generations-edits.md)
- [Mục lục Tài liệu](../README.md)
