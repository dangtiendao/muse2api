# Hướng Dẫn Kiểm Thử (Testing Guide)

---

## 1. Cơ Cấu Bộ Kiểm Thử (Test Suites)

Thư mục `tests/` chứa 18 bộ kiểm thử tự động bao quát toàn diện các khía cạnh kỹ thuật của hệ thống:

| File kiểm thử | Nội dung kiểm tra |
| :--- | :--- |
| `test_cookie_requirements.py` | Kiểm tra tính bắt buộc của 2 cookie cốt lõi `hatch_sess` và `hatch_vml`. |
| `test_ref_image_safety.py` | Kiểm tra cơ chế phòng vệ SSRF, DNS Rebinding và chặn IP nội bộ. |
| `test_reference_limits.py` | Kiểm tra các ngưỡng giới hạn (tối đa 4 ảnh, tối đa 10MB/ảnh, 24MB tổng). |
| `test_concurrency.py` | Kiểm tra khóa `ConcurrencyLock` và cơ chế điều phối `AccountPoolManager`. |
| `test_session_health.py` | Kiểm tra việc nhận diện phiên sống/chết và thời hạn tính toán. |
| `test_keepalive_scheduling.py`| Kiểm tra chu kỳ lập lịch heartbeat tự động của daemon ngầm. |
| `test_refusal_rotation.py` | Kiểm tra cơ chế tự động xoay sang tài khoản khác khi bị model từ chối. |
| `test_media_selection.py` | Kiểm tra thuật toán chọn lọc đúng tệp video/ảnh, tránh nhận nhầm ảnh bìa. |
| `test_media_delete.py` | Kiểm tra các API xóa file media trong kho. |
| `test_async_images.py` | Kiểm tra luồng xử lý sinh ảnh bất đồng bộ. |
| `test_quota_localization.py` | Kiểm tra bóc tách nội dung hiển thị quota đa ngôn ngữ (EN, ZH). |
| `test_admin_base_url.py` | Kiểm tra logic xác định URL công khai cho admin console. |
| `test_admin_api_error_messages.mjs`| Kiểm tra các thông điệp lỗi API Admin bằng Node.js. |

---

## 2. Cách Chạy Kiểm Thử Cục Bộ

### Chạy toàn bộ với Unittest:
```bash
python -m unittest discover tests
```

### Chạy một bài test cụ thể:
```bash
python -m unittest tests.test_ref_image_safety
```

### Chạy kiểm tra cú pháp toàn bộ file Python:
```bash
python -m py_compile app.py engine.py store.py cdp.py config.py tools/*.py
```

---

## 3. Quy Tắc Viết Test Mới

1. **Mocking kết nối mạng**: Sử dụng `unittest.mock` để giả lập các phản hồi của `requests.get` hoặc `requests.post` tới `muse.ai`, không phụ thuộc vào kết nối mạng thật khi chạy unit test.
2. **Dọn dẹp môi trường**: Mọi bài test tạo file tạm hoặc sửa đổi biến môi trường phải có phương thức `tearDown()` để dọn dẹp sạch sẽ sau khi chạy xong.

---

## 4. Liên kết Liên quan
- [Quy Chuẩn Lập Trình](coding-convention.md)
- [Quy Trình Đóng Góp](quy-trinh-dong-gop.md)
- [Mục lục Tài liệu](../README.md)
