# Giới Thiệu Dự Án MUSE2API

---

## 1. Mục tiêu Dự án

**MUSE2API** là giải pháp phần mềm Reverse Proxy kiêm Orchestrator được thiết kế nhằm chuyển đổi các năng lực trí tuệ nhân tạo tạo sinh đa phương tiện (Multimodal Generative AI) từ nền tảng web [muse.ai](https://muse.ai/) thành các giao diện lập trình ứng dụng RESTful API chuẩn công nghiệp, tương thích 100% với giao thức **OpenAI API**.

Dự án ra đời nhằm giải quyết các bài toán kỹ thuật phức tạp:
- **Tận dụng hạn mức miễn phí**: Khai thác năng lực sinh văn bản (Chat Completions), sinh hình ảnh chất lượng cao (Text-to-Image / Image Editing) và sinh video chân thực (Text-to-Video / Image-to-Video) từ tài khoản muse.ai mà không cần chi phí bản quyền lớn.
- **Tiêu chuẩn hóa giao diện**: Cho phép các ứng dụng khách (NextChat, LobeChat, Chatbox, Cursor, Continue, các AI SDK...) tích hợp trực tiếp mà không cần sửa đổi mã nguồn client (chỉ cần đổi `BASE_URL` và `API_KEY`).
- **Khắc phục rào cản kỹ thuật của muse.ai**: Tự động giải quyết việc cookie phiên (`hatch_vml`) hết hạn sau 48 giờ, cơ chế máy ảo đám mây ngủ đông (VM Hibernation), cookie bảo mật `httpOnly` và phòng chống xung đột khi chạy song song nhiều tác vụ.

---

## 2. Phạm vi Dự án (Scope)

### 2.1. Năng lực cốt lõi được hỗ trợ
1. **Trò chuyện thông minh (Chat Completions & Responses API)**:
   - Tương thích endpoint chuẩn `/v1/chat/completions` và `/v1/responses` (chuẩn Codex mới).
   - Hỗ trợ đầy đủ SSE Stream (`stream=True`) với độ trễ phản hồi ký tự đầu (TTFT) đạt **2 ~ 3 giây** nhờ cơ chế giữ ấm tab (Warm-Tab Affinity).
   - Hỗ trợ đa lượt hội thoại (Multi-turn Context) và thiết lập vai trò hệ thống (System Prompt).
   - Tự động định tuyến (alias routing) cho các mô hình: `gpt-4o`, `gpt-5`, `claude-sonnet-4`, `deepseek-chat`...
2. **Tạo và Chỉnh sửa Hình ảnh (Image Generation & Edits)**:
   - Tương thích endpoint `/v1/images/generations` và `/v1/images/edits`.
   - Hỗ trợ nhiều tỉ lệ khung hình: `1:1`, `16:9`, `9:16`, `4:3`, `3:4`.
   - Hỗ trợ truyền 1 hoặc nhiều ảnh tham chiếu (tối đa 4 ảnh, tối đa 24 MiB tổng cộng).
   - Trả về định dạng URL trực tiếp hoặc chuỗi `b64_json`. Tự động nhận diện từ chối của mô hình để ngắt sớm.
3. **Sinh Video (Video Generation)**:
   - Tương thích endpoint `/v1/videos` (tạo tác vụ) và `/v1/videos/{task_id}` (polling trạng thái).
   - Hỗ trợ video ngang `16:9` và dọc `9:16`, điều khiển thời lượng (5s, 6s, 8s, 10s).
   - Hỗ trợ Text-to-Video và Image-to-Video (dùng ảnh tham chiếu làm khung hình bắt đầu).
   - Lưu trữ cục bộ tệp MP4 trong kho media `/v1/media/{filename}`.
4. **Hạ tầng Quản trị & Điều phối Đa tài khoản**:
   - Hồ chứa tài khoản không giới hạn (Account Pool).
   - Cách ly tuyệt đối Cookie và Session bằng Chromium Incognito Contexts (`Target.createBrowserContext`).
   - Tự động duy trì phiên 48 giờ và đánh thức VM ngầm (`/api/session`, `/api/hatch/vm/wake`).
   - Giao diện Admin Console trực quan, hỗ trợ cập nhật OTA 1-click từ GitHub.
   - Tiện ích Chrome Extension và Tampermonkey Script đồng bộ cookie 1-click.

### 2.2. Các trường hợp nằm ngoài phạm vi (Out of Scope)
- Không can thiệp vào mô hình trọng số bên trong của muse.ai; hệ thống chỉ đóng vai trò tự động hóa giao diện web thông qua giao thức gỡ lỗi trình duyệt (CDP).
- Không vượt qua Cloudflare Captcha nếu địa chỉ IP máy chủ bị đánh dấu spam mức độ cao (cần cấu hình proxy sạch hoặc máy chủ có IP uy tín).

---

## 3. Đối tượng Sử dụng (Target Audience)

- **Lập trình viên AI / Fullstack Developers**: Cần một nguồn API tạo ảnh/video/chat miễn phí, ổn định để thử nghiệm ứng dụng, chatbot hoặc tích hợp vào hệ sinh thái nội bộ.
- **Kỹ sư DevOps / System Administrators**: Cần một dịch vụ dễ dàng đóng gói Docker, tự động hóa duy trì kết nối và bảo trì tối thiểu.
- **Người dùng cá nhân**: Sử dụng các phần mềm chat client nguồn mở phổ biến (NextChat, LobeChat, Cherry Studio, Dify...) muốn tận dụng tài nguyên từ muse.ai.

---

## 4. Liên kết Liên quan

- [Kiến trúc Tổng thể](kien-truc.md)
- [Cấu trúc Thư mục](cau-truc-thu-muc.md)
- [Công nghệ Sử dụng](cong-nghe.md)
- [Mục lục Tài liệu](../README.md)
