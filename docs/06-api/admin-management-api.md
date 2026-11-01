# API: Quản Trị Hệ Thống & Hồ Chứa Tài Khoản (`/admin/*`)

---

## 1. Tổng Quan Nhóm API Quản Trị

Các API này phục vụ cho việc vận hành, tích hợp dashboard và quản lý hồ chứa tài khoản. Toàn bộ các endpoint này yêu cầu xác thực bằng `MUSE2API_KEY`.

---

## 2. Bảng Danh Sách Endpoints Quản Trị

| Phương thức | Endpoint | Chức năng |
| :--- | :--- | :--- |
| **`GET`** | `/admin/status` | Thống kê số lượng tài khoản, tỉ lệ lỗi, hạn mức và trạng thái tiến trình Chromium. |
| **`GET`** | `/admin/accounts` | Liệt kê danh sách tất cả tài khoản trong hồ chứa (đã loại bỏ trường `cookies` bảo mật). |
| **`POST`** | `/admin/accounts` | Nhập tài khoản mới (hỗ trợ nhập đơn, nhập chuỗi text hoặc mảng JSON). |
| **`PATCH`**| `/admin/accounts/{aid}` | Cập nhật nhãn (`label`) hoặc kích hoạt/vô hiệu hóa (`enabled: true/false`). |
| **`DELETE`**| `/admin/accounts/{aid}` | Xóa vĩnh viễn một tài khoản khỏi hồ chứa. |
| **`POST`** | `/admin/accounts/{aid}/test` | Mở tab thật kiểm tra phiên làm việc của tài khoản có hoạt động không. |
| **`POST`** | `/admin/accounts/{aid}/quota`| Tra cứu hạn mức sử dụng gói cước hàng tuần của tài khoản chỉ định. |
| **`POST`** | `/admin/accounts/keepalive` | Kích hoạt ngay lập tức tiến trình gia hạn cookie và đánh thức VM cho toàn bộ tài khoản. |
| **`GET`** | `/admin/keepalive/status` | Xem kết quả và thời gian lần chạy bảo hoạt gần nhất. |
| **`GET`** | `/admin/media` | Liệt kê danh sách các tệp hình ảnh và video đã tạo được lưu trong thư mục `data/media/`. |
| **`POST`** | `/admin/media/delete` | Xóa hàng loạt tệp media được chọn. |
| **`GET`** | `/admin/extension` | Tải về tệp nén zip chứa tiện ích Chrome Extension. |
| **`GET`** | `/admin/repo/status` | Kiểm tra xem kho GitHub có phiên bản phát hành mới hơn không. |
| **`POST`** | `/admin/repo/pull` | Thực hiện kéo mã nguồn mới nhất từ GitHub và tự động khởi động lại server. |

---

## 3. Chi Tiết Một Số Request Điển Hình

### 3.1. Nhập tài khoản mới (`POST /admin/accounts`)
```json
{
  "label": "tai-khoan-vip-01",
  "cookies": {
    "hatch_sess": "eyJhbGciOi...",
    "hatch_vml": "abc123vml..."
  },
  "expires": {
    "hatch_vml": 1740200000
  }
}
```

### 3.2. Cập nhật trạng thái tài khoản (`PATCH /admin/accounts/{aid}`)
```json
{
  "enabled": false,
  "label": "Tài khoản tạm khóa"
}
```

---

## 4. Liên kết Liên quan
- [Tổng Quan API](tong-quan-api.md)
- [Sơ Đồ Đồng Bộ Cookie](../05-luong-xu-ly/cookie-import.md)
- [Mục lục Tài liệu](../README.md)
