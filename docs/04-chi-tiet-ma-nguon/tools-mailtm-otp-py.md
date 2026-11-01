# Chi Tiết Mã Nguồn: `tools/mailtm_otp.py`

---

## 1. Thông Tin Cơ Bản
- **Đường dẫn file gốc**: [../../tools/mailtm_otp.py](../../tools/mailtm_otp.py)
- **Số dòng mã**: ~105 dòng.
- **Ngôn ngữ**: Python 3.8+ (Zero Dependency, 100% Standard Library).
- **Chức năng chính**: Script CLI tự động tạo hòm thư điện tử tạm thời qua Mail.tm REST API và polling hòm thư để trích xuất mã xác thực OTP (4-8 chữ số) phục vụ đăng ký/đăng nhập tài khoản muse.ai.

---

## 2. Vai Trò Trong Hệ Thống
- **Thuộc tầng**: Công Cụ Dòng Lệnh Phụ Trợ (Helper CLI Tool).
- **Được gọi bởi**: Người dùng / Kỹ sư khi thực hiện onboarding tài khoản mới.
- **Gọi đến**: Dịch vụ Mail.tm API (`https://api.mail.tm`).

---

## 3. Danh Sách Hàm Quan Trọng

| Tên hàm | Chức năng chi tiết |
| :--- | :--- |
| `req(path, method, token, body)` | Wrapper gửi yêu cầu HTTP và phân giải JSON qua `urllib.request`. |
| `new_account()` | Đăng ký một tài khoản hòm thư ngẫu nhiên trên Mail.tm, trả về `(address, password, token)`. |
| `login(addr, pwd)` | Đăng nhập vào hòm thư đã có để lấy JWT token. |
| `poll(token, timeout)` | Vòng lặp kiểm tra hòm thư đến mỗi 3 giây, dùng regex tìm chuỗi 4-8 số và in ra console. |
| `main()` | Xử lý các tham số dòng lệnh CLI `--addr`, `--pass`, `--timeout`. |

---

## 4. Liên kết Liên quan
- [Module Tools](../03-module/tools-helpers.md)
- [Mục lục Tài liệu](../README.md)
