#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""muse2api Cookie 助手 —— 一键把 muse.ai 的登录 cookie 导入账号池 (Cookie Exporter Helper).

Tại sao cần script này?
  Các cookie định danh phiên làm việc của muse.ai (đặc biệt là hatch_sess và hatch_vml) mang cờ httpOnly,
  nghĩa là mã JavaScript thông thường chạy trên web console (document.cookie) KHÔNG THỂ đọc được.
  Chỉ có tầng giao thức gỡ lỗi trình duyệt (Chrome DevTools Protocol - CDP) mới có quyền đọc được chúng.
  Do đó không thể dùng Bookmarklet hay Console script thông thường, mà cần script điều khiển CDP này.

Cơ chế hoạt động:
  1. Khởi chạy một cửa sổ Chromium/Chrome độc lập với User Data Profile tạm thời (không ảnh hưởng dữ liệu duyệt web cá nhân).
  2. Người dùng đăng nhập tài khoản trên cửa sổ muse.ai vừa mở.
  3. Script lắng nghe qua WebSocket CDP (lệnh Storage.getCookies), ngay khi thấy đủ 2 cookie cốt lõi
     (hatch_sess, hatch_vml) sẽ tự động POST lên API quản trị `/admin/accounts` của muse2api.
  4. Đóng cửa sổ trình duyệt và dọn dẹp file tạm.

Cách sử dụng:
  python get_muse_cookie.py --base http://your-server-ip:18610 --key m2a_xxx
  python get_muse_cookie.py --base http://your-server-ip:18610 --key m2a_xxx --label acc-01

Hoặc thiết lập trước qua biến môi trường:
  set MUSE2API_BASE=http://your-server-ip:18610     (Windows)
  set MUSE2API_KEY=m2a_xxx
  export MUSE2API_BASE=...                          (macOS / Linux)
  export MUSE2API_KEY=...

Yêu cầu môi trường:
  Chỉ phụ thuộc thư viện chuẩn của Python (Python 3.8+), không cần chạy `pip install`.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

SITE = "https://muse.ai/"
CDP_PORT = 9333
ESSENTIAL = ("hatch_sess", "hatch_vml")
DOMAIN_HINT = "muse.ai"


# ---------------------------------------------------------------- Xuất log ra Console
def say(msg=""):
    """In thông điệp ra màn hình, tự động xử lý mã hóa UTF-8 an toàn trên Windows Console cũ."""
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:                     # Xử lý console Windows không hỗ trợ utf-8 nguyên bản
        print(msg.encode("utf-8", "replace").decode("utf-8", "replace"), flush=True)


