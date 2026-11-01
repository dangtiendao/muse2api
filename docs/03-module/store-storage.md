# Module Lưu Trữ & Hồ Chứa Tài Khoản (`store.py`)

---

## 1. Tổng Quan Module

- **File nguồn**: [store.py](file:///e:/Project/muse2api/store.py)
- **Vai trò**: Quản lý hồ chứa tài khoản (Account Pool), lưu trữ trạng thái phiên làm việc, tính toán chính xác thời hạn sống của cookie và lưu trữ hàng đợi nhiệm vụ bất đồng bộ.
- **Tập tin dữ liệu quản lý**:
  - `data/accounts.json`: Danh sách tài khoản, cookies, trạng thái kích hoạt, thời gian sử dụng gần nhất.
  - `data/tasks.json`: Danh sách các nhiệm vụ sinh ảnh, video bất đồng bộ.

---

## 2. Các Quy Tắc & Thuật Toán Trọng Yếu

### 2.1. Xác Định Hạn Dùng Tài Khoản (`account_expiry`)
Cookie quyết định sự sống còn của tài khoản muse.ai là `hatch_vml`:
- Thời hạn sống cố định khoảng **2 ngày (48 giờ)** và không tự động tăng thêm nếu chỉ sử dụng thông thường.
- Thứ tự ưu tiên xác định hạn dùng:
  1. Đọc thuộc tính `expires` thực tế của `hatch_vml` (chính xác nhất).
  2. Nếu không đọc được: Ước lượng bằng `base_ts` (thời điểm import/đồng bộ) + `VML_TTL` (2 ngày).
  3. Fallback: Lấy thời gian hết hạn sớm nhất trong toàn bộ cookie (`min_expiry`).

### 2.2. Thuật Toán Điều Phối Tài Khoản (`pick_account`)
Kết hợp giữa hai chiến lược: **Warm-Tab Sticky Affinity** và **LRU Balancing**:
1. **Lọc tài khoản khả dụng**: Chỉ lấy tài khoản đang bật (`enabled=True`), có cookie và không nằm trong danh sách đang bị khóa bởi các luồng khác (`exclude_ids`).
2. **Tái sử dụng tab ấm (Sticky Affinity)**: Nếu truyền `preferred_id` và tài khoản này vẫn khỏe, hệ thống ưu tiên tiếp tục dùng tài khoản này tối đa **15 lần liên tiếp**. Điều này giúp tận dụng tab WebSocket đang mở, đạt tốc độ phản hồi 2s mà không mất thời gian reload.
3. **Cân bằng tải xoay tua (LRU Balancing)**: Khi đạt mốc 15 lần hoặc khi gặp lỗi, hệ thống sắp xếp các tài khoản khỏe theo thứ tự ưu tiên:
   - `last_used` nhỏ nhất (lâu nhất chưa dùng).
   - `use_count` nhỏ nhất (số lần gọi ít nhất).
   Đảm bảo toàn bộ tài khoản trong hồ chứa được tiêu thụ hạn mức đồng đều.

### 2.3. Cơ Chế Ghi File Nguyên Tử (Atomic File Writing)
Để ngăn ngừa tình trạng hỏng file JSON khi máy chủ mất điện hoặc bị tắt đột ngột:
```python
def _write(path: str, obj):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
        os.replace(tmp, path)  # Ghi đè nguyên tử ở cấp hệ điều hành
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
```

---

## 3. Danh Sách Phương Thức Của Lớp `Store`

| Nhóm chức năng | Tên phương thức | Ý nghĩa |
| :--- | :--- | :--- |
| **Tài khoản** | `add_account(...)` | Thêm tài khoản mới, tự động tính `expires_at` và lưu xuống đĩa. |
| | `list_accounts()` | Liệt kê tài khoản đã lược bỏ trường `cookies` nhạy cảm để hiển thị trên UI. |
| | `pick_account(...)` | Thuật toán chọn tài khoản tối ưu theo Sticky LRU. |
| | `touch_keepalive(...)`| Cập nhật mốc thời gian bảo hoạt và trạng thái sức khỏe tài khoản. |
| | `update_account(...)` | Cập nhật nhãn, trạng thái bật/tắt hoặc bổ sung cookie mới. |
| | `delete_account(...)` | Xóa tài khoản khỏi hồ chứa theo ID. |
| | `stats()` | Thống kê số lượng: tổng, đang bật, lỗi, sắp hết hạn (<3 ngày). |
| **Nhiệm vụ** | `create_task(...)` | Tạo nhiệm vụ sinh ảnh/video với trạng thái ban đầu là `queued`. |
| | `update_task(...)` | Cập nhật trạng thái (`processing`, `completed`, `failed`) và kết quả. |
| | `get_task(...)` | Lấy chi tiết thông tin nhiệm vụ theo task ID. |
| | `list_tasks(...)` | Liệt kê các nhiệm vụ gần nhất có phân trang. |
| | `clear_tasks(...)` | Dọn dẹp các nhiệm vụ cũ, giữ lại N bản ghi gần nhất. |

---

## 4. Liên kết Liên quan

- [Tài liệu Chi tiết File store.py](../04-chi-tiet-ma-nguon/store-py.md)
- [Module App API](app-api.md)
- [Mục lục Tài liệu](../README.md)
