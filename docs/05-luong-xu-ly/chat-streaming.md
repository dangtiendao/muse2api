# Luồng Xử Lý: Hội Thoại & Stream SSE (`/v1/chat/completions`)

---

## 1. Mô Tả Luồng Nghiệp Vụ

Luồng hội thoại xử lý yêu cầu trò chuyện văn bản và viết mã nguồn, hỗ trợ cả hai chế độ:
1. **Chế độ Stream (`stream=True`)**: Trả về dữ liệu theo định dạng Server-Sent Events (SSE) theo chuẩn OpenAI, ký tự đầu tiên phản hồi cực nhanh sau **2~3 giây**.
2. **Chế độ Đồng bộ (`stream=False`)**: Gom toàn bộ câu trả lời hoàn chỉnh và trả về một đối tượng JSON duy nhất.

Cơ chế **Warm-Tab Affinity** được áp dụng: Nếu trang web đang ở trạng thái sạch, không có tệp đính kèm và số lượng tin nhắn ít hơn 24 bong bóng, hệ thống tái sử dụng ngay tab trình duyệt hiện có mà không reload, giảm thiểu độ trễ bắt đầu.

---

## 2. Sơ Đồ Tuần Tự (Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    actor Client as Ứng dụng Khách (NextChat/SDK)
    participant API as app.py (/v1/chat/completions)
    participant Lock as ConcurrencyLock
    participant Pool as AccountPoolManager
    participant Store as store.py
    participant Engine as engine.py (MuseEngine)
    participant CDP as Chromium CDP Tab
    participant Muse as muse.ai Cloud

    Client->>API: POST /v1/chat/completions {messages, model, stream: true}
    API->>API: Xác thực API Key (auth)
    API->>Lock: acquire() [Giữ slot đồng thời]
    API->>Pool: acquire(preferred_id)
    Pool->>Store: pick_account() [Ưu tiên Warm Tab]
    Store-->>Pool: Trả về tài khoản khả dụng (Account A)
    Pool-->>API: Gán Account A

    API->>Engine: chat_stream(cookies, prompt, account_id)
    Engine->>Engine: ensure_page() & reset_thread(for_chat=True)
    alt Tab đang ấm (Warm Tab)
        Engine->>CDP: Tái sử dụng kết nối WebSocket hiện có
    else Tab mới / Đổi tài khoản
        Engine->>CDP: Mở Incognito Context & Bơm Cookies
        CDP->>Muse: Kết nối WebSocket kênh trò chuyện
    end

    Engine->>CDP: _send(prompt) qua React prototype setter
    CDP->>Muse: Gửi tin nhắn lên đám mây

    loop Polling siêu nhanh mỗi 60ms (_poll_chat)
        Engine->>CDP: Kiểm tra text mới và nút Stop
        CDP-->>Engine: Phát hiện token mới
        Engine-->>API: yield delta_chunk
        API-->>Client: data: {"choices": [{"delta": {"content": "..."}}]}
    end

    Muse-->>CDP: Hoàn thành sinh câu trả lời (Nút Stop biến mất)
    Engine-->>API: Kết thúc Stream Generator
    API-->>Client: data: [DONE]

    API->>Pool: release(Account A)
    API->>Lock: release() [Trả slot đồng thời]
```

---

## 3. Các Điểm Cần Lưu Ý
- Nếu kết nối giữa Client và Server bị ngắt sớm (Client Abort), `Request.is_disconnected()` sẽ kích hoạt `stop_event.set()`, lập tức dừng vòng lặp polling trên engine để tiết kiệm tài nguyên máy chủ.

---

## 4. Liên kết Liên quan
- [Module App API](../03-module/app-api.md)
- [Module Engine Core](../03-module/engine-core.md)
- [Chi Tiết API Chat Completions](../06-api/chat-completions.md)
- [Mục lục Tài liệu](../README.md)