def init_console():
    """Cấu hình encoding UTF-8 cho luồng stdout và stderr của tiến trình (Python 3.7+)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")   # Python 3.7+
        except Exception:                          # noqa: BLE001
            pass


# ---------------------------------------------------------------- WebSocket Client tối giản
class WS:
    """Client WebSocket RFC6455 tối giản tự xây dựng dành riêng cho giao tiếp CDP (không cần thư viện ngoài)."""

    def __init__(self, url: str, timeout: float = 15.0):
        """Khởi tạo socket TCP và thực hiện cú bắt tay nâng cấp giao thức HTTP Upgrade sang WebSocket.
        
        Args:
            url (str): Địa chỉ WebSocket ws://...
            timeout (float): Thời gian chờ kết nối tối đa (giây).
        """
        assert url.startswith("ws://"), url
        rest = url[5:]
        hostport, _, path = rest.partition("/")
        path = "/" + path
        host, _, port = hostport.partition(":")
        port = int(port or 80)

        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (f"GET {path} HTTP/1.1\r\n"
               f"Host: {host}:{port}\r\n"
               "Upgrade: websocket\r\n"
               "Connection: Upgrade\r\n"
               f"Sec-WebSocket-Key: {key}\r\n"
               "Sec-WebSocket-Version: 13\r\n\r\n")
        self.sock.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("WebSocket 握手被断开 / Bắt tay WebSocket bị ngắt kết nối")
            buf += chunk
        status = buf.split(b"\r\n", 1)[0]
        if b" 101" not in status:
            raise ConnectionError(f"WebSocket 握手失败: {status!r} / Bắt tay WebSocket thất bại")
        self._id = 0

    # --- Đóng gói và gửi khung tin (Frame) ---
    def _frame(self, opcode: int, payload: bytes):
        """Đóng gói khung tin WebSocket theo chuẩn RFC 6455 có che mặt nạ (Client masking)."""
        head = bytearray([0x80 | opcode])
        n = len(payload)
        if n < 126:
            head.append(0x80 | n)
        elif n < 65536:
            head.append(0x80 | 126)
            head += struct.pack(">H", n)
        else:
            head.append(0x80 | 127)
            head += struct.pack(">Q", n)
        mask = os.urandom(4)
        head += mask
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(bytes(head) + masked)

    def send_text(self, text: str):
        """Gửi khung tin dạng văn bản UTF-8 (Opcode 0x1)."""
        self._frame(0x1, text.encode("utf-8"))

    # --- Đọc nhận khung tin ---
    def _read(self, n: int) -> bytes:
        """Đọc chính xác n byte từ socket mạng."""
        out = b""
        while len(out) < n:
            chunk = self.sock.recv(n - len(out))
            if not chunk:
                raise ConnectionError("连接已关闭 / Kết nối đã đóng")
            out += chunk
        return out

    def recv_text(self) -> str:
        """Đọc và giải mã một khung tin văn bản hoàn chỉnh từ WebSocket, tự động phản hồi Ping/Pong."""
        while True:
            h = self._read(2)
            opcode = h[0] & 0x0F
            masked = h[1] & 0x80
            ln = h[1] & 0x7F
            if ln == 126:
                ln = struct.unpack(">H", self._read(2))[0]
            elif ln == 127:
                ln = struct.unpack(">Q", self._read(8))[0]
            mk = self._read(4) if masked else None
            data = self._read(ln) if ln else b""
            if mk:
                data = bytes(b ^ mk[i % 4] for i, b in enumerate(data))
            if opcode == 0x1:
                return data.decode("utf-8", "replace")
            if opcode == 0x9:                       # Xử lý frame Ping từ server -> gửi lại Pong (0xA)
                self._frame(0xA, data)
            elif opcode == 0x8:
                raise ConnectionError("服务端关闭了连接 / Máy chủ đã đóng kết nối")
            # Bỏ qua các frame khác (Pong, binary, fragmentation)

    def call(self, method: str, params: dict | None = None,
             timeout: float = 20.0) -> dict:
        """Thực thi gọi hàm CDP RPC đồng bộ và chờ kết quả trả về tương ứng theo ID."""
        self._id += 1
        mid = self._id
        self.send_text(json.dumps({"id": mid, "method": method,
                                   "params": params or {}}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                msg = json.loads(self.recv_text())
            except socket.timeout:
                continue
            except ConnectionError:
                raise
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})
        raise TimeoutError(f"CDP {method} 超时 (Timeout)")

    def close(self):
        """Đóng kết nối socket an toàn."""
        try:
            self.sock.close()
        except Exception:                              # noqa: BLE001
            pass


# ---------------------------------------------------------------- Tìm kiếm đường dẫn trình duyệt
CHROME_EXES = ("chrome.exe", "msedge.exe", "brave.exe", "chromium.exe")


def _win_registry_paths() -> list[str]:
    """Tìm đường dẫn trình duyệt từ khóa App Paths trong Windows Registry.

    Không thể chỉ dựa vào biến môi trường %ProgramFiles% vì trong một số môi trường shell tinh giản
    biến này có thể bị rỗng.
    """
    out: list[str] = []
    try:
        import winreg
    except ImportError:
        return out
    sub = (r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths")
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for exe in CHROME_EXES:
            for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
                try:
                    with winreg.OpenKey(root, sub + "\\" + exe, 0,
                                        winreg.KEY_READ | view) as k:
                        val = winreg.QueryValueEx(k, "")[0]
                        if val:
                            out.append(os.path.expandvars(val))
                except OSError:
                    continue
    return out


def _win_common_paths() -> list[str]:
    """Danh sách các đường dẫn cài đặt thông dụng trên hệ điều hành Windows."""
    roots = [os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"),
             os.environ.get("LOCALAPPDATA"), r"C:\Program Files",
             r"C:\Program Files (x86)"]
    rel = [
        r"Google\Chrome\Application\chrome.exe",
        r"Microsoft\Edge\Application\msedge.exe",
        r"BraveSoftware\Brave-Browser\Application\brave.exe",
    ]
    return [os.path.join(r, p) for r in roots if r for p in rel]


def find_chrome() -> str | None:
    """Tự động tìm kiếm file thực thi của trình duyệt dựa trên nền tảng hệ điều hành (Windows, macOS, Linux).
    
    Returns:
        str | None: Đường dẫn tới file thực thi hoặc None nếu không tìm thấy.
    """
    if sys.platform == "win32":
        cands = _win_registry_paths() + _win_common_paths()
    elif sys.platform == "darwin":
        cands = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        ]
    else:
        cands = ["google-chrome", "google-chrome-stable", "chromium",
                 "chromium-browser", "microsoft-edge", "brave-browser"]
    seen = set()
    for c in cands:
        if not c or c in seen:
            continue
        seen.add(c)
        if os.path.isfile(c):
            return c
        if not os.path.isabs(c):
            w = shutil.which(c)
            if w:
                return w
    return None


def wait_cdp(port: int, timeout: float = 30.0) -> str:
    """Lắng nghe cổng gỡ lỗi CDP cho đến khi sẵn sàng và trả về URL WebSocket ở cấp trình duyệt."""
    deadline = time.time() + timeout
    url = f"http://127.0.0.1:{port}/json/version"
    last = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                return json.load(r)["webSocketDebuggerUrl"]
        except Exception as exc:                       # noqa: BLE001
            last = exc
            time.sleep(0.5)
    raise RuntimeError(f"浏览器调试端口没起来（{port}）：{last} / Cổng debug trình duyệt chưa sẵn sàng ({port}): {last}")


# ---------------------------------------------------------------- Đọc Cookie qua CDP
def read_cookies(ws: WS) -> dict[str, dict]:
    """Dùng lệnh cấp trình duyệt `Storage.getCookies` để lấy toàn bộ cookie, sau đó lọc tên miền muse.ai.

    Điểm mấu chốt: CDP đọc được toàn bộ cookie có cờ httpOnly mà JavaScript trang web không thể lấy được.
    
    Returns:
        dict[str, dict]: Cấu trúc cookie gồm giá trị, thời hạn hết hạn và cờ httpOnly.
    """
    res = ws.call("Storage.getCookies", {}, timeout=20)
    out: dict[str, dict] = {}
    for c in res.get("cookies", []):
        domain = (c.get("domain") or "").lstrip(".")
        if DOMAIN_HINT not in domain:
            continue
        name = c.get("name")
        if not name:
            continue
        try:
            exp = int(float(c.get("expires", -1)))
        except (TypeError, ValueError):
            exp = -1
        out[name] = {"value": c.get("value", ""), "expires": exp,
                     "httpOnly": bool(c.get("httpOnly"))}
    return out


# ---------------------------------------------------------------- Đẩy Cookie lên máy chủ
def upload(base: str, key: str, label: str, cookies: dict[str, dict]) -> dict:
    """Gửi yêu cầu HTTP POST để đẩy cookie tài khoản vừa đọc được lên máy chủ muse2api.
    
    Args:
        base (str): Địa chỉ máy chủ muse2api (ví dụ: http://127.0.0.1:18610).
        key (str): Khóa bí mật API Key quản trị.
        label (str): Nhãn đại diện cho tài khoản.
        cookies (dict): Danh sách cookies đã thu thập.
        
    Returns:
        dict: Phản hồi JSON xác nhận từ máy chủ.
    """
    payload = {
        "label": label,
        "cookies": {k: v["value"] for k, v in cookies.items()},
        "expires": {k: v["expires"] for k, v in cookies.items() if v["expires"] > 0},
    }
    req = urllib.request.Request(
        base.rstrip("/") + "/admin/accounts",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        raise RuntimeError(f"上传失败 HTTP {e.code}: {detail} / Tải lên thất bại HTTP {e.code}: {detail}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"连不上 {base}：{e.reason} / Không thể kết nối tới {base}: {e.reason}") from None


def fmt_ts(ts: int) -> str:
    """Định dạng timestamp dạng số sang chuỗi hiển thị ngày giờ thân thiện."""
    if ts <= 0:
        return "会话级 (Session)"
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))


# ---------------------------------------------------------------- Quy trình thực thi chính
def main() -> int:
    """Điều phối toàn bộ luồng khởi động trình duyệt, bắt cookie và nhập tài khoản."""
    init_console()
    ap = argparse.ArgumentParser(
        description="把 muse.ai 的登录 cookie 一键导入 muse2api 账号池 / Tự động xuất cookie đăng nhập muse.ai sang muse2api")
    ap.add_argument("--base", default=os.environ.get("MUSE2API_BASE", ""),
                    help="muse2api 地址，如 http://your-server-ip:18610")
    ap.add_argument("--key", default=os.environ.get("MUSE2API_KEY", ""),
                    help="API Key（m2a_ 开头）")
    ap.add_argument("--label", default="", help="账号标签，如 acc-01")
    ap.add_argument("--timeout", type=int, default=300,
                    help="等待登录的最长秒数，默认 300 (Thời gian chờ tối đa)")
    ap.add_argument("--keep-open", action="store_true",
                    help="上传成功后不关闭浏览器窗口 (Giữ cửa sổ trình duyệt không đóng)")
    ap.add_argument("--port", type=int, default=CDP_PORT,
                    help=f"调试端口，默认 {CDP_PORT} (Cổng debug)")
    ap.add_argument("--chrome", default="", help="手动指定浏览器可执行文件路径 (Đường dẫn thủ công tới Chrome)")
    args = ap.parse_args()

    say("=" * 66)
    say("  muse2api Cookie 助手 (Cookie Importer Helper)")
    say("=" * 66)
    say()

    if not args.base or not args.key:
        say("✗ 缺少参数。请这样运行：/ Thiếu tham số bắt buộc. Cú pháp chạy:")
        say("    python get_muse_cookie.py --base https://your-server-ip:18610 --key m2a_xxx")
        say()
        say("  （这两个值可以在 muse2api 管理页面的「接入信息」里复制 / Có thể sao chép tại trang Admin）")
        return 2
    if not args.label:
        args.label = "muse-" + time.strftime("%m%d-%H%M")

    chrome = args.chrome or find_chrome()
    if not chrome:
        say("✗ 没找到 Chrome / Edge 浏览器。/ Không tìm thấy trình duyệt Chrome hoặc Edge.")
        say("  请先安装 Chrome，或用 --chrome \"完整路径\" 手动指定。")
        return 3
    say(f"Trình duyệt phát hiện: {chrome}")

    profile = os.path.join(tempfile.gettempdir(), "muse2api-cookie-profile")
    shutil.rmtree(profile, ignore_errors=True)
    os.makedirs(profile, exist_ok=True)

    args_cmd = [
        chrome,
        f"--remote-debugging-port={args.port}",
        f"--user-data-dir={profile}",
        "--no-first-run", "--no-default-browser-check",
        # Thêm cờ --no-sandbox và --disable-gpu để tránh crash tiến trình con trong môi trường container/sandbox
        "--no-sandbox", "--disable-gpu",
        "--new-window", SITE,
    ]
    say("Đang khởi tạo một cửa sổ trình duyệt độc lập (không ảnh hưởng tới dữ liệu cá nhân)...")
    proc = subprocess.Popen(args_cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)

    ws = None
    try:
        try:
            ws_url = wait_cdp(args.port, 30)
        except RuntimeError as exc:
            say(f"✗ {exc}")
            say("  Gợi ý: Nếu Chrome đang mở, hãy đóng hẳn các cửa sổ Chrome đang chạy rồi thử lại.")
            return 4
        ws = WS(ws_url)

        say()
        say("┌" + "─" * 64 + "┐")
        say("│  Vui lòng đăng nhập muse.ai trên cửa sổ trình duyệt vừa xuất hiện.     │")
        say("│  Khi thấy giao diện trò chuyện, script sẽ tự động trích xuất cookie.   │")
        say("└" + "─" * 64 + "┘")
        say()

        deadline = time.time() + args.timeout
        got: dict[str, dict] = {}
        last_note = 0.0
        while time.time() < deadline:
            try:
                got = read_cookies(ws)
            except Exception as exc:                    # noqa: BLE001
                say(f"  Đọc cookie gặp lỗi, đang thử lại... ({exc})")
                time.sleep(2)
                continue

            have = [n for n in ESSENTIAL if n in got]
            if len(have) == len(ESSENTIAL):
                break

            now = time.time()
            if now - last_note > 5:
                last_note = now
                left = int(deadline - now)
                say(f"  Đang chờ đăng nhập... Đã bắt được {len(have)}/{len(ESSENTIAL)} cookie cốt lõi "
                    f"({', '.join(have) or 'chưa có'}) - Còn lại {left}s")
            time.sleep(2)
        else:
            say()
            say("✗ Hết thời gian chờ mà chưa đăng nhập thành công.")
            return 5

        say()
        say("✓ Đã thu thập đầy đủ session cookie hợp lệ:")
        say()
        say(f"  {'Tên cookie':<30}{'httpOnly':<10}{'Hạn sử dụng'}")
        say("  " + "-" * 62)
        for name in ESSENTIAL:
            c = got.get(name, {})
            say(f"  {name:<30}{('Có' if c.get('httpOnly') else 'Không'):<10}"
                f"{fmt_ts(c.get('expires', -1))}")
        say()

        say("Đang đồng bộ dữ liệu lên máy chủ muse2api...")
        try:
            r = upload(args.base, args.key, args.label, got)
        except RuntimeError as exc:
            say(f"✗ {exc}")
            say()
            say("  Cookie đã lấy thành công nhưng upload gặp lỗi. Bạn có thể sao chép dòng dưới đây")
            say("  và dán thủ công vào ô 'Nhập tài khoản' trên trang quản trị:")
            say()
            say("  " + "; ".join(f"{k}={v['value']}" for k, v in got.items()))
            return 6

        say()
        say("=" * 66)
        say(f"✓ Đã nhập tài khoản thành công! Nhãn: {r['added'][0]['label']}")
        say(f"  Mã tài khoản ID: {r['added'][0]['id']}")
        say(f"  Tổng cộng {r['added'][0]['cookie_count']} cookie được lưu trữ")
        if r.get("warning"):
            say(f"  ⚠ Cảnh báo: {r['warning']}")
        say()
        say(f"  Mở {args.base.rstrip('/')}/ để xem trạng thái tài khoản trong hồ chứa.")
        say("=" * 66)
        return 0

    finally:
        if ws:
            ws.close()
        if not args.keep_open:
            try:
                proc.terminate()
            except Exception:                           # noqa: BLE001
                pass
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        say()
        say("Thao tác đã bị hủy bởi người dùng.")
        sys.exit(130)
