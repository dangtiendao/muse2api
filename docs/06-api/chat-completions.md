# API: Hội Thoại Chuẩn OpenAI (`/v1/chat/completions`)

---

## 1. Thông Tin Endpoint

- **Method**: `POST`
- **Path**: `/v1/chat/completions`
- **Mô tả**: Gửi danh sách tin nhắn hội thoại và nhận về câu trả lời từ mô hình. Hỗ trợ cả phản hồi một lần và Server-Sent Events (SSE) streaming.

---

## 2. Cấu Trúc Request Body

```json
{
  "model": "gpt-4o",
  "messages": [
    {
      "role": "system",
      "content": "Bạn là một trợ lý lập trình chuyên nghiệp."
    },
    {
      "role": "user",
      "content": "Hãy viết hàm quicksort bằng Python."
    }
  ],
  "stream": true,
  "temperature": 0.7
}
```

### Chi tiết các trường:
- `model` *(string, bắt buộc)*: Tên mô hình (hỗ trợ alias: `gpt-4o`, `gpt-5`, `claude-sonnet-4`, `deepseek-chat`...).
- `messages` *(array, bắt buộc)*: Danh sách tin nhắn hội thoại, mỗi phần tử gồm `role` (`system`, `user`, `assistant`) và `content` (chuỗi văn bản).
- `stream` *(boolean, tùy chọn, mặc định: false)*: Nếu đặt `true`, dữ liệu sẽ được stream theo chuẩn SSE.
- `tools` *(array, tùy chọn)*: Danh sách định nghĩa functions/tools (nếu bật `MUSE2API_TOOL_PROTOCOL`).

---

## 3. Cấu Trúc Response

### 3.1. Chế độ Stream (`stream=true`)
Dữ liệu trả về qua kết nối SSE (`Content-Type: text/event-stream`):

```text
data: {"id":"chatcmpl-abc123xyz","object":"chat.completion.chunk","created":1740000000,"model":"gpt-4o","choices":[{"index":0,"delta":{"content":"Dưới"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123xyz","object":"chat.completion.chunk","created":1740000000,"model":"gpt-4o","choices":[{"index":0,"delta":{"content":" đây là"},"finish_reason":null}]}

data: [DONE]
```

### 3.2. Chế độ Đồng bộ (`stream=false`)
Dữ liệu JSON hoàn chỉnh (`Content-Type: application/json`):

```json
{
  "id": "chatcmpl-abc123xyz",
  "object": "chat.completion",
  "created": 1740000000,
  "model": "gpt-4o",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Dưới đây là mã nguồn hàm quicksort bằng Python:\n\n```python\ndef quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)\n```"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 85,
    "total_tokens": 110
  }
}
```

---

## 4. Ví Dụ Gọi Bằng cURL & Python

### cURL:
```bash
curl -X POST http://127.0.0.1:18610/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <MUSE2API_KEY>" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Xin chào, bạn là ai?"}],
    "stream": false
  }'
```

### Python (OpenAI SDK):
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:18610/v1",
    api_key="<MUSE2API_KEY>"
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Viết thơ về mùa thu"}],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

---

## 5. Liên kết Liên quan
- [Tổng Quan API](tong-quan-api.md)
- [Sơ Đồ Luồng Chat Streaming](../05-luong-xu-ly/chat-streaming.md)
- [Mục lục Tài liệu](../README.md)
