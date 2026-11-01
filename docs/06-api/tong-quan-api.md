# Tổng Quan Giao Diện Lập Trình Ứng Dụng (API Reference)

---

## 1. Chuẩn Thiết Kế & Địa Chỉ Gốc (Base URL)

Mọi API của **MUSE2API** đều tuân thủ chuẩn RESTful và tương thích hoàn toàn với định dạng OpenAI API specification:
- **Địa chỉ dịch vụ cục bộ**: `http://127.0.0.1:18610`
- **Địa chỉ OpenAI Base**: `http://127.0.0.1:18610/v1`
- **Định dạng dữ liệu**: `application/json` (ngoại trừ endpoint `/v1/images/edits` hỗ trợ thêm `multipart/form-data`).
- **Bộ mã hóa ký tự**: `UTF-8`.

---

## 2. Xác Thực Truy Cập (Authentication)

Nếu hệ thống đã thiết lập biến môi trường `MUSE2API_KEY` khác rỗng, tất cả các yêu cầu API (bao gồm cả `/v1/*` và `/admin/*`) đều phải gửi kèm HTTP Header:

```http
Authorization: Bearer <MUSE2API_KEY>
```

Nếu không truyền hoặc truyền sai API key, máy chủ sẽ phản hồi mã lỗi `HTTP 401 Unauthorized`.

---

## 3. Bảng Mã Lỗi Chuẩn (HTTP Status Codes)

| Mã lỗi HTTP | Ý nghĩa | Nguyên nhân thường gặp |
| :--- | :--- | :--- |
| **`200 OK`** | Thành công | Yêu cầu được thực thi và trả về kết quả hợp lệ. |
| **`400 Bad Request`** | Dữ liệu không hợp lệ | Thiếu tham số bắt buộc, sai định dạng cookie hoặc URL ảnh không đúng. |
| **`401 Unauthorized`** | Không có quyền | Thiếu hoặc sai API Key trong header `Authorization`. |
| **`404 Not Found`** | Không tìm thấy | Task ID hoặc tên file media không tồn tại. |
| **`422 Unprocessable`** | Lỗi Schema Pydantic | Dữ liệu JSON không khớp với schema định nghĩa. |
| **`500 Internal Error`** | Lỗi máy chủ / Engine | Lỗi trong quá trình điều khiển trình duyệt hoặc muse.ai phản hồi bất thường. |
| **`503 Service Unavailable`** | Hết tài nguyên | Không còn tài khoản rảnh rỗi hoặc toàn bộ tài khoản trong hồ chứa đều gặp sự cố. |

---

## 4. Danh Sách Nhóm API

- [Hội thoại Trò chuyện (`/v1/chat/completions`)](chat-completions.md)
- [Hội thoại Chuẩn Codex (`/v1/responses`)](responses-codex.md)
- [Tạo & Chỉnh Sửa Hình Ảnh (`/v1/images/*`)](images-generations-edits.md)
- [Tạo Video Bất Đồng Bộ (`/v1/videos/*`)](videos-generations.md)
- [Quản Trị Hồ Chứa Tài Khoản & Hệ Thống (`/admin/*`)](admin-management-api.md)

---

## 5. Liên kết Liên quan
- [Mục lục Tài liệu](../README.md)
