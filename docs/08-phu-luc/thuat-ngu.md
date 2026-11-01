# Bảng Thuật Ngữ (Glossary)

---

## 1. Danh Mục Thuật Ngữ Kỹ Thuật

| Thuật ngữ | Tên tiếng Anh đầy đủ | Giải thích trong ngữ cảnh dự án |
| :--- | :--- | :--- |
| **CDP** | Chrome DevTools Protocol | Giao thức truyền thông hai chiều dựa trên JSON-RPC qua WebSocket, cho phép điều khiển trực tiếp trình duyệt Chromium từ bên ngoài. |
| **Headless Browser** | Headless Chromium | Phiên bản trình duyệt chạy nền không cần hiển thị giao diện đồ họa (GUI), tối ưu hóa tài nguyên cho môi trường máy chủ. |
| **Incognito Context** | BrowserContext (CDP) | Một phiên làm việc ẩn danh độc lập trong Chromium. Cookie, bộ nhớ đệm và session của mỗi context hoàn toàn cách ly với nhau. |
| **SSE** | Server-Sent Events | Giao thức truyền dữ liệu một chiều từ máy chủ về máy khách qua kết nối HTTP duy nhất, dùng để tạo hiệu ứng gõ chữ (打字机 streaming) trong hội thoại AI. |
| **TTFT** | Time To First Token | Thời gian tính từ khi client gửi yêu cầu cho tới khi nhận được token chữ đầu tiên. muse2api tối ưu chỉ còn 2-3s. |
| **Warm-Tab Affinity** | Warm-Tab Sticky Affinity | Cơ chế ưu tiên tái sử dụng tab trình duyệt đã kết nối sẵn WebSocket với muse.ai thay vì mở tab mới mỗi lượt, giúp giảm độ trễ từ 10s xuống 2s. |
| **Keepalive** | Heartbeat Keepalive | Quá trình gửi yêu cầu định kỳ lên máy chủ upstream để gia hạn cookie phiên và giữ cho máy ảo đám mây không bị rơi vào trạng thái ngủ đông. |
| **LRU** | Least Recently Used | Thuật toán cân bằng tải: ưu tiên chọn tài khoản đã lâu chưa được sử dụng nhất và có số lần gọi ít nhất để tiêu thụ đều quota. |
| **SSRF** | Server-Side Request Forgery | Lỗ hổng bảo mật khi máy chủ bị lừa gửi yêu cầu đến các địa chỉ mạng nội bộ. muse2api ngăn chặn bằng cơ chế kiểm duyệt IP và chống DNS Rebinding. |
| **DNS Rebinding** | DNS Rebinding Attack | Kỹ thuật tấn công vượt qua bộ lọc IP bằng cách trả về IP công khai ở lần phân giải đầu và đổi sang IP nội bộ ở các lần chuyển hướng tiếp theo. |
| **Refusal** | Model Refusal | Tình huống mô hình AI từ chối thực hiện yêu cầu (do vi phạm chính sách nội dung) và trả về văn bản thay vì hình ảnh/video. |
| **hatch_sess** | Session Cookie | Cookie phiên chính của muse.ai (thời hạn ~30 ngày). |
| **hatch_vml** | VM Lease Cookie | Cookie cấp quyền máy ảo của muse.ai (thời hạn cố định ~48 giờ, quyết định sự sống còn của tài khoản). |

---

## 2. Liên kết Liên quan
- [Câu Hỏi Thường Gặp](faq.md)
- [Đề Xuất Cải Tiến](de-xuat-cai-tien.md)
- [Mục lục Tài liệu](../README.md)
