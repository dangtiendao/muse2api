# Cấu Hình & Biến Môi Trường (Environment Variables)

---

## 1. Cơ Chế Nạp Cấu Hình

Hệ thống quản lý cấu hình thông qua module [config.py](file:///e:/Project/muse2api/config.py):
1. Tự động đọc file `.env` tại thư mục gốc dự án khi khởi động.
2. Không ghi đè các biến môi trường đã tồn tại trong hệ thống (System Environment Variables).
3. Hỗ trợ fallback về các giá trị mặc định hợp lý nếu biến chưa được định nghĩa.

---

## 2. Bảng Danh Mục Các Biến Môi Trường

| Tên biến môi trường | Giá trị mặc định | Giải thích chi tiết & Khuyến nghị |
| :--- | :--- | :--- |
| **`MUSE2API_KEY`** | `""` (Rỗng) | Khóa API Key bảo mật dịch vụ. Bắt buộc nên đặt chuỗi bí mật ngẫu nhiên (ví dụ `m2a_secr3t_123`). Khi đặt giá trị này, mọi request tới `/v1/*` và `/admin/*` đều phải mang header `Authorization: Bearer <KEY>`. |
| **`MUSE2API_HOST`** | `"0.0.0.0"` | Địa chỉ IP máy chủ lắng nghe. `0.0.0.0` cho phép truy cập từ mọi mạng bên ngoài; đặt `127.0.0.1` nếu chỉ dùng nội bộ hoặc đứng sau Nginx. |
| **`MUSE2API_PORT`** | `18610` | Cổng mạng TCP mà FastAPI máy chủ lắng nghe. |
| **`MUSE2API_PUBLIC_BASE`** | `""` | Địa chỉ công khai bên ngoài (ví dụ `https://api.yourdomain.com`). Dùng để hiển thị trong mục "Địa chỉ kết nối" trên bảng điều khiển Admin; nếu bỏ trống, trang sẽ dùng domain hiện tại. |
| **`MUSE2API_CHROMIUM`** | `""` (Tự động dò) | Đường dẫn tuyệt đối tới file thực thi Chromium/Chrome. Bỏ trống để hệ thống tự động dò tìm trong danh sách đường dẫn phổ biến. |
| **`MUSE2API_CDP_PORT`** | `19210` | Cổng kết nối gỡ lỗi từ xa (Remote Debugging Port) của Chromium. Chỉ chạy nội bộ trên localhost `127.0.0.1`. |
| **`MUSE2API_CONCURRENCY`** | `2` | Số lượng tác vụ nặng (sinh ảnh, sinh video, CDP) tối đa được phép chạy đồng thời. Máy chủ RAM 2GB nên để 2; RAM 4GB có thể nâng lên 4; RAM 8GB có thể nâng lên 6-8. |
| **`MUSE2API_IMAGE_TIMEOUT`** | `240` | Thời gian timeout tối đa cho một tác vụ sinh hình ảnh (tính theo giây). Mặc định 4 phút. |
| **`MUSE2API_VIDEO_TIMEOUT`** | `600` | Thời gian timeout tối đa cho một tác vụ sinh video (tính theo giây). Mặc định 10 phút. |
| **`MUSE2API_CHAT_TIMEOUT`** | `300` | Thời gian timeout tối đa cho một phiên hội thoại chat (tính theo giây). Mặc định 5 phút. |
| **`MUSE2API_LOGIN_WAIT`** | `60` | Thời gian chờ tối đa khi tải tab mới và kết nối WebSocket trên muse.ai (giây). |
| **`MUSE2API_PROFILE_ROOT`** | `~/muse2api-profiles` | Thư mục gốc lưu trữ User Data Profile của trình duyệt. **Lưu ý**: Trên Linux Snap, bắt buộc phải nằm trong `$HOME`. |
| **`MUSE2API_CORS_ORIGINS`** | `https://muse.ai,https://www.muse.ai` | Danh sách các nguồn tên miền cho phép gọi API CORS (phục vụ Tampermonkey script gửi cookie từ web muse.ai). |
| **`MUSE2API_REF_IMAGE_LOCAL_FILES`** | `0` (Tắt) | Cờ an toàn bảo mật: Có cho phép tham chiếu đường dẫn file cục bộ trên máy chủ làm ảnh đầu vào hay không (`1` là bật). Mặc định tắt để chống Local File Inclusion (LFI). |
| **`MUSE2API_REF_IMAGE_PRIVATE_FETCH`**| `0` (Tắt) | Cờ an toàn bảo mật: Có cho phép tải ảnh từ các dải IP nội bộ/riêng tư (127.0.0.1, 10.x, 192.168.x) hay không (`1` là bật). Mặc định tắt để chống SSRF. |
| **`MUSE2API_TOOL_PROTOCOL`** | `0` (Tắt) | Có tiêm prompt ép mô hình sinh cấu trúc Function Calling / Tool Call giả lập hay không. Mặc định tắt vì muse.ai sẽ từ chối trả lời nếu bị ép định dạng JSON tool call. |
| **`MUSE2API_KEEPALIVE_DISABLED_ACCOUNTS`** | `0` (Tắt) | Có duy trì phiên và đánh thức VM cho các tài khoản đang bị tắt (disabled) hay không. Bật (`1`) giúp tài khoản lưu kho không bị hết hạn cookie. |

---

## 3. Ví Dụ File `.env` Hoàn Chỉnh Cho Triển Khai Production

```ini
# ==========================================
# CẤU HÌNH BẢO MẬT & MẠNG
# ==========================================
MUSE2API_KEY=m2a_k9x8y7z6w5v4u3t2s1
MUSE2API_HOST=0.0.0.0
MUSE2API_PORT=18610
MUSE2API_PUBLIC_BASE=https://api.yourdomain.com

# ==========================================
# CẤU HÌNH HIỆU NĂNG & ĐỒNG THỜI
# ==========================================
MUSE2API_CONCURRENCY=4
MUSE2API_IMAGE_TIMEOUT=240
MUSE2API_VIDEO_TIMEOUT=600
MUSE2API_CHAT_TIMEOUT=300

# ==========================================
# CẤU HÌNH TRÌNH DUYỆT & BẢO HOẠT
# ==========================================
MUSE2API_CDP_PORT=19210
MUSE2API_KEEPALIVE_DISABLED_ACCOUNTS=1
```

---

## 4. Liên kết Liên quan

- [Yêu Cầu Hệ Thống](yeu-cau-he-thong.md)
- [Hướng Dẫn Cài Đặt](huong-dan-cai-dat.md)
- [Lệnh Chạy Dự Án](chay-du-an.md)
- [Mục lục Tài liệu](../README.md)
