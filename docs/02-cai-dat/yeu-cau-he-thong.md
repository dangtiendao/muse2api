# Yêu Cầu Hệ Thống Cho MUSE2API

---

## 1. Cấu Hình Phần Cứng Tối Thiểu & Khuyến Nghị

Vì hệ thống vận hành một tiến trình trình duyệt Chromium vô đầu (Headless Browser) và quản lý nhiều tab làm việc đồng thời, yêu cầu tài nguyên phần cứng phụ thuộc vào tham số cấu hình số lượng tác vụ đồng thời (`MUSE2API_CONCURRENCY`).

| Thành phần | Cấu hình tối thiểu (1-2 Concurrency) | Cấu hình khuyến nghị (4+ Concurrency) |
| :--- | :--- | :--- |
| **CPU** | 2 Cores (x86_64 hoặc ARM64) | 4 Cores trở lên |
| **RAM** | 2.0 GB RAM (khuyến nghị có 2GB Swap) | 4.0 GB – 8.0 GB RAM |
| **Ổ cứng trống** | 10 GB SSD trống | 20 GB SSD trống (phục vụ lưu trữ tệp media MP4/WebP) |
| **Mạng Internet** | Tối thiểu 10 Mbps, IP sạch, truy cập ổn định tới `muse.ai` | 50+ Mbps, độ trễ thấp |

> [!IMPORTANT]
> Mỗi tab làm việc của Chromium tiêu tốn trung bình từ 150MB đến 350MB RAM. Nếu máy chủ có 1GB hoặc 2GB RAM, bắt buộc phải bật bộ nhớ ảo **Swap** tối thiểu 2GB để tránh bị hệ điều hành Linux kích hoạt OOM Killer (Out Of Memory) tắt tiến trình Chromium.

---

## 2. Hệ Điều Hành Được Hỗ Trợ

- **Linux (Khuyến nghị hàng đầu cho Production)**:
  - Ubuntu 20.04 LTS / 22.04 LTS / 24.04 LTS
  - Debian 11 / 12
  - CentOS Stream / AlmaLinux / Rocky Linux 9
- **Windows**:
  - Windows 10 / Windows 11 (64-bit)
  - Windows Server 2019 / 2022
- **macOS**:
  - macOS 12 Monterey trở lên (hỗ trợ cả Apple Silicon M-series và Intel).

---

## 3. Các Phần Mềm & Công Cụ Bắt Buộc Cần Cài Sẵn

1. **Python Runtime**:
   - Phiên bản: `Python 3.10` trở lên (Khuyến nghị Python 3.11 hoặc 3.12).
   - Đi kèm công cụ quản lý gói `pip` và module môi trường ảo `venv`.
2. **Trình duyệt Web (Browser Binary)**:
   - Một trong các trình duyệt: `Chromium`, `Google Chrome`, `Microsoft Edge`, hoặc `Brave`.
   - Đối với Linux: Phải cài đặt các gói thư viện đồ họa cơ bản của hệ thống và phông chữ Unicode (ví dụ: `fonts-wqy-zenhei` hoặc `fonts-noto-cjk`) để trình duyệt không bị lỗi font hoặc crash khi render canvas.
3. **Docker & Docker Compose (Tùy chọn nhưng khuyến nghị cao nhất)**:
   - Docker Engine phiên bản 24.0+
   - Docker Compose v2.0+

---

## 4. Kiểm Tra Mạng & Tường Lửa (Network Prerequisites)

- Máy chủ cần có khả năng kết nối mạng thông suốt (không bị chặn DNS hoặc chặn dải IP) tới các tên miền sau:
  - `https://muse.ai`
  - `https://*.muse.ai`
  - `https://api.mail.tm` (nếu sử dụng công cụ tạo email tự động `mailtm_otp.py`)
- Mở cổng kết nối mạng:
  - Cổng dịch vụ API mặc định: `18610` (có thể tùy chỉnh qua `MUSE2API_PORT`).
  - Cổng gỡ lỗi CDP nội bộ: `19210` (chỉ lắng nghe trên `127.0.0.1`, tuyệt đối không mở ra Internet).

---

## 5. Liên kết Liên quan

- [Hướng dẫn Cài đặt](huong-dan-cai-dat.md)
- [Giải thích Biến Môi trường & Cấu hình](cau-hinh.md)
- [Lệnh Chạy Dự Án](chay-du-an.md)
- [Mục lục Tài liệu](../README.md)
