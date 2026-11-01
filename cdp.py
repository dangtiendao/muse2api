"""Client Chrome DevTools Protocol tối giản (Minimalist Chrome DevTools Protocol Client).

Module này cung cấp client giao tiếp trực tiếp với Chromium/Chrome thông qua giao thức CDP:
  - Kết nối WebSocket hai chiều tới trình duyệt hoặc tab cụ thể.
  - Gửi lệnh CDP đồng bộ (synchronous RPC qua request ID) có thread-lock bảo vệ.
  - Thực thi mã JavaScript trong ngữ cảnh trang web (Runtime.evaluate).
  - Lắng nghe luồng sự kiện (CDP event pumping).
  - Truy vấn danh sách target/version của trình duyệt qua HTTP JSON.
"""
from __future__ import annotations

import json
import time
import threading

import requests
import websocket


class CDPError(RuntimeError):
    """Ngoại lệ ném ra khi trình duyệt trả về phản hồi lỗi cho một lệnh CDP cụ thể."""
    pass


class CDP:
    """Lớp giao tiếp với trình duyệt Chromium qua kết nối WebSocket sử dụng giao thức DevTools Protocol.
    
    Attributes:
        ws: Kết nối WebSocket đang hoạt động.
        timeout (float): Thời gian chờ phản hồi tối đa (giây).
        _id (int): Bộ đếm request ID tăng dần để ghép cặp yêu cầu - phản hồi.
        _lock (threading.Lock): Khóa đồng bộ hóa đảm bảo an toàn đa luồng khi gửi lệnh.
    """

    def __init__(self, ws_url: str, timeout: float = 90.0, max_size: int = 256 << 20):
        """Khởi tạo kết nối WebSocket tới endpoint DevTools của trình duyệt.
        
        Args:
            ws_url (str): URL WebSocket của target hoặc browser (ví dụ: ws://127.0.0.1:19210/devtools/page/...).
            timeout (float, optional): Thời gian timeout cho socket (mặc định: 90.0 giây).
            max_size (int, optional): Kích thước tin nhắn tối đa nhận qua WebSocket (mặc định: 256 MiB).
        """
        self.ws = websocket.create_connection(ws_url, timeout=timeout, max_size=max_size)
        self.timeout = timeout
        self._id = 0
        self._lock = threading.Lock()

    def send(self, method: str, params: dict | None = None, timeout: float | None = None) -> dict:
        """Gửi lệnh RPC theo chuẩn giao thức CDP và chờ phản hồi tương ứng.
        
        Args:
            method (str): Tên phương thức CDP (ví dụ: 'Page.navigate', 'Runtime.evaluate').
            params (dict | None, optional): Tham số của lệnh. Mặc định là None (sẽ chuyển thành rỗng).
            timeout (float | None, optional): Thời gian chờ phản hồi riêng cho lệnh này (giây).
            
        Returns:
            dict: Đối tượng JSON phản hồi từ trình duyệt chứa kết quả trả về trong khóa 'result'.
            
        Raises:
            CDPError: Khi trình duyệt trả về lỗi trong phản hồi.
            TimeoutError: Khi không nhận được phản hồi trước thời hạn deadline.
        """
        with self._lock:
            self._id += 1
            mid = self._id
            self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
            deadline = time.time() + (timeout or self.timeout)
            while time.time() < deadline:
                try:
                    msg = json.loads(self.ws.recv())
                except websocket.WebSocketTimeoutException:
                    continue
                except Exception:  # noqa: BLE001
                    continue
                # Ghép đúng request ID để đảm bảo lấy đúng kết quả của lệnh vừa gửi
                if msg.get("id") == mid:
                    if "error" in msg:
                        raise CDPError(f"{method}: {msg['error']}")
                    return msg
            raise TimeoutError(f"CDP {method} 超时 (Timeout)")

    def js(self, expr: str, await_promise: bool = False, timeout: float | None = None):
        """Thực thi một biểu thức JavaScript trong context của trang hiện tại và trả về giá trị kết quả.
        
        Args:
            expr (str): Chuỗi mã JavaScript cần thực thi.
            await_promise (bool, optional): Có chờ Promise giải quyết xong hay không. Mặc định là False.
            timeout (float | None, optional): Thời gian timeout thực thi (giây).
            
        Returns:
            Any: Giá trị trực tiếp của biểu thức (nếu có thuộc tính 'value') hoặc cấu trúc RemoteObject.
        """
        r = self.send("Runtime.evaluate",
                      {"expression": expr, "returnByValue": True,
                       "awaitPromise": await_promise}, timeout)
        res = r.get("result", {}).get("result", {})
        if "value" in res:
            return res["value"]
        return r.get("result")

    def pump(self, seconds: float, on_event=None, sock_timeout: float = 2.0):
        """Lắng nghe liên tục các sự kiện CDP phát ra từ trình duyệt trong khoảng thời gian nhất định.
        
        Args:
            seconds (float): Tổng thời gian duy trì vòng lặp lắng nghe (giây).
            on_event (callable, optional): Hàm callback nhận tham số là dictionary sự kiện `ev`.
            sock_timeout (float, optional): Timeout đọc socket cho mỗi lần thử (mặc định: 2.0 giây).
        """
        end = time.time() + seconds
        self.ws.settimeout(sock_timeout)
        while time.time() < end:
            try:
                ev = json.loads(self.ws.recv())
            except Exception:  # noqa: BLE001
                continue
            if on_event and "method" in ev:
                on_event(ev)

    def close(self):
        """Đóng kết nối WebSocket an toàn và giải phóng tài nguyên mạng."""
        with self._lock:
            try:
                self.ws.close()
            except Exception:  # noqa: BLE001
                pass


def http_json(url: str, timeout: float = 5.0) -> dict | list:
    """Helper gửi HTTP GET tới cổng debug của Chromium và phân giải kết quả JSON.
    
    Args:
        url (str): Địa chỉ HTTP endpoint (ví dụ: http://127.0.0.1:19210/json/version).
        timeout (float, optional): Thời gian chờ phản hồi HTTP (mặc định: 5.0 giây).
        
    Returns:
        dict | list: Dữ liệu phân giải từ JSON.
    """
    return requests.get(url, timeout=timeout).json()
