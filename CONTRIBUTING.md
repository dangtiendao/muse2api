# Hướng Dẫn Đóng Góp Cho Dự Án MUSE2API (Contributing Guidelines)

Cảm ơn bạn đã quan tâm và muốn đóng góp cho dự án **MUSE2API**! Để đảm bảo chất lượng mã nguồn, tính ổn định của hệ thống và tính đồng bộ của tài liệu, vui lòng đọc kỹ các quy tắc dưới đây trước khi gửi Pull Request (PR).

---

## 📌 Nguyên Tắc Vàng (Golden Rule)

> [!IMPORTANT]
> **MỌI THAY ĐỔI VỀ MÃ NGUỒN (CODE) BẮT BUỘC PHẢI ĐƯỢC CẬP NHẬT TÀI LIỆU TƯƠNG ỨNG TRONG THƯ MỤC [`docs/`](docs/README.md).**
> - Thêm/sửa API $\rightarrow$ Cập nhật `docs/06-api/`.
> - Thêm/sửa biến môi trường $\rightarrow$ Cập nhật `docs/02-cai-dat/cau-hinh.md` và `.env.example`.
> - Thay đổi luồng xử lý $\rightarrow$ Cập nhật sơ đồ trong `docs/05-luong-xu-ly/`.
> - Bất kỳ PR nào sửa đổi logic nhưng không cập nhật tài liệu sẽ bị từ chối duyệt.

---

## 🛠️ Quy Trình Đóng Góp (Step-by-Step)

### 1. Tạo Nhánh (Branching)
Tạo nhánh mới từ nhánh `main` với tiền tố phù hợp:
- `feat/<ten-tinh-nang>`: Tính năng mới.
- `fix/<ten-loi>`: Sửa lỗi phát sinh.
- `docs/<noi-dung>`: Cập nhật hoặc bổ sung tài liệu.
- `refactor/<ten-module>`: Tái cấu trúc mã nguồn.

### 2. Quy Chuẩn Lập Trình & Comment
- Tuân thủ PEP 8 và PEP 257 cho Python.
- Thêm docstring đầy đủ cho các hàm và lớp mới.
- Không đưa thông tin nhạy cảm (mật khẩu, API Key thật, Cookie thật) vào mã nguồn hoặc tài liệu.
- Tham khảo chi tiết tại: [Quy chuẩn lập trình](docs/07-huong-dan-phat-trien/coding-convention.md).

### 3. Quy Chuẩn Commit (Conventional Commits)
Thông điệp commit phải tuân theo cấu trúc:
```text
<type>(<scope>): <mô tả ngắn bằng chữ thường>
```
*Ví dụ*:
- `feat(engine): support multi-image upload via DataTransfer`
- `fix(store): resolve race condition in sticky account allocation`
- `docs(api): update request schema for /v1/images/edits`

### 4. Kiểm Thử Trước Khi Gửi PR
Trước khi mở PR, hãy đảm bảo:
```bash
# 1. Kiểm tra cú pháp
python -m py_compile app.py engine.py store.py cdp.py config.py

# 2. Chạy toàn bộ unit tests
python -m unittest discover tests

# 3. Kiểm tra hiển thị tài liệu
mkdocs build
```

---

## 📋 Pull Request Template
Khi mở Pull Request trên GitHub, vui lòng điền đầy đủ thông tin theo mẫu được định nghĩa sẵn tại `.github/PULL_REQUEST_TEMPLATE.md`.
