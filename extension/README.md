# Tiện Ích Nhập Cookie Muse2API — Hướng Dẫn Cài Đặt

Tiện ích này chỉ làm duy nhất một việc: đồng bộ Cookie đăng nhập `muse.ai` trong trình duyệt của bạn sang dịch vụ `muse2api`. Không cần cài Python, không cần mở Terminal.

---

## 1. Giải nén

Giải nén tệp `muse2api-extension.zip` vào một thư mục cố định (không xóa đi sau khi cài), ví dụ:

- **Windows**: `D:\muse2api-extension`
- **macOS / Linux**: `~/Documents/muse2api-extension`

Sau khi giải nén, bên trong sẽ có các tệp `manifest.json`, `popup.html`, `popup.js` và thư mục `_locales/`.

---

## 2. Nạp tiện ích vào Chrome / Edge

### Trên Google Chrome:
1. Gõ `chrome://extensions` vào thanh địa chỉ rồi nhấn **Enter**.
2. Bật công tắc **Chế độ dành cho nhà phát triển (Developer mode)** ở góc trên bên phải.
3. Nhấn nút **Tải tiện ích đã giải nén (Load unpacked)** ở góc trên bên trái.
4. Chọn **thư mục** vừa giải nén ở Bước 1 (chọn cả thư mục, không phải chọn từng tệp bên trong).
5. Nhấn biểu tượng mảnh ghép trên thanh công cụ trình duyệt và ghim tiện ích ra ngoài để tiện sử dụng.

### Trên Microsoft Edge:
1. Gõ `edge://extensions` vào thanh địa chỉ rồi nhấn **Enter**.
2. Bật **Chế độ nhà phát triển (Developer mode)** ở thanh bên trái.
3. Nhấn **Tải phần mở rộng đã giải nén (Load unpacked)** và chọn thư mục như trên.

Các trình duyệt nhân Chromium khác (Brave, Vivaldi, Cốc Cốc...) thực hiện hoàn toàn tương tự.

---

## 3. Sử dụng

1. Mở `https://muse.ai/` trên chính trình duyệt này và đăng nhập cho đến khi nhìn thấy giao diện trò chuyện.
2. Mở trang quản trị `muse2api`, tại đầu tab **Hồ chứa tài khoản**, sao chép **BASE URL** và **API Key**.
3. Nhấn vào biểu tượng tiện ích trên thanh công cụ trình duyệt, điền hai thông tin trên (chỉ cần điền 1 lần, tiện ích sẽ tự ghi nhớ).
4. Nhấn **Đọc và nhập tài khoản**. Khi thấy thông báo `✓ Nhập thành công` là hoàn tất!

*(Tiện ích hỗ trợ chuyển đổi 3 ngôn ngữ trực tiếp trên góc phải: **Tiếng Việt**, **English**, **中文**).*

---

## 4. Câu hỏi thường gặp (FAQ)

- **Báo lỗi "Không tìm thấy Cookie nào của muse.ai"**:
  Trình duyệt hiện tại chưa đăng nhập `muse.ai`. Hãy mở `https://muse.ai/` và đăng nhập trước.
- **Báo lỗi "Thiếu mục cốt lõi: hatch_sess..."**:
  Quá trình đăng nhập chưa hoàn tất. Hãy đăng nhập đến khi vào được màn hình chat chính rồi bấm lại.
- **Báo lỗi "API Key không đúng (dịch vụ trả về 401)"**:
  Sao chép lại API Key trên trang quản trị (lưu ý Key bắt đầu bằng `m2a_`).
- **Báo lỗi mạng / CORS**:
  Kiểm tra lại địa chỉ dịch vụ xem đã đúng giao thức `http://` hoặc `https://` chưa, và thử mở trực tiếp `<Địa chỉ dịch vụ>/admin` trên trình duyệt xem dịch vụ có đang chạy không.
- **Tiện ích có gửi Cookie của tôi đi nơi khác không?**:
  Không. Tiện ích chỉ sử dụng quyền `cookies` và `storage`, toàn bộ mã nguồn nằm rõ ràng trong `popup.js`: chỉ gửi duy nhất một yêu cầu POST tới địa chỉ dịch vụ do chính bạn cấu hình.

---

## 5. Gỡ cài đặt

Mở `chrome://extensions` → Tìm **Muse2API Nhập Cookie** → Nhấn **Xóa (Remove)**.
