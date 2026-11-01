# Quy Trình Đóng Góp Mã Nguồn (Contribution Workflow)

---

## 1. Mô Hình Phân Nhánh (Git Branching Flow)

Dự án áp dụng mô hình phân nhánh đơn giản dựa trên **GitHub Flow**:
- `main`: Nhánh chính, luôn phản ánh trạng thái ổn định và sẵn sàng triển khai.
- `feature/<ten-tinh-nang>`: Nhánh phát triển tính năng mới.
- `fix/<ten-loi>`: Nhánh sửa lỗi.
- `docs/<noi-dung>`: Nhánh cập nhật tài liệu kỹ thuật.

---

## 2. Quy Chuẩn Thông Điệp Commit (Conventional Commits)

Mọi commit phải tuân thủ chuẩn **Conventional Commits 1.0.0**:

```text
<loại>(<phạm vi>): <mô tả ngắn bằng chữ thường, không dấu chấm cuối>

[Nội dung chi tiết giải thích lý do thay đổi nếu cần]

[Liên kết issue: Fixes #123]
```

### Các tiền tố (Types) được chấp nhận:
- `feat`: Tính năng mới cho người dùng hoặc API.
- `fix`: Sửa lỗi phát sinh.
- `docs`: Thêm hoặc sửa đổi tài liệu trong `docs/` hoặc `README.md`.
- `refactor`: Tái cấu trúc mã nguồn mà không thay đổi hành vi bên ngoài.
- `perf`: Cải tiến hiệu năng hoặc giảm độ trễ.
- `test`: Bổ sung hoặc chỉnh sửa các bài kiểm thử tự động.
- `chore`: Cập nhật cấu hình build, dependencies hoặc công cụ phát triển.

*Ví dụ*:
```text
feat(engine): support multi-reference images upload via DataTransfer API
fix(store): prevent duplicate sticky count reset on concurrency collision
docs(api): add detailed documentation for /v1/responses endpoint
```

---

## 3. Quy Trình Tạo Pull Request (PR)

1. **Fork & Tạo nhánh**: Fork repository về tài khoản cá nhân và tạo nhánh mới từ `main`.
2. **Kiểm tra mã nguồn cục bộ**:
   - Chạy `python -m py_compile <file.py>` đảm bảo không lỗi cú pháp.
   - Chạy `python -m unittest discover tests` đảm bảo vượt qua toàn bộ bài test.
3. **Đồng bộ tài liệu**:
   > [!IMPORTANT]
   > Mọi thay đổi về API, tham số môi trường hoặc hành vi hệ thống BẮT BUỘC phải cập nhật tài liệu tương ứng trong thư mục `docs/`.
4. **Mở Pull Request**: Điền đầy đủ thông tin vào mẫu PR Template, tích chọn các checkbox kiểm tra và gửi PR để Maintainer duyệt.

---

## 4. Liên kết Liên quan
- [Quy Chuẩn Lập Trình](coding-convention.md)
- [Quy Trình Kiểm Thử](kiem-thu.md)
- [Mục lục Tài liệu](../README.md)
