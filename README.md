# MUSE2API

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python" alt="Python Version" />
  <img src="https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker" alt="Docker" />
  <img src="https://img.shields.io/badge/API-OpenAI%20Compatible-green" alt="OpenAI API Compatible" />
  <img src="https://img.shields.io/badge/License-MIT-orange" alt="License" />
  <a href="docs/README.md"><img src="https://img.shields.io/badge/Docs-T%C3%A0i%20Li%E1%BB%87u%20K%E1%BB%B9%20Thu%E1%BA%ADt-blueviolet?logo=read-the-docs" alt="Docs" /></a>
  <a href="https://linux.do/" target="_blank"><img src="https://img.shields.io/badge/Community-LINUX%20DO-111827?logo=linux&logoColor=white" alt="LINUX DO" /></a>
</p>

<p align="center">
  🤝 Dự án mã nguồn mở này đã liên kết và đồng hành cùng <b><a href="https://linux.do/" target="_blank">Cộng đồng LINUX DO (https://linux.do/)</a></b> — Cộng đồng kỹ thuật chân thành, thân thiện, đoàn kết và chuyên nghiệp
</p>

Đóng gói và chuyển đổi các năng lực đa phương thức tiên tiến trên nền tảng web **[muse.ai](https://muse.ai/)** thành **RESTful API tương thích hoàn toàn chuẩn OpenAI**. Thông qua điều khiển trình duyệt không giao diện qua giao thức CDP, tái sử dụng đường hầm WebSocket dự phòng nóng và quản lý phiên động, hệ thống hỗ trợ nguyên bản hội thoại văn bản (độ trễ ký tự đầu tiên qua stream chỉ 2~3 giây), văn bản sinh ảnh, chỉnh sửa ảnh tham chiếu, văn bản sinh video, ảnh sinh video, kết hợp luân chuyển hồ chứa đa tài khoản, tự động gia hạn phiên 48 giờ, đánh thức VM đám mây và bộ tiện ích Chrome Extension / Userscript nhập tài khoản 1 chạm.

> [!TIP]
> 📖 **Hệ Thống Tài Liệu Kỹ Thuật Toàn Diện (Full Technical Documentation)**
>
> Toàn bộ kiến trúc, chi tiết mã nguồn, phân tích module, sơ đồ luồng dữ liệu (Mermaid) và hướng dẫn API đã được biên soạn chính thức tại thư mục **[`docs/`](docs/README.md)**.
> - 🏗️ [Kiến Trúc & Thiết Kế Phân Tầng](docs/01-tong-quan/kien-truc.md)
> - 🚀 [Hướng Dẫn Cài Đặt Chi Tiết](docs/02-cai-dat/huong-dan-cai-dat.md)
> - 🔌 [Tài Liệu Tra Cứu API Đầy Đủ](docs/06-api/tong-quan-api.md)
> - 🔄 [Sơ Đồ Tuần Tự (Sequence Diagrams)](docs/05-luong-xu-ly/chat-streaming.md)
> - 🤝 [Quy Chuẩn Đóng Góp (Contributing)](CONTRIBUTING.md)

---

## 🌟 Tính Năng Cốt Lõi

- 💬 **Giao diện hội thoại tiêu chuẩn (Chat Completions & Responses API)**
  - Tương thích hoàn toàn với `/v1/chat/completions` và giao thức `/v1/responses` được Codex thế hệ mới sử dụng mặc định.
  - Hỗ trợ nguyên bản đầu ra dạng dòng chảy SSE mô phỏng máy đánh chữ (`stream=True`) và phản hồi đồng bộ trọn gói; tích hợp tái sử dụng tab ấm và đường truyền Noise WebSocket, **độ trễ ký tự đầu tiên cho hội thoại liên tiếp chỉ từ 2~3 giây**.
  - Hỗ trợ ngữ cảnh hội thoại nhiều lượt và thiết lập System Prompt.
  - Tích hợp ánh xạ bí danh mô hình thông minh: tự động định tuyến các tên phổ biến như `gpt-4o`, `gpt-5`, `claude-sonnet-4`, `deepseek-chat`...
- 🎨 **Tạo ảnh chất lượng cao & Chỉnh sửa ảnh (Images Generations & Edits)**
  - Tương thích hoàn toàn với `/v1/images/generations` (văn bản sinh ảnh) và `/v1/images/edits` (ảnh sinh ảnh / chỉnh sửa theo ảnh tham chiếu).
  - Hỗ trợ nhiều tỉ lệ khung hình (`1:1`, `16:9`, `9:16`, `4:3`, `3:4`...), tải lên trực tiếp 1 hoặc tối đa 4 ảnh tham chiếu có thứ tự và xuất ảnh sạch không watermark.
  - Hỗ trợ hai định dạng trả về `url` trực tiếp hoặc `b64_json`; tích hợp phát hiện nhanh phản hồi từ chối thuần văn bản trong vài giây để tránh kẹt hàng đợi.
  - Chỉnh sửa ảnh đảm bảo chỉ trả về media mới tạo trong lượt hiện tại: loại trừ ảnh xem trước tải lên và tệp đính kèm lịch sử; báo lỗi rõ ràng nếu tải ảnh tham chiếu hoặc gửi prompt chưa được xác nhận thay vì âm thầm trả lại ảnh gốc.
- 🎬 **Văn bản sinh video / Ảnh sinh video (Videos)**
  - Kết nối trực tiếp mô hình tạo video của Muse, hỗ trợ truyền yêu cầu thời lượng 5s / 6s / 8s / 10s (thời lượng thành phẩm thực tế theo đầu ra của Muse) cùng khung hình dọc `9:16` / ngang `16:9`.
  - Hỗ trợ tải lên 1 ảnh khung hình đầu tiên, hoặc mảng `images` gồm nhiều ảnh tham chiếu chủ thể và phong cách (ảnh đầu tiên đóng vai trò khung mở đầu chính).
  - Kiến trúc tác vụ bất đồng bộ (`POST /v1/videos` tạo nhiệm vụ + `GET /v1/videos/{task_id}` truy vấn trạng thái).
  - Tích hợp sẵn dịch vụ phân phối media `/v1/media/{filename}`, tự động lưu trữ bền vững tài nguyên MP4 / WebP đã tạo.
- ⚡ **Thực thi song song đa tài khoản thực thụ (Multi-Account Parallel Execution)**
  - Dựa trên container ẩn danh cô lập `Target.createBrowserContext` gốc của Chromium, các tác vụ chạy đồng thời trong những sandbox độc lập.
  - Nhiều tài khoản cùng lúc tạo ảnh, tạo video, hội thoại streaming không chặn lẫn nhau; Cookie và Session được cách ly 100%.
  - Tích hợp bộ điều phối xung đột thông minh: tự động khóa loại trừ trên cùng một tài khoản và chạy song song tối đa trên nhiều tài khoản khác nhau.
  - Linh hoạt mở rộng giới hạn đồng thời qua biến `MUSE2API_CONCURRENCY` theo cấu hình máy chủ (mặc định: `2`).
- 🔄 **Hồ chứa đa tài khoản & Điều phối ưu tiên kết nối ấm**
  - Hỗ trợ nhập không giới hạn số lượng tài khoản Muse vào hồ chứa.
  - Phân phối thông minh kết hợp ưu tiên tab ấm (Warm-Tab Affinity) và thuật toán xoay vòng công bằng LRU.
  - Tự động đánh dấu và chuyển đổi dự phòng (failover) tức thì sang tài khoản khỏe mạnh tiếp theo khi gặp tài khoản hết hạn mức hoặc lỗi phiên.
- 🛡️ **Tự động gia hạn phiên 48 giờ & Giữ ấm VM đám mây**
  - Coroutine chạy nền định kỳ gọi thẳng `/api/session` để tự động gia hạn `hatch_vml` (+48h) và `hatch_sess` (+30d), đồng thời gọi `/api/hatch/vm/wake` để giữ máy ảo workspace trên mây luôn sẵn sàng.
  - Giải quyết triệt để bài toán hết hạn tĩnh 48 giờ của Meta Cookie và tình trạng VM ngủ đông ngắt kết nối.
- 🧩 **Tiện ích Chrome Extension & Userscript nhập tài khoản 1 chạm**
  - Không cần mở F12 bắt gói tin thủ công: chỉ một cú nhấp chuột trên biểu tượng tiện ích là toàn bộ phiên đăng nhập hiện tại (bao gồm cả các cookie cốt lõi `HttpOnly` và thời gian hết hạn thực tế) sẽ được trích xuất và đẩy an toàn vào hồ chứa tài khoản.
- 🖥️ **Bảng điều khiển Web Console giao diện tối hiện đại (Đa ngôn ngữ Việt / Anh / Trung) & Nâng cấp nóng OTA**
  - Web UI tích hợp sẵn với **Tiếng Việt là ngôn ngữ mặc định** (hỗ trợ chuyển đổi linh hoạt `Tiếng Việt` / `English` / `中文`), cho phép theo dõi sức khỏe dịch vụ, hạn mức và trạng thái hồ chứa tài khoản, giữ phiên toàn bộ 1 chạm, xem lại tiến độ nhiệm vụ, quản lý thư viện media và kiểm thử API trực tuyến.
  - **Thông báo cập nhật thời gian thực & Nâng cấp 1 chạm**: Khi kho GitHub chính thức phát hành phiên bản hoặc bản vá mới, thanh thông báo trên đầu trang quản trị sẽ tự động hiển thị, nhấn **「⚡ Nâng cấp trực tuyến & khởi động lại」** để tự động kéo mã mới nhất và khởi động lại mượt mà (giữ nguyên cấu hình `.env` và dữ liệu tài khoản cục bộ).

---

## 🚀 Triển Khai Nhanh

### Cách 1: Docker Compose (Khuyến nghị — chạy ngay với một dòng lệnh)

1. **Sao chép mã nguồn và di chuyển vào thư mục dự án**:
   ```bash
   git clone https://github.com/czg86389-hub/muse2api.git
   cd muse2api
   ```

2. **Cấu hình biến môi trường (Tùy chọn)**:
   ```bash
   cp .env.example .env
   # Chỉnh sửa .env theo nhu cầu, khuyến nghị đặt MUSE2API_KEY thành khóa bí mật riêng của bạn
   ```

   Docker Compose sẽ tự động đọc `MUSE2API_KEY` từ `.env` mà không bị ghi đè bởi giá trị mẫu.

3. **Khởi chạy container**:
   ```bash
   docker compose up -d
   ```

4. **Truy cập bảng điều khiển quản trị**:
   Mở trình duyệt truy cập: `http://<IP_MÁY_CHỦ>:18610/admin?key=<MUSE2API_KEY_CỦA_BẠN>`

---

### Cách 2: Triển khai trực tiếp trên Máy chủ vật lý / VPS (Ubuntu / Debian)

1. **Cài đặt các gói phụ thuộc hệ thống và Chromium**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y chromium fonts-wqy-zenhei python3 python3-pip python3-venv
   ```

2. **Thiết lập môi trường ảo Python**:
   ```bash
   cd /opt/muse2api
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Cấu hình dịch vụ systemd**:
   ```bash
   sudo cp deploy/muse2api.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now muse2api
   ```

4. **Cấu hình Nginx Reverse Proxy (Quan trọng: chống lỗi 502 Timeout & giật cục khi stream)**:
   Nếu sử dụng Nginx / aaPanel / 1Panel làm reverse proxy, bắt buộc tăng `proxy_read_timeout` lên `600s` và tắt `proxy_buffering` (xem chi tiết tại `deploy/nginx.example.conf`):
   ```nginx
   location / {
       proxy_pass http://127.0.0.1:18610;
       proxy_read_timeout 600s;      # Tránh bị Nginx ngắt kết nối báo 502 Bad Gateway khi tạo ảnh/video lâu
       proxy_send_timeout 600s;
       proxy_buffering off;          # Đảm bảo SSE hội thoại xuất chữ tức thì không độ trễ
       client_max_body_size 64M;     # Hỗ trợ tải lên tệp ảnh tham chiếu dung lượng lớn
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
   }
   ```

---

## 🧩 Nhập Tài Khoản (Chrome Extension / Tampermonkey Userscript)

### Cách A: Tiện ích mở rộng Chrome / Edge
Dự án tích hợp sẵn tiện ích mở rộng nhập tài khoản chuyên dụng (nằm tại thư mục `extension/`), không cần trích xuất Cookie thủ công qua F12:

1. Mở trình duyệt Chrome / Edge, truy cập `chrome://extensions` và bật **「Chế độ dành cho nhà phát triển (Developer mode)」** ở góc trên bên phải.
2. Nhấn **「Tải tiện ích đã giải nén (Load unpacked)」** và chọn thư mục `extension` của dự án.
3. Đăng nhập [muse.ai](https://muse.ai/) trên trình duyệt đó cho đến khi vào giao diện trò chuyện chính.
4. Nhấn biểu tượng tiện ích trên thanh công cụ trình duyệt, điền địa chỉ dịch vụ (ví dụ `http://1.2.3.4:18610`) và `MUSE2API_KEY`.
5. Nhấn **「Đọc và nhập tài khoản」**, tài khoản sẽ được đồng bộ vào hồ chứa ngay lập tức!

### Cách B: Tampermonkey Userscript (Đa trình duyệt, không cần bật Developer mode)
Dành cho người dùng Firefox / Safari hoặc không muốn cài đặt extension giải nén:

👉 **[⚡ Nhấn để cài đặt nhanh Userscript (Raw UserJS)](https://raw.githubusercontent.com/czg86389-hub/muse2api/main/tools/muse2api_cookie_importer.user.js)**

1. Cài đặt tiện ích [Tampermonkey](https://www.tampermonkey.net/) trên trình duyệt.
2. Nhấn vào liên kết **「⚡ Nhấn để cài đặt nhanh Userscript」** ở trên, Tampermonkey sẽ tự bật cửa sổ cài đặt, nhấn **Install (Cài đặt)**.
3. Mở trang [muse.ai](https://muse.ai/), biểu tượng nổi **「⚡」** sẽ xuất hiện ở góc dưới bên phải màn hình — nhấn vào để mở bảng cấu hình và đẩy tài khoản vào hồ chứa chỉ với 1 chạm (tự động sao lưu Cookie vào Clipboard dự phòng).

---

## 📖 Ví Dụ Gọi API

Tất cả các endpoint có bảo vệ đều yêu cầu đính kèm Header:
```http
Authorization: Bearer <MUSE2API_KEY_CỦA_BẠN>
```

### 1. Hội thoại văn bản (Chat Completions)

```bash
curl -X POST "http://localhost:18610/v1/chat/completions" \
  -H "Authorization: Bearer m2a_your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "muse-spark",
    "messages": [
      {"role": "user", "content": "Viết một bài thơ thất ngôn tứ tuyệt về đêm mưa ánh đèn neon cyberpunk"}
    ],
    "stream": false
  }'
```

### 2. Tạo ảnh từ văn bản & ảnh tham chiếu (Image Generation & Edits)

```bash
curl -X POST "http://localhost:18610/v1/images/generations" \
  -H "Authorization: Bearer m2a_your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "muse-image",
    "prompt": "Một chú chó Shiba cơ khí mặc bộ đồ phi hành gia phản trọng lực, ánh sáng điện ảnh, độ phân giải 8k",
    "size": "16:9",
    "response_format": "url"
  }'
```

**Ví dụ phản hồi**:
```json
{
  "created": 1790148495,
  "data": [
    {
      "revised_prompt": "Một chú chó Shiba cơ khí mặc bộ đồ phi hành gia phản trọng lực, ánh sáng điện ảnh, độ phân giải 8k",
      "url": "http://localhost:18610/v1/media/img_abc123.webp",
      "kind": "image",
      "bytes": 54210
    }
  ]
}
```

Khi sử dụng nhiều ảnh tham chiếu, truyền qua mảng `images` (tối đa 4 ảnh; mỗi ảnh không quá 10 MiB, tổng cộng không quá 24 MiB); dịch vụ sẽ tải lên tuần tự theo thứ tự mảng và chỉ gửi prompt sau khi toàn bộ tệp đính kèm được giao diện web xác nhận. Không dùng chung `images` với các trường ảnh đơn cũ như `image` / `reference_image`:

```bash
curl -X POST "http://localhost:18610/v1/images/generations" \
  -H "Authorization: Bearer m2a_your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "muse-image",
    "prompt": "Kết hợp chủ thể của ảnh thứ nhất với bảng màu của ảnh thứ hai để tạo poster",
    "images": [
      {"url": "https://example.com/subject.png"},
      {"url": "https://example.com/style.png"}
    ],
    "response_format": "url"
  }'
```

Với yêu cầu multipart tới `/v1/images/edits`, bạn có thể lặp lại nhiều trường `image` cùng tên:

```bash
curl -X POST "http://localhost:18610/v1/images/edits" \
  -H "Authorization: Bearer m2a_your_secret_key" \
  -F "prompt=Kết hợp hai ảnh tham chiếu để tạo một bức ảnh mới" \
  -F "image=@subject.png" \
  -F "image=@style.png"
```

### 3. Văn bản sinh video / Ảnh sinh video (Videos)

- **Bước 1: Tạo nhiệm vụ sinh video**
  ```bash
  curl -X POST "http://localhost:18610/v1/videos" \
    -H "Authorization: Bearer m2a_your_secret_key" \
    -H "Content-Type: application/json" \
    -d '{
      "prompt": "Lá phong vàng nhẹ nhàng rơi trong làn gió thu, nắng ấm xuyên qua tán cây",
      "duration": 5,
      "size": "16:9"
    }'
  ```
  Trả về ID nhiệm vụ: `{"id": "task_xyz789", "status": "queued"}`

  Tạo video từ nhiều ảnh tham chiếu cũng sử dụng mảng `images` có thứ tự trong cùng yêu cầu (chỉ hỗ trợ hình ảnh làm tham chiếu video, không hỗ trợ tải lên tệp video):
  ```bash
  curl -X POST "http://localhost:18610/v1/videos" \
    -H "Authorization: Bearer m2a_your_secret_key" \
    -H "Content-Type: application/json" \
    -d '{
      "prompt": "Cho chủ thể ở ảnh thứ nhất chuyển động trong bối cảnh và tông màu của ảnh thứ hai",
      "images": [
        {"url": "https://example.com/start.png"},
        {"url": "https://example.com/style.png"}
      ],
      "duration": 6,
      "size": "16:9"
    }'
  ```

- **Bước 2: Truy vấn tiến độ nhiệm vụ**
  ```bash
  curl "http://localhost:18610/v1/videos/task_xyz789" \
    -H "Authorization: Bearer m2a_your_secret_key"
  ```
  Khi hoàn tất sẽ trả về:
  ```json
  {
    "id": "task_xyz789",
    "status": "completed",
    "progress": 100,
    "result": {
      "url": "http://localhost:18610/v1/media/vid_xyz789.mp4"
    }
  }
  ```

---

## ⚙️ Danh Mục Biến Môi Trường Cấu Hình

| Tên biến | Giá trị mặc định | Vai trò & Mô tả |
|---|---|---|
| `MUSE2API_KEY` | Tự động tạo | Khóa xác thực cho Bảng điều khiển quản trị và API (bắt đầu bằng `m2a_`) |
| `MUSE2API_HOST` | `0.0.0.0` | Địa chỉ IP lắng nghe |
| `MUSE2API_PORT` | `18610` | Cổng chạy dịch vụ |
| `MUSE2API_PUBLIC_BASE` | *(trống)* | Tiền tố URL công khai bên ngoài; khi để trống giao diện quản trị tự nhận diện theo địa chỉ truy cập |
| `MUSE2API_CHROMIUM` | Tự động dò tìm | Đường dẫn đầy đủ tới tệp thực thi trình duyệt Chromium / Chrome |
| `MUSE2API_CDP_PORT` | `19210` | Cổng giao tiếp gỡ lỗi CDP nội bộ |
| `MUSE2API_CONCURRENCY` | `2` | Số lượng tác vụ tạo nội dung chạy đồng thời tối đa |
| `MUSE2API_IMAGE_TIMEOUT` | `240` | Giới hạn thời gian chờ tạo ảnh (giây) |
| `MUSE2API_VIDEO_TIMEOUT` | `600` | Giới hạn thời gian chờ tạo video (giây) |
| `MUSE2API_CHAT_TIMEOUT` | `300` | Giới hạn thời gian chờ phản hồi hội thoại (giây) |
| `MUSE2API_KEEPALIVE_DISABLED_ACCOUNTS` | `0` | Đặt là `1` nếu muốn tự động gia hạn phiên ngầm cho cả các tài khoản đang tắt thủ công |
| `MUSE2API_REF_IMAGE_LOCAL_FILES` | `0` | Mặc định cấm đọc đường dẫn tệp cục bộ trên máy chủ; chỉ bật `1` trong môi trường đơn người dùng tin cậy |
| `MUSE2API_REF_IMAGE_PRIVATE_FETCH` | `0` | Mặc định chỉ cho phép URL công cộng, kiểm tra lại DNS/redirect ở từng bước và ghim IP đã xác thực; chỉ đặt `1` khi cần cho phép URL nội bộ/localhost |

Hai cờ an toàn mặc định đều là `0`: toàn bộ endpoint tạo ảnh, chỉnh sửa ảnh, tác vụ ảnh và video đều từ chối đường dẫn cục bộ trên máy chủ cũng như URL mạng nội bộ/loopback. Data URL, chuỗi Base64 hợp lệ và URL công cộng hoạt động bình thường. Các lỗi vi phạm chính sách, tải thất bại, sai MIME hoặc vượt dung lượng đều trả về ngay HTTP 400 trước khi tạo tác vụ nền.

Kiểm thử hồi quy an toàn ảnh tham chiếu (mô phỏng DNS & HTTP, không cần mạng ngoài hay tài khoản thật):

```bash
python tests/test_ref_image_safety.py
```

---

## 🧪 Ghi Chú Kỹ Thuật & Kiểm Thử Hồi Quy

### 1. Kiểm thử lựa chọn Media
Xác minh cơ chế loại trừ ảnh xem trước tải lên, khử trùng lặp kết quả, loại trừ tệp đính kèm lịch sử, tải xuống đúng nguồn đã chọn và dừng sớm khi đọc ảnh tham chiếu thất bại (chạy offline với Chromium cục bộ, không tiêu tốn hạn mức):

```bash
python tests/test_media_selection.py
```

*(Nếu trình duyệt không nằm trong `PATH`, hãy đặt biến `MUSE2API_CHROMIUM` trỏ tới tệp thực thi Chrome/Edge/Chromium).*

### 2. Tác vụ tạo ảnh bất đồng bộ qua Reverse Proxy / CDN
Để tránh bị CDN hoặc Reverse Proxy ngắt kết nối khi tạo ảnh lâu, các client sản xuất nên dùng cơ chế gửi nhanh + polling:

1. Gửi `POST /v1/images/tasks` (cùng cấu trúc JSON với `/v1/images/generations`, khuyến nghị kèm header `Idempotency-Key` ổn định) — hoặc truyền `"async": true` vào `/v1/images/generations` và `/v1/images/edits`.
2. Nhận HTTP 202 cùng `id`, gọi `GET /v1/images/tasks/{id}` mỗi 3 giây.
3. Khi `status=completed`, đọc `url` hoặc `data[0]`; khi `status=failed`, đọc `error`.

```bash
python tests/test_async_images.py
python tests/test_vm_wait.py engine.py --assert
```

### 3. Chẩn đoán sức khỏe phiên làm việc (`/api/session`)
Yêu cầu giữ phiên xuất phát từ **IP đầu ra của máy chủ triển khai** chứ không phải trình duyệt xuất Cookie:
- `HTTP 401`: Upstream từ chối xác thực → kiểm tra đăng nhập trên `muse.ai` và nhập lại Cookie.
- `HTTP 403`: Truy cập bị từ chối do giới hạn vùng/IP đầu ra của máy chủ → **không đồng nghĩa Cookie hết hạn**.
- `HTTP 429`, `5xx`, lỗi mạng hoặc không trả về `assigned`: Giữ nguyên trạng thái tài khoản đã xác nhận trước đó và ghi chú chi tiết để chẩn đoán.

```bash
python tests/test_session_health.py
```

---

## 🔒 Bảo Mật & Quyền Riêng Tư

- **Không rò rỉ dữ liệu**: Toàn bộ dữ liệu của phần mềm (bao gồm thông tin đăng nhập tài khoản, hàng đợi nhiệm vụ, tệp media) đều được lưu trữ cục bộ trong thư mục `data/`, không phụ thuộc bất kỳ dịch vụ theo dõi hay máy chủ trung gian bên thứ ba nào.
- **Tuân thủ mã nguồn mở**: Dự án chỉ phục vụ mục đích nghiên cứu kỹ thuật, tự động hóa vận hành hệ thống và kiểm thử tự động. Vui lòng không sử dụng vào các mục đích vi phạm điều khoản dịch vụ của nền tảng Meta hoặc quy định pháp luật hiện hành.

---

## 🤝 Liên Kết Cộng Đồng & Lời Cảm Ơn Đóng Góp (Contributors)

Dự án liên kết cùng **[Cộng đồng LINUX DO (https://linux.do/)](https://linux.do/)**. Xin chân thành cảm ơn các nhà phát triển đã đóng góp mã nguồn và tối ưu tính năng cho MUSE2API:

- 🌟 **[@cpt-kenvie](https://github.com/cpt-kenvie)** (PR [#2](https://github.com/czg86389-hub/muse2api/pull/2)) — Sửa lỗi Docker Compose đọc biến môi trường `.env` và ghi đè cấu hình mẫu
- 🌟 **[@djs-91](https://github.com/djs-91)** (PR [#9](https://github.com/czg86389-hub/muse2api/pull/9)) — Sửa lỗi phân giải Base URL trên trang quản trị khi chưa cấu hình `MUSE2API_PUBLIC_BASE`
- 🌟 **[@toby-bridges](https://github.com/toby-bridges)** (PR [#8](https://github.com/czg86389-hub/muse2api/pull/8)) — Tương thích giao diện đa ngôn ngữ của muse.ai, xác nhận tải tệp đính kèm, trạng thái nút Stop và phân biệt video với ảnh bìa
- 🌟 **[@LF2023](https://github.com/LF2023)** (PR [#18](https://github.com/czg86389-hub/muse2api/pull/18)) — Khắc phục lỗi chọn nhầm ảnh tĩnh bìa video dựa trên `tid`
- 🌟 **[@wuliaolaozi](https://github.com/wuliaolaozi)** (PR [#27](https://github.com/czg86389-hub/muse2api/pull/27)) — Hỗ trợ đọc hạn mức đa ngôn ngữ và cải thiện thông báo lỗi trên trang quản trị
- 🌟 **[@CarloCPP](https://github.com/CarloCPP)** (PR [#6](https://github.com/czg86389-hub/muse2api/pull/6), [#26](https://github.com/czg86389-hub/muse2api/pull/26)) — Đóng góp Tampermonkey Userscript nhập tài khoản 1 chạm và tinh gọn kiểm tra Cookie cốt lõi
- 🌟 **[@gr219](https://github.com/gr219)** (PR [#31](https://github.com/czg86389-hub/muse2api/pull/31)) — Xây dựng cơ chế chuyển đổi đa ngôn ngữ động cho trang quản trị và Chrome Extension
- 🌟 **[@Yeadon8888](https://github.com/Yeadon8888)** (PR [#32](https://github.com/czg86389-hub/muse2api/pull/32)) — Bổ sung hỗ trợ nhiều ảnh tham chiếu có thứ tự cho tạo ảnh, chỉnh sửa ảnh và ảnh sinh video
- 🌟 **[@pandalaohe](https://github.com/pandalaohe)** (PR [#24](https://github.com/czg86389-hub/muse2api/pull/24)) — Xây dựng chính sách bảo mật tệp cục bộ/URL nội bộ, kiểm tra chuyển hướng và chống tấn công DNS Rebinding cho ảnh tham chiếu

---

## 📚 Hệ Thống Tài Liệu Kỹ Thuật (Documentation)

Chi tiết toàn bộ kiến trúc kỹ thuật và hướng dẫn phát triển được lưu trữ tại thư mục `docs/`:
- 📂 [Mục Lục Tổng Quan](docs/README.md)
- 🏗️ [Kiến Trúc & Thiết Kế](docs/01-tong-quan/kien-truc.md)
- 📁 [Cấu Trúc Thư Mục](docs/01-tong-quan/cau-truc-thu-muc.md)
- ⚙️ [Cấu Hình & Biến Môi Trường](docs/02-cai-dat/cau-hinh.md)
- 🔌 [Tài Liệu Tra Cứu API](docs/06-api/tong-quan-api.md)
- 🔄 [Sơ Đồ Tuần Tự (Sequence Diagrams)](docs/05-luong-xu-ly/chat-streaming.md)
- 🧪 [Hướng Dẫn Kiểm Thử](docs/07-huong-dan-phat-trien/kiem-thu.md)
- 🤝 [Quy Chuẩn Đóng Góp](CONTRIBUTING.md)

---

## 🤝 Đóng Góp & Giấy Phép (Contributing & License)

- **Quy chuẩn đóng góp**: Vui lòng đọc kỹ hướng dẫn tại [CONTRIBUTING.md](CONTRIBUTING.md).
- **Lịch sử cập nhật**: Xem chi tiết tại [CHANGELOG.md](CHANGELOG.md).
- **Giấy phép**: Dự án được phát hành theo giấy phép mã nguồn mở [MIT License](LICENSE).
