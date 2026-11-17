# Các Câu Hỏi Thường Gặp (FAQ)

---

## 1. Vận Hành & Khởi Chạy

### Q1: Tại sao Chromium báo lỗi "Khởi động Chromium thất bại" khi khởi chạy trên máy chủ Linux?
**Trả lời**:
1. Đảm bảo bạn đã cài đặt các gói thư viện đồ họa hệ thống và phông chữ:
   ```bash
   sudo apt-get install -y chromium fonts-wqy-zenhei
   ```
2. Nếu chạy trong container hoặc dưới quyền `root`, cờ `--no-sandbox` bắt buộc phải có (muse2api đã mặc định bật cờ này).
3. Kiểm tra xem cổng `19210` có bị tiến trình nào khác chiếm dụng không:
   ```bash
   lsof -i :19210
   ```

---

### Q2: Tại sao tài khoản báo hạn dùng chỉ có 2 ngày thay vì 30 ngày?
**Trả lời**:
Nền tảng muse.ai quy định thời hạn của cookie máy ảo `hatch_vml` là **cố định 48 giờ** và không tự động tăng khi sử dụng thông thường. Mặc dù cookie `hatch_sess` kéo dài 30 ngày, nhưng nếu `hatch_vml` hết hạn thì tài khoản sẽ bị lỗi khi tạo ảnh hoặc video.
Hệ thống muse2api đã tích hợp daemon tự động gọi `/api/session` để gia hạn `hatch_vml` thêm 48h liên tục. Miễn là server hoạt động và tài khoản đang bật, phiên sẽ luôn được duy trì sống.

---

### Q3: Làm sao để tích hợp vào NextChat hoặc LobeChat?
**Trả lời**:
1. Mở phần Cài đặt (Settings) của NextChat / LobeChat.
2. Chọn nhà cung cấp **OpenAI**.
3. **Endpoint (URL giao diện)**: Điền `http://<IP_MÁY_CHỦ>:18610` (hoặc `https://domain-cua-ban.com`).
4. **API Key**: Điền giá trị `MUSE2API_KEY` bạn đã cấu hình trong file `.env`.
5. **Model tùy chỉnh**: Bạn có thể chọn `gpt-4o`, `gpt-5`, `claude-sonnet-4` hoặc `deepseek-chat`.

---

### Q4: Làm thế nào để tạo nhiều ảnh hoặc video song song mà không bị nghẽn?
**Trả lời**:
1. Thêm nhiều tài khoản vào hồ chứa (mỗi tài khoản sẽ được cấp phát một Incognito Context độc lập).
2. Tăng tham số `MUSE2API_CONCURRENCY` trong file `.env` (ví dụ nâng lên `4` hoặc `6` nếu máy chủ có 4GB - 8GB RAM).

---

## 2. Liên kết Liên quan
- [Bảng Thuật Ngữ](thuat-ngu.md)
- [Đề Xuất Cải Tiến](de-xuat-cai-tien.md)
- [Mục lục Tài liệu](../README.md)
