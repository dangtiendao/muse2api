# API: Hội Thoại Chuẩn Codex (`/v1/responses`)

---

## 1. Thông Tin Endpoint

- **Method**: `POST`
- **Path**: `/v1/responses`
- **Mô tả**: Tương thích với giao thức Responses API thế hệ mới (thường được sử dụng bởi các plugin Codex, Continue hoặc Cursor thế hệ mới).

---

## 2. Cấu Trúc Request Body

```json
{
  "model": "codex",
  "input": "Hoàn thiện hàm tính giai thừa bằng đệ quy",
  "stream": true
}
```
*Ghi chú*: Trường `input` có thể là một chuỗi văn bản đơn giản hoặc một mảng các tin nhắn (tương tự như `messages` trong Chat API).

---

## 3. Cấu Trúc Response

### Chế độ Stream (`stream=true`):
```text
event: response.output_item.added
data: {"type":"response.output_item.added","item":{"type":"message","role":"assistant"}}

event: response.text.delta
data: {"type":"response.text.delta","delta":"def factorial(n):"}

event: response.done
data: {"type":"response.done","response":{"status":"completed"}}
```

### Chế độ Đồng bộ (`stream=false`):
```json
{
  "id": "resp-abc123xyz",
  "object": "response",
  "created_at": 1740000000,
  "model": "codex",
  "status": "completed",
  "output": [
    {
      "id": "msg-xyz",
      "type": "message",
      "role": "assistant",
      "content": [
        {
          "type": "text",
          "text": "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n - 1)"
        }
      ]
    }
  ]
}
```

---

## 4. Liên kết Liên quan
- [API Chat Completions](chat-completions.md)
- [Tổng Quan API](tong-quan-api.md)
- [Mục lục Tài liệu](../README.md)
