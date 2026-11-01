# Chi Tiết Mã Nguồn: `store.py`

---

## 1. Thông Tin Cơ Bản
- **Đường dẫn file gốc**: [../../store.py](../../store.py)
- **Số dòng mã**: ~317 dòng.
- **Ngôn ngữ**: Python 3.10+.
- **Chức năng chính**: Quản lý hồ chứa tài khoản (Account Pool) và hàng đợi tác vụ bất đồng bộ (Task Store), tính toán thời hạn sống chính xác của cookie và đảm bảo an toàn dữ liệu trên đĩa bằng cơ chế ghi file nguyên tử (Atomic Write).

---

## 2. Vai Trò Trong Hệ Thống
- **Thuộc tầng**: Tầng Lưu Trữ Dữ Liệu (Data Persistence Layer).
- **Được gọi bởi**: `app.py`.
- **Gọi đến**: File hệ thống (`data/accounts.json`, `data/tasks.json`).

---

## 3. Luồng Xử Lý Dữ Liệu (Data Flow)

```text
Thao tác nghiệp vụ (Thêm tài khoản / Cập nhật task / Chọn tài khoản)
  ↓
Khóa toàn cục `_LOCK = threading.Lock()`
  ↓
Thao tác trên danh sách đối tượng trong bộ nhớ RAM (`self.accounts`, `self.tasks`)
  ↓
Ghi nguyên tử xuống đĩa qua file tạm `mkstemp()` và `os.replace()`
  ↓
Trả về kết quả cho tầng trên
```

---

## 4. Danh Sách Các Lớp & Hàm Quan Trọng

| Tên lớp / hàm | Chức năng chi tiết |
| :--- | :--- |
| `ESSENTIAL_COOKIES` | Bộ đôi cookie cốt lõi quyết định phiên sống: `hatch_sess` và `hatch_vml`. |
| `account_expiry(...)` | Tính toán mốc thời gian hết hạn chính xác của tài khoản dựa trên hạn dùng thực của `hatch_vml`. |
| `_write(path, obj)` | Cơ chế ghi file JSON nguyên tử (Atomic Write) chống hỏng file khi crash. |
| `Store.add_account(...)` | Thêm tài khoản mới với đầy đủ nhãn và tính toán hạn dùng. |
| `Store.pick_account(...)` | Thuật toán chọn tài khoản tối ưu kết hợp Sticky Affinity (15 lần) và cân bằng tải LRU. |
| `Store.touch_keepalive(...)`| Ghi nhận kết quả kiểm tra bảo hoạt của background heartbeat. |
| `Store.update_account(...)` | Cập nhật nhãn, trạng thái enabled hoặc cập nhật cookies mới. |
| `Store.create_task(...)` | Tạo bản ghi nhiệm vụ mới trong hàng đợi (`queued`). |
| `Store.update_task(...)` | Cập nhật tiến độ hoặc kết quả nhiệm vụ. |

---

## 5. Phụ Thuộc (Dependencies)
- **Thư viện bên ngoài**: Không (100% Python Standard Library: `json`, `os`, `tempfile`, `threading`, `time`, `uuid`).
- **Module nội bộ**: `config.CFG`.

---

## 6. Liên kết Liên quan
- [Module Store Storage](../03-module/store-storage.md)
- [Module App API](../03-module/app-api.md)
- [Mục lục Tài liệu](../README.md)
