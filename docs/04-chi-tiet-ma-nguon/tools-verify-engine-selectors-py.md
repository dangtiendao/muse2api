# Chi Tiết Mã Nguồn: `tools/verify_engine_selectors.py`

---

## 1. Thông Tin Cơ Bản
- **Đường dẫn file gốc**: [../../tools/verify_engine_selectors.py](../../tools/verify_engine_selectors.py)
- **Số dòng mã**: ~106 dòng.
- **Ngôn ngữ**: Python 3.10+.
- **Chức năng chính**: Script chẩn đoán và kiểm thử trực tiếp các bộ chọn DOM (CSS/XPath selectors) và đoạn mã JavaScript injection của `engine.py` trên trang muse.ai đang chạy thật.

---

## 2. Vai Trò Trong Hệ Thống
- **Thuộc tầng**: Công Cụ Chẩn Đoán & Kiểm Thử Nội Bộ (Diagnostic Tool).
- **Được gọi bởi**: Kỹ sư phát triển khi cần bảo trì hoặc gỡ lỗi selectors.
- **Gọi đến**: Cổng CDP của server muse2api (19210) và module `engine.MuseEngine`.

---

## 3. Danh Sách Hàm & Lớp Quan Trọng

| Tên | Chức năng chi tiết |
| :--- | :--- |
| `find_page_ws()` | Truy vấn `/json` trên cổng CDP để tìm tab đang mở tên miền `muse.ai`. |
| `FakeEngine` | Lớp giả lập nhỏ mượn trực tiếp các hàm `attachments` và `_clear_attachments` từ `engine.MuseEngine`. |
| `main()` | Điều phối kịch bản: in danh sách `button[aria-label]`, in attachments hiện có, thử nghiệm inject ảnh 1x1 PNG qua DataTransfer và kiểm tra sự xuất hiện của nút xóa đính kèm. |

---

## 4. Liên kết Liên quan
- [Module Tools](../03-module/tools-helpers.md)
- [Module Engine Core](../03-module/engine-core.md)
- [Mục lục Tài liệu](../README.md)
