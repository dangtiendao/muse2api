# Quy Chuẩn Lập Trình (Coding Conventions)

---

## 1. Phong Cách Mã Nguồn Python

- **Chuẩn phong cách**: Tuân thủ tiêu chuẩn **PEP 8**.
- **Docstring**: Tuân thủ chuẩn **PEP 257**. Mọi lớp (class) và hàm (function) công khai đều phải có docstring rõ ràng:
  - Mô tả chức năng ngắn gọn.
  - Danh sách tham số (`Args`): Tên, kiểu dữ liệu, ý nghĩa.
  - Kết quả trả về (`Returns`): Kiểu dữ liệu, ý nghĩa.
  - Ngoại lệ (`Raises`): Các lỗi runtime có thể ném ra.
- **Type Hinting**: Bắt buộc khai báo kiểu dữ liệu cho tham số và giá trị trả về của hàm:
  ```python
  from __future__ import annotations
  
  def pick_account(self, preferred_id: str | None = None) -> dict | None:
      ...
  ```
- **Xử lý An toàn Ngoại Lệ**: Không sử dụng `except:` trần trụi. Bắt buộc bắt đúng kiểu ngoại lệ (ví dụ: `except requests.RequestException:`, `except (KeyError, ValueError):`). Nếu dùng catch-all, phải có comment rõ ràng `# noqa: BLE001`.

---

## 2. Phong Cách Mã Nguồn JavaScript

- **Chuẩn cú pháp**: ES6+ (ECMAScript 2020+).
- **JSDoc**: Các hàm tiện ích trong `extension/` và `tools/` phải có chú thích JSDoc chuẩn:
  ```javascript
  /**
   * Trích xuất cookie từ browser.
   * @param {string} domain - Tên miền cần đọc.
   * @returns {Promise<Object>}
   */
  async function grabCookies(domain) { ... }
  ```
- **Khai báo biến**: Dùng `const` cho hằng số và biến không gán lại; dùng `let` cho biến cục bộ; tuyệt đối không dùng `var` trong mã ứng dụng mới (trừ các đoạn JS string injection tương thích trình duyệt cũ).

---

## 3. Quy Tắc Viết Comment

1. **Ngôn ngữ**: Viết comment bằng tiếng Việt rõ nghĩa, chuẩn thuật ngữ kỹ thuật; hoặc tiếng Anh chuẩn mực.
2. **Không lặp lại điều hiển nhiên**: Tránh các comment vô nghĩa như `i = i + 1  # tăng i lên 1`.
3. **Tập trung vào "Tại sao" (Why)**: Giải thích lý do chọn giải pháp kỹ thuật, các trường hợp góc (edge cases) và các bài học kinh nghiệm từ thực tế (ví dụ: lý do không truyền expires quá khứ cho Chromium setCookie, lý do Snap Chromium không đọc được thư mục ẩn...).

---

## 4. Liên kết Liên quan
- [Quy Trình Đóng Góp](quy-trinh-dong-gop.md)
- [Quy Trình Kiểm Thử](kiem-thu.md)
- [Mục lục Tài liệu](../README.md)
