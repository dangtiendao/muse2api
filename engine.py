"""Engine sinh nội dung Muse: Điều khiển phiên web thực tế để sinh ảnh và video trên muse.ai (Muse Generation Engine Core).

Module lõi chịu trách nhiệm tương tác và điều khiển trực tiếp phiên làm việc web muse.ai:
  - Khởi tạo và quản lý vòng đời tiến trình vô đầu Chromium qua giao thức Chrome DevTools Protocol (CDP).
  - Tách biệt ngữ cảnh đa tài khoản (Multi-Account Browser Context Isolation) bằng `Target.createBrowserContext`.
  - Tự động duy trì phiên đăng nhập và kích hoạt máy ảo đám mây (`/api/session`, `/api/hatch/vm/wake`).
  - Điều khiển giao diện web tự động: định vị composer textarea, inject văn bản, xử lý tải ảnh đính kèm (DataTransfer API).
  - Lắng nghe và trích xuất kết quả đa phương tiện (ảnh hoàn thiện, video hoàn thiện) qua DOM mutation và Blob binary fetching.
  - Hỗ trợ trò chuyện tương tác với khả năng stream thời gian thực (SSE tokens) với độ trễ phản hồi cực thấp (2-3s).

Quy trình tự động hóa đã được kiểm chứng:
  Bơm Cookie -> Mở https://muse.ai/ -> Định vị textarea -> Đặt giá trị văn bản -> Click 'Gửi'
  -> Lắng nghe container kết quả [data-testid^=hatch-chat-attachment-presentation-]
  -> Trích xuất dữ liệu Blob từ thẻ img/video -> Ghi file xuống đĩa.
"""
from __future__ import annotations

import base64
import binascii
import http.client
import ipaddress
import mimetypes
import urllib.error
import urllib.parse
import urllib.request
import json
import logging
import os
import re
import shutil
import socket
import subprocess
import threading
import time
import uuid
import unicodedata

from cdp import CDP, http_json

log = logging.getLogger("muse2api")

ATT_SEL = '[data-testid^="hatch-chat-attachment-presentation-"]'
MAX_REFERENCE_IMAGES = 4
MAX_REFERENCE_IMAGE_BYTES = 10 * 1024 * 1024
MAX_REFERENCE_TOTAL_BYTES = 24 * 1024 * 1024

# Cookie cốt lõi quyết định trạng thái tài khoản (thiếu hoặc hết hạn = phiên vô hiệu)
# Lưu ý: hatch_gw là bộ nhớ đệm định tuyến gateway; sự sống còn của phiên chủ yếu phụ thuộc vào hatch_sess và hatch_vml, thiếu gw vẫn có thể gia hạn và sinh nội dung bình thường
ESSENTIAL_COOKIES = ("hatch_sess", "hatch_vml")


class MuseAuthError(RuntimeError):
    """Ngoại lệ khi xác thực tài khoản muse.ai thất bại (hết hạn session cookie hoặc bị logout)."""
    pass


class MuseGenerationError(RuntimeError):
    """Ngoại lệ chung trong quá trình điều khiển trình duyệt hoặc sinh nội dung tại muse.ai."""
    pass


class MuseModelRefusalError(MuseGenerationError):
    """Ngoại lệ khi model muse.ai từ chối yêu cầu sinh ảnh/video và chỉ trả về văn bản từ chối (Policy Refusal)."""


class RefImageSafetyError(MuseGenerationError):
    """Ngoại lệ vi phạm chính sách an toàn ảnh tham chiếu (ví dụ: cố tình truy cập dải IP nội bộ SSRF)."""


class _RefImageHTTPHandler(urllib.request.HTTPHandler, urllib.request.HTTPSHandler):
    def __init__(self, address: str):
        super().__init__()
        self.address = address

    def _connection(self, host, connection_type, **kwargs):
        connection = connection_type(host, **kwargs)

        def create_connection(address, timeout, source_address):
            return socket.create_connection((self.address, address[1]), timeout, source_address)

        # Giữ host gốc cho tiêu đề Host, TLS SNI và kiểm thực chứng chỉ;
        # chỉ ghim địa chỉ socket đích vào địa chỉ IP đã qua kiểm duyệt an toàn.
        connection._create_connection = create_connection
        return connection

    def http_open(self, req):
        return self.do_open(lambda host, **kw: self._connection(
            host, http.client.HTTPConnection, **kw), req)

    def https_open(self, req):
        return self.do_open(lambda host, **kw: self._connection(
            host, http.client.HTTPSConnection, **kw), req)


class _NoRefImageRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _open_public_ref_image(url: str):
    """Mở một URL ảnh công khai HTTP(S) có kiểm tra chống tấn công DNS Rebinding và kiểm soát chuyển hướng.
    
    Phân giải địa chỉ IP của hostname và từ chối các dải IP nội bộ/riêng tư để ngăn chặn tấn công SSRF.
    
    Args:
        url (str): Đường dẫn URL ảnh từ xa cần tải về.
        
    Returns:
        HTTPResponse: Đối tượng phản hồi HTTP đã mở kết nối an toàn.
        
    Raises:
        RefImageSafetyError: Nếu URL trỏ về IP nội bộ hoặc giao thức không hợp lệ.
        urllib.error.URLError: Nếu quá số lần chuyển hướng cho phép (>10 lần) hoặc không phân giải được IP.
    """
    for _ in range(11):
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise RefImageSafetyError("Chuyển hướng ảnh tham chiếu chỉ cho phép URL http(s) hợp lệ")
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        addresses = socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
        checked = []
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
                ip = ip.ipv4_mapped
            if not ip.is_global:
                raise RefImageSafetyError(
                    "Địa chỉ ảnh tham chiếu bị từ chối: chỉ cho phép địa chỉ mạng công cộng; nếu thực sự cần tải từ mạng nội bộ, vui lòng đặt tường minh "
                    "MUSE2API_REF_IMAGE_PRIVATE_FETCH=1")
            checked.append(str(ip))
        if not checked:
            raise urllib.error.URLError("Tên miền ảnh tham chiếu không phân giải được địa chỉ IP")
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), _NoRefImageRedirect(),
            _RefImageHTTPHandler(checked[0]))
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            return opener.open(req, timeout=20)
        except urllib.error.HTTPError as exc:
            location = exc.headers.get("Location")
            if exc.code not in (301, 302, 303, 307, 308) or not location:
                raise
            exc.close()
            url = urllib.parse.urljoin(url, location)
    raise urllib.error.URLError("Ảnh tham chiếu chuyển hướng quá nhiều lần")


class MuseEngine:
    """Động cơ cốt lõi điều khiển trình duyệt vô đầu (Headless Chromium) để tương tác với muse.ai.
    
    Quản lý tiến trình Chromium, các kết nối WebSocket CDP, cô lập session theo luồng,
    và điều khiển tự động toàn bộ luồng sinh ảnh, video và hội thoại.
    """

    def __init__(self, cfg):
        """Khởi tạo thể hiện MuseEngine với cấu hình hệ thống.
        
        Args:
            cfg (Config): Cấu hình hệ thống (chứa cổng CDP, đường dẫn Chromium, thư mục data...).
        """
        self.cfg = cfg
        self.proc: subprocess.Popen | None = None
        self.browser: CDP | None = None
        self._local = threading.local()
        self._start_lock = threading.Lock()
        self._active_contexts: set[str] = set()
        self._contexts_lock = threading.Lock()
        self._last_http_renew: dict[str, float] = {}
        self._log = None
        os.makedirs(cfg.profile_dir, exist_ok=True)

    def _ensure_local(self):
        local = getattr(self, "_local", None)
        if local is None:
            local = threading.local()
            self._local = local
        return local

    @property
    def page(self) -> CDP | None:
        return getattr(self._ensure_local(), "page", None)

    @page.setter
    def page(self, val: CDP | None):
        self._ensure_local().page = val

    @property
    def current_acc_id(self) -> str | None:
        return getattr(self._ensure_local(), "current_acc_id", None)

    @current_acc_id.setter
    def current_acc_id(self, val: str | None):
        self._ensure_local().current_acc_id = val

    @property
    def current_context_id(self) -> str | None:
        return getattr(self._ensure_local(), "current_context_id", None)

    @current_context_id.setter
    def current_context_id(self, val: str | None):
        self._ensure_local().current_context_id = val

    # ---------------- Vòng đời trình duyệt (Browser Lifecycle) ----------------
    def _debug_url(self):
        return f"http://127.0.0.1:{self.cfg.cdp_port}/json/version"

    def start(self):
        """Khởi chạy tiến trình trình duyệt Chromium nền với cờ Remote Debugging Port.
        
        Nếu phát hiện đã có tiến trình CDP đang chạy hợp lệ trên cổng chỉ định, hàm sẽ tự động tái sử dụng.
        
        Raises:
            MuseGenerationError: Nếu không thể kết nối tới cổng gỡ lỗi CDP sau 90 giây thử lại.
        """
        with self._start_lock:
            if self.proc and self.proc.poll() is None and self.browser:
                return
        env = dict(os.environ)
        env.setdefault("HOME", self.cfg.home_dir)
        env["PATH"] = (self.cfg.extra_path + os.pathsep + env.get("PATH", "")) if self.cfg.extra_path else env.get("PATH", "")
        args = [
            self.cfg.chromium,
            "--headless=new", "--no-sandbox", "--disable-gpu",
            "--disable-dev-shm-usage", "--disable-background-networking",
            "--no-first-run", "--no-default-browser-check",
            "--autoplay-policy=no-user-gesture-required",
            "--window-size=1440,2400",
            f"--remote-debugging-port={self.cfg.cdp_port}",
            "--remote-allow-origins=*",
            f"--user-data-dir={self.cfg.profile_dir}",
            "about:blank",
        ]
        # Thử tái sử dụng kết nối CDP lành mạnh hiện có
        if not self.proc:
            try:
                v = http_json(self._debug_url(), timeout=1)
                if v and "webSocketDebuggerUrl" in v:
                    self.browser = CDP(v["webSocketDebuggerUrl"], timeout=180)
                    return
            except Exception:
                pass

        # Dọn dẹp khóa (lock) tàn dư
        for lock_name in ("SingletonLock", "SingletonSocket", "SingletonCookie"):
            lp = os.path.join(self.cfg.profile_dir, lock_name)
            if os.path.exists(lp) or os.path.islink(lp):
                try:
                    os.unlink(lp)
                except Exception:
                    pass

        os.makedirs(self.cfg.data_dir, exist_ok=True)
        self._log = open(os.path.join(self.cfg.data_dir, "chromium.log"), "ab", buffering=0)
        cwd_dir = self.cfg.home_dir if (self.cfg.home_dir and os.path.isdir(self.cfg.home_dir)) else None
        self.proc = subprocess.Popen(args, stdout=self._log, stderr=subprocess.STDOUT,
                                     env=env, cwd=cwd_dir)
        last = None
        for _ in range(90):
            try:
                v = http_json(self._debug_url(), timeout=2)
                self.browser = CDP(v["webSocketDebuggerUrl"], timeout=180)
                return
            except Exception as exc:  # noqa: BLE001
                last = exc
                time.sleep(1)
        raise MuseGenerationError(f"Khởi động Chromium thất bại: {last}")

    def stop(self):
        """Dừng hoàn toàn engine, đóng các Incognito BrowserContext, ngắt kết nối WebSocket và hủy tiến trình Chromium."""
        with self._start_lock:
            self._close_page()
            if self.browser:
                with self._contexts_lock:
                    for ctx_id in list(self._active_contexts):
                        try:
                            self.browser.send("Target.disposeBrowserContext", {"browserContextId": ctx_id})
                        except Exception:
                            pass
                    self._active_contexts.clear()
                try:
                    self.browser.close()
                except Exception:
                    pass
                self.browser = None
            if self.proc and self.proc.poll() is None:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=10)
                except Exception:  # noqa: BLE001
                    self.proc.kill()
            self.proc = None

    # ---------------- Quản lý trang (Page Management) ----------------
    def _close_page(self):
        """Đóng trang riêng của luồng hiện tại và hủy BrowserContext cô lập để giải phóng hoàn toàn bộ nhớ và Session."""
        p = self.page
        ctx_id = self.current_context_id
        if p:
            try:
                p.close()
            except Exception:
                pass
            self.page = None
        if ctx_id and self.browser:
            try:
                self.browser.send("Target.disposeBrowserContext", {"browserContextId": ctx_id})
            except Exception:
                pass
            with self._contexts_lock:
                self._active_contexts.discard(ctx_id)
            self.current_context_id = None
        self.current_acc_id = None

    def _open_page(self):
        """Tạo trang độc lập cho luồng làm việc hiện tại.
        Nếu kết nối trình duyệt chính đang tồn tại, tạo một Incognito BrowserContext độc lập nhằm đảm bảo Cookies và phiên giữa nhiều tài khoản được cô lập 100%."""
        if self.browser:
            try:
                res = self.browser.send("Target.createBrowserContext")
                ctx_id = res.get("result", {}).get("browserContextId")
                if ctx_id:
                    self.current_context_id = ctx_id
                    with self._contexts_lock:
                        self._active_contexts.add(ctx_id)
                    t_res = self.browser.send("Target.createTarget", {
                        "url": "about:blank",
                        "browserContextId": ctx_id
                    })
                    target_id = t_res.get("result", {}).get("targetId")
                    if target_id:
                        ws_url = f"ws://127.0.0.1:{self.cfg.cdp_port}/devtools/page/{target_id}"
                        page = CDP(ws_url, timeout=180)
                        page.send("Network.enable")
                        page.send("Page.enable")
                        page.send("Runtime.enable")
                        page.send("Browser.setDownloadBehavior",
                                  {"behavior": "allow", "downloadPath": self.cfg.download_dir})
                        return page
            except Exception as exc:
                log.warning("Target.createBrowserContext tạo ngữ cảnh cô lập thất bại, quay về dùng tab thông thường: %s", exc)

        import requests
        tgt = requests.put(
            f"http://127.0.0.1:{self.cfg.cdp_port}/json/new?about:blank",
            timeout=10).json()
        page = CDP(tgt["webSocketDebuggerUrl"], timeout=180)
        page.send("Network.enable")
        page.send("Page.enable")
        page.send("Runtime.enable")
        page.send("Browser.setDownloadBehavior",
                  {"behavior": "allow", "downloadPath": self.cfg.download_dir})
        return page

    @staticmethod
    def renew_session_http(cookies: dict, expires: dict | None = None,
                           wake_vm: bool = True) -> dict:
        """Gia hạn phiên làm việc trực tiếp qua giao thức HTTP (không cần tải giao diện trang web).
        
        Gọi API nội bộ của muse.ai:
          - GET `https://muse.ai/api/session` để gia hạn hatch_vml (+48h), hatch_sess (+30d), hatch_gw (+1y).
          - POST `https://muse.ai/api/hatch/vm/wake` để đánh thức máy ảo container nếu vm_state chưa ở trạng thái RUNNING.
          
        Args:
            cookies (dict): Dictionary chứa các cookie hiện tại.
            expires (dict | None, optional): Dictionary chứa hạn dùng các cookie.
            wake_vm (bool, optional): Có kích hoạt đánh thức VM hay không (mặc định: True).
            
        Returns:
            dict: Kết quả trạng thái phiên, ID máy ảo (vm_id), trạng thái máy ảo (vm_state),
                  và dictionary cookies/cookies_exp đã được cập nhật giá trị mới.
                  
        Raises:
            MuseAuthError: Khi máy chủ trả về mã HTTP 401 (phiên đã hết hạn hoặc bị thu hồi).
            MuseGenerationError: Khi gặp lỗi mạng hoặc HTTP status khác 200.
        """
        import requests
        cur_cookies = dict(cookies or {})
        cur_exp = dict(expires or {})
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Origin": "https://muse.ai",
            "Referer": "https://muse.ai/thread/new",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Cookie": "; ".join(f"{k}={v}" for k, v in cur_cookies.items() if v),
        }
        try:
            r = requests.get("https://muse.ai/api/session", headers=headers,
                             timeout=12, allow_redirects=False)
        except requests.RequestException as exc:
            # Không hiển thị lại nội dung request: ngoại lệ có thể chứa URL proxy kèm thông tin xác thực.
            raise MuseGenerationError(
                f"Yêu cầu mạng /api/session thất bại ({type(exc).__name__}); vui lòng kiểm tra mạng/proxy máy chủ rồi thử lại") from None
        if r.status_code == 401:
            raise MuseAuthError("Xác thực phiên thất bại (/api/session HTTP 401), vui lòng kiểm tra đăng nhập trên trang chủ rồi nhập lại cookie")
        if r.status_code != 200:
            hint = ("Truy cập bị từ chối, vui lòng kiểm tra IP đầu ra/khu vực/giới hạn truy cập của máy chủ; không thể dựa vào đây để kết luận Cookie hết hạn"
                    if r.status_code == 403 else "Yêu cầu tới upstream không thành công, vui lòng thử lại sau và kiểm tra mạng máy chủ")
            raise MuseGenerationError(f"/api/session HTTP {r.status_code}: {hint}")
        try:
            sj = r.json()
        except ValueError:
            raise MuseGenerationError("/api/session HTTP 200 trả về dữ liệu không phải JSON; trạng thái phiên chưa được xác nhận") from None
        if not isinstance(sj, dict) or sj.get("status") != "assigned":
            raise MuseGenerationError("/api/session HTTP 200 không trả về phiên assigned; vui lòng kiểm tra trạng thái tài khoản/workspace trên trang chủ")
        for c in r.cookies:
            if c.value:
                cur_cookies[c.name] = c.value
            if c.expires:
                cur_exp[c.name] = int(float(c.expires))
        vm_id = sj.get("vm_id")
        vm_state = sj.get("vm_state")
        wake_ok = False
        wake_requested = False
        if wake_vm and vm_id and vm_state != "DISABLED":
            try:
                headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in cur_cookies.items() if v)
                rw = requests.post("https://muse.ai/api/hatch/vm/wake", headers=headers, json={
                    "vm_id": vm_id,
                    "retry_count": 0,
                    "connect_attempt_id": str(uuid.uuid4()),
                }, timeout=8)
                wake_requested = rw.status_code == 200
                if wake_requested:
                    # HTTP 200 chỉ xác nhận đã nhận yêu cầu; chỉ trạng thái session mới khẳng định chắc chắn VM đã thức giấc.
                    verify = requests.get("https://muse.ai/api/session", headers=headers,
                                          timeout=12, allow_redirects=False)
                    if verify.status_code == 200:
                        verified_session = verify.json()
                        if isinstance(verified_session, dict) and verified_session.get("status") == "assigned":
                            vm_state = verified_session.get("vm_state") or vm_state
                            wake_ok = vm_state == "RUNNING"
            except Exception:
                pass
        return {
            "ok": sj.get("status") == "assigned",
            "status": sj.get("status"),
            "vm_id": vm_id,
            "vm_state": vm_state,
            "wake_ok": wake_ok,
            "wake_requested": wake_requested,
            "cookies": cur_cookies,
            "cookies_exp": cur_exp,
        }

    def _apply_cookies(self, page: CDP, cookies: dict, expires: dict | None = None):
        """Tiêm cookie. Xóa sạch hoàn toàn cookie tài khoản cũ để đảm bảo cô lập, và tuyệt đối không truyền expires trong quá khứ nhằm ngăn Chromium loại bỏ hatch_vml."""
        try:
            page.send("Network.clearBrowserCookies")
        except Exception:
            pass
        now = time.time()
        for name, value in cookies.items():
            if not value:
                continue
            exp = (expires or {}).get(name)
            try:
                exp_val = float(exp) if exp and float(exp) > now + 3600 else (now + 7 * 86400)
            except (TypeError, ValueError):
                exp_val = now + 7 * 86400
            for dom in (".muse.ai", "muse.ai"):
                params = {
                    "name": name,
                    "value": value,
                    "domain": dom,
                    "path": "/",
                    "secure": True,
                    "expires": exp_val,
                }
                try:
                    page.send("Network.setCookie", params)
                except Exception:  # noqa: BLE001
                    pass

    def read_cookies(self) -> dict[str, dict]:
        """Đọc lại cookie từ trang hiện tại (**bao gồm cả cờ httpOnly**, điều mà JavaScript thông thường trên web không thể làm được).

        Trả về {name: {"value": ..., "expires": unix timestamp hoặc -1}}.
        Mục đích: muse.ai tự động gia hạn một phần cookie khi truy cập; việc đọc lại sau khi sinh nội dung và cập nhật vào hồ chứa giúp tài khoản khó bị hết hạn hơn.
        """
        if not self.page:
            return {}
        try:
            msg = self.page.send("Network.getCookies",
                                 {"urls": [self.cfg.site_url]}, timeout=20)
        except Exception:  # noqa: BLE001
            return {}
        out: dict[str, dict] = {}
        for c in (msg.get("result", {}).get("cookies") or []):
            name = c.get("name")
            if not name:
                continue
            try:
                exp = int(float(c.get("expires", -1)))
            except (TypeError, ValueError):
                exp = -1
            out[name] = {"value": c.get("value", ""), "expires": exp}
        return out

    def _wait_ws_ready(self, page: CDP, timeout: float = 15.0) -> bool:
        """Chờ trang muse.ai hoàn tất quá trình React hydration và không còn ở trạng thái Connecting..."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                st = page.js("""(function(){
                    if (document.readyState !== 'complete') return 'loading';
                    if (!document.querySelector('textarea')) return 'no-ta';
                    var h = document.querySelector('[data-hatch-shell-hydration-state]');
                    if (h && h.getAttribute('data-hatch-shell-hydration-state') !== 'hydrated') return 'hydrating';
                    var b = document.body ? (document.body.innerText || '') : '';
                    if (b.indexOf('Connecting...') !== -1) return 'connecting';
                    // Khung nhập liệu rỗng có thể không render nút Send cho đến khi văn bản được nhập vào.
                    if (document.querySelector('textarea').disabled) return 'input-disabled';
                    return 'ready';
                })()""")
                if st == "ready":
                    return True
            except Exception:
                pass
            time.sleep(0.1)
        return False

    def reset_thread(self, for_chat: bool = False):
        """Đóng các popup tàn dư và đảm bảo phiên hội thoại sạch sẽ với WebSocket đã sẵn sàng.
        Đối với hội thoại văn bản thuần túy (for_chat=True), nếu trang ấm hiện tại không có tệp đính kèm, không bị treo và số lượng bong bóng tin nhắn còn ít, hệ thống sẽ tái sử dụng trực tiếp kết nối ấm để phản hồi nhanh chóng trong ~2 giây."""
        if not self.page:
            return
        try:
            needs_nav = self.page.js("""(function(forChat){
                var d = document.querySelector('[role="dialog"]');
                if (d) {
                    var b = d.querySelector('button[aria-label*="close" i], button');
                    if (b) b.click();
                }
                var scope = document.querySelector('main,[class*="chat-scroll"],[class*="hatch-chat-scroll"]') || document.body;
                var bubbleCount = scope ? scope.querySelectorAll('div[class*="hatch-chat-groupable-bubble"]').length : 0;
                var hasAtts = document.querySelectorAll('[data-testid^="hatch-chat-attachment-presentation-"]').length > 0;
                var hasStop = !!(document.querySelector('[data-testid="hatch-composer-stop-button"]')
                    || document.querySelector('button[aria-label*="Stop" i]')
                    || document.querySelector('button[aria-label*="停止"]'));
                var bodyTxt = document.body ? (document.body.innerText || '') : '';
                var hasStuck = bodyTxt.indexOf('Still sending') !== -1 || bodyTxt.indexOf('Connecting...') !== -1;
                if (hasStop || hasStuck || hasAtts) return true;
                if (forChat) {
                    return bubbleCount >= 24;
                }
                return (window.location.pathname !== '/thread/new') || bubbleCount > 0;
            })(%s)""" % ("true" if for_chat else "false"))
            if needs_nav:
                self.page.send("Page.navigate", {"url": "https://muse.ai/thread/new"})
                t_end = time.time() + 10.0
                while time.time() < t_end:
                    time.sleep(0.08)
                    ready = self.page.js("""(function(){
                        return document.readyState === 'complete'
                            && !!document.querySelector('textarea')
                            && document.querySelectorAll('div[class*="hatch-chat-groupable-bubble"]').length === 0;
                    })()""")
                    if ready:
                        break
                self._wait_ws_ready(self.page, timeout=12.0)
        except Exception:
            pass

    def ensure_page(self, cookies: dict, expires: dict | None = None, account_id: str | None = None):
        """Đảm bảo tab làm việc của luồng hiện tại đã được khởi tạo, nạp đúng Cookies và WebSocket sẵn sàng.
        
        Nếu tài khoản trùng khớp và tab đang khỏe (textarea tồn tại và đã hydrated), tab sẽ được tái sử dụng ngay.
        Nếu cần đổi tài khoản hoặc mở tab mới:
          - Tự động gọi renew_session_http để gia hạn trước nếu quá 10 phút.
          - Mở Incognito BrowserContext độc lập, áp dụng cookie và điều hướng tới `/thread/new`.
          - Chờ cho tới khi khung soạn thảo React hoàn thành kết nối WebSocket (`_wait_ws_ready`).
          
        Args:
            cookies (dict): Danh sách cookies của tài khoản.
            expires (dict | None, optional): Hạn dùng của các cookie.
            account_id (str | None, optional): ID tài khoản cần gán cho ngữ cảnh này.
            
        Returns:
            CDP: Đối tượng client CDP kết nối tới tab đã sẵn sàng.
            
        Raises:
            MuseAuthError: Nếu trang web chuyển hướng về màn hình đăng nhập (bị logout).
            MuseGenerationError: Nếu tải trang hoặc kết nối WebSocket quá hạn timeout.
        """
        if self.page is not None and (account_id is None or getattr(self, "current_acc_id", None) == account_id):
            try:
                if self.page.js("!!document.querySelector('textarea')") and self._wait_ws_ready(self.page, timeout=8.0):
                    return self.page
            except Exception:
                pass
        self._close_page()
        # Chỉ gọi /api/session trên luồng chính khi lần gia hạn HTTP trước cách hơn 10 phút, tránh lặp lại gây nghẽn mỗi lần chuyển tài khoản
        last_map = getattr(self, "_last_http_renew", None)
        if last_map is None:
            last_map = {}
            self._last_http_renew = last_map
        now_ts = time.time()
        if not account_id or (now_ts - last_map.get(account_id, 0) > 600):
            try:
                renewed = self.renew_session_http(cookies, expires, wake_vm=True)
                if renewed.get("cookies"):
                    cookies = renewed["cookies"]
                if renewed.get("cookies_exp"):
                    expires = renewed["cookies_exp"]
                if account_id:
                    last_map[account_id] = now_ts
            except MuseAuthError:
                raise
            except Exception as e:
                log.warning("Gia hạn sớm /api/session thất bại (tiếp tục thử tải bằng trình duyệt): %s", e)

        page = self._open_page()
        self._apply_cookies(page, cookies, expires)
        page.send("Page.navigate", {"url": "https://muse.ai/thread/new"})
        self.page = page  # Cleanup must also own pages that never become ready.
        if self._wait_ws_ready(page, timeout=self.cfg.login_wait):
            self.current_acc_id = account_id
            return page
        try:
            body = (page.js("document.body ? document.body.innerText.slice(0,1200) : ''") or "").lower()
        except Exception:
            body = ""
        self._close_page()
        if "connecting..." in body:
            raise MuseGenerationError("Quá thời gian kết nối cổng trang web (Connecting...), đang tự động chuyển tài khoản")
        # Phân biệt giữa phiên làm việc đã hết hạn và trang web không bao giờ sẵn sàng.
        if re.search(r"log in|sign in|create an account|登录|đăng nhập|use another account", body):
            raise MuseAuthError("Phiên đã bị muse.ai đăng xuất (có thể bị đăng nhập nơi khác đẩy ra hoặc kích hoạt kiểm soát rủi ro), "
                                "vui lòng dùng tiện ích trình duyệt nhập lại cookie")
        raise MuseGenerationError("Tải trang muse.ai quá thời gian chờ (chưa xuất hiện ô nhập trò chuyện), vui lòng kiểm tra mạng máy chủ rồi thử lại; chưa xác nhận phiên hết hạn")

    def close_current_page(self):
        """Giải phóng tường minh trang và ngữ cảnh cô lập do luồng hiện tại nắm giữ."""
        self._close_page()

    def refresh(self, cookies: dict, expires: dict | None = None):
        self._close_page()
        return self.ensure_page(cookies, expires)

    # ---------------- Truy vấn hạn mức Quota (Bảng Settings) ----------------
    # Hạn mức của muse.ai nằm trong menu Settings ở dưới cùng → mục Settings → bảng cài đặt
    # mục General → Usage, có dạng như:
    #   Free plan
    #   Weekly limit resets on Sep 30
    #   1% used
    #   Additional tokens / Never expires / 0% used (2B tokens left)
    def _click_point(self, x: int, y: int):
        for t in ("mousePressed", "mouseReleased"):
            self.page.send("Input.dispatchMouseEvent",
                           {"type": t, "x": x, "y": y,
                            "button": "left", "clickCount": 1})

    _CLICK_JS = (
        "(function(){var sel=%s;"
        "var b=[...document.querySelectorAll(sel)]"
        ".filter(function(x){return x.offsetParent!==null;})[0];"
        "if(!b)return null;var r=b.getBoundingClientRect();"
        "return JSON.stringify({x:Math.round(r.x+r.width/2),"
        "y:Math.round(r.y+r.height/2)});})()")

    _QUOTA_SETTINGS_JS = r"""(() => {
        const visible = e => e.getClientRects().length > 0
            && getComputedStyle(e).visibility !== 'hidden';
        const labels = ['Settings', '設定', '设置'];
        const b = [...document.querySelectorAll('[data-testid="hatch-dock-more"]')].find(visible)
            || [...document.querySelectorAll('button,[role=button]')].find(e =>
                visible(e) && labels.includes((e.getAttribute('aria-label') || '').trim()));
        if (!b) return null;
        const r = b.getBoundingClientRect();
        return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});
    })()"""

    _QUOTA_MENU_JS = r"""(() => {
        const visible = e => e.getClientRects().length > 0
            && getComputedStyle(e).visibility !== 'hidden';
        const labels = ['Settings', '設定', '设置'];
        const exact = e => labels.includes((e.textContent || '').trim());
        // Các mục menu có chứa hậu tố phím tắt (ví dụ: Settings, 設定, 设置, v.v.).
        const b = [...document.querySelectorAll('[role=menuitem]')].find(e =>
            visible(e) && (exact(e) || [...e.querySelectorAll('span,div')].some(exact)))
            || [...document.querySelectorAll('[role=menu] button,[role=menu] span,[role=menu] div')]
                .find(e => visible(e) && exact(e));
        if (!b) return null;
        const r = b.getBoundingClientRect();
        return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});
    })()"""

    _QUOTA_DIALOG_JS = r"""(() => {
        const d = [...document.querySelectorAll('[role=dialog],[aria-modal=true]')]
            .find(e => e.getClientRects().length > 0 && getComputedStyle(e).visibility !== 'hidden');
        return d ? (d.innerText || '') : '';
    })()"""

    def _quota_click(self, expr: str, error: str, timeout: float = 8.0):
        deadline = time.monotonic() + timeout
        while True:
            raw = self.page.js(expr)
            if raw:
                pt = json.loads(raw)
                self._click_point(pt['x'], pt['y'])
                return
            if time.monotonic() >= deadline:
                raise MuseGenerationError(error)
            time.sleep(0.15)

    def _dismiss_quota_ui(self):
        # Một lần tra cứu thất bại có thể để lại menu đang mở; dọn dẹp các menu và hộp thoại.
        for _ in range(2):
            for typ in ('keyDown', 'keyUp'):
                self.page.send('Input.dispatchKeyEvent',
                               {'type': typ, 'key': 'Escape', 'code': 'Escape',
                                'windowsVirtualKeyCode': 27, 'nativeVirtualKeyCode': 27})
            time.sleep(0.1)  # Chờ giao diện hoàn tất việc đóng lại trước tương tác tiếp theo.

    def quota(self, cookies: dict, expires: dict | None = None,
              account_id: str | None = None) -> dict:
        """Tra cứu hạn mức và dung lượng sử dụng (Quota) của tài khoản trong một ngữ cảnh trình duyệt dùng 1 lần (disposable).
        
        Mở menu Settings -> Chọn mục Settings -> Đọc nội dung hộp thoại hiển thị dung lượng tuần (Usage) và gói cước.
        
        Args:
            cookies (dict): Cookies của tài khoản cần kiểm tra.
            expires (dict | None, optional): Hạn dùng của cookies.
            account_id (str | None, optional): ID của tài khoản.
            
        Returns:
            dict: Thông tin gói cước (plan), tỉ lệ phần trăm đã dùng (% used), ngày reset tuần, token còn lại...
            
        Raises:
            MuseGenerationError: Nếu không tìm thấy nút Settings hoặc không đọc được bảng Usage sau timeout.
        """
        # Menu Settings của Muse có thể rơi vào trạng thái React đóng dở sau khi đọc.
        # Ngữ cảnh dùng một lần chậm hơn nhưng ngăn các lần đọc liên tiếp
        # kế thừa giao diện cũ và giữ cookie tài khoản được cô lập nghiêm ngặt.
        self._close_page()
        try:
            self.ensure_page(cookies, expires, account_id=account_id)
            self._quota_click(self._QUOTA_SETTINGS_JS, 'Không tìm thấy nút Cài đặt (Settings / 設定 / 设置)')
            self._quota_click(self._QUOTA_MENU_JS, 'Menu cài đặt không xuất hiện mục cài đặt nhận diện được')
            deadline = time.monotonic() + 12.0
            while True:
                parsed = self._parse_quota(self.page.js(self._QUOTA_DIALOG_JS) or '')
                if parsed['found']:
                    return parsed
                if time.monotonic() >= deadline:
                    raise MuseGenerationError('Bảng hạn mức không đọc được dữ liệu sử dụng hợp lệ; giữ nguyên bộ nhớ đệm cũ')
                time.sleep(0.2)
        finally:
            self._close_page()

    @staticmethod
    def _parse_quota(txt: str) -> dict:
        """Phân tích văn bản dung lượng sử dụng hỗ trợ tiếng Anh, tiếng Trung phồn thể và giản thể."""
        normalized = unicodedata.normalize('NFKC', txt or '')
        lines = [ln.strip() for ln in normalized.splitlines() if ln.strip()]
        # Tránh các đoạn văn bản tài khoản/hồ sơ không liên quan nằm trước phần Usage.
        start = next((i + 1 for i, ln in enumerate(lines)
                      if ln.lower() in ('usage', '用量', '使用量')), 0)
        lines = lines[start:]
        end = next((i for i, ln in enumerate(lines)
                    if ln.lower() in ('language', '语言', '語言')), len(lines))
        lines = lines[:end]
        out: dict = {'raw': '\n'.join(lines[:40])}
        for ln in lines:
            if re.fullmatch(r'.{1,60}?(?:\s+plan|計劃|计划|方案)', ln, re.I):
                out['plan'] = ln
                break
        text = '\n'.join(lines)
        reset = re.search(r'Weekly limit resets? on ([^\n]+)', text, re.I)
        if not reset:
            reset = re.search(
                r'(?:每(?:週|周|星期)|週|周)(?:上限|限額|限额|額度|额度)'
                r'(?:會|会|將|将)?(?:於|于|在)\s*([^\n]+?)\s*(?:重設|重置)', text)
        if reset:
            out['weekly_reset'] = reset.group(1).strip()

        extra_at = next((i for i, ln in enumerate(lines) if re.match(
            r'^(?:(?:Additional|Extra)\s+tokens|(?:額外|额外)(?:的)?(?:符元|符記|代幣|代币|令牌|憑證|凭证|tokens))',
            ln, re.I)), len(lines))

        def percentage(line):
            m = re.search(r'(\d+(?:\.\d+)?)\s*%\s*(?:used\b|已(?:使)?用)', line, re.I)
            if not m:
                m = re.search(r'已(?:使)?用\s*(\d+(?:\.\d+)?)\s*%', line)
            if not m:
                return None
            value = float(m.group(1))
            if not 0 <= value <= 100:
                return None
            return int(value) if value.is_integer() else value

        for ln in lines[:extra_at]:
            value = percentage(ln)
            if value is not None:
                out['weekly_used_pct'] = value
                break
        for ln in lines[extra_at:]:
            value = percentage(ln)
            if value is not None:
                out['extra_used_pct'] = value
                left = re.search(r'\(([^)]+)\)', ln)
                if left:
                    out['extra_left'] = left.group(1).strip()
                break
        if re.search(r'Never expires|永不過期|永不过期', text, re.I):
            out['extra_expires'] = 'never'
        # Chỉ riêng nhãn gói cước không đại diện cho việc đọc quota thành công. Giữ nguyên cache cũ.
        out['found'] = 'weekly_used_pct' in out
        return out

    # ---------------- Tệp đính kèm (Kết quả sinh nội dung) ----------------
    _ATT_JS = (
        "(function(){"
        "var list = []; var seen = new Set();"
        "function addEl(el, tid){"
        "  if(!el || seen.has(el)) return;"
        "  seen.add(el);"
        "  if(el.closest('form, [class*=chat-user-bubble], [class*=\"group/msg\"]')) return;"
        "  var v = el.querySelector('video') || (el.tagName === 'VIDEO' ? el : null);"
        "  var img = el.querySelector('img') || (el.tagName === 'IMG' ? el : null);"
        "  var isVid = (tid || '').includes('video') || !!v;"
        "  var primary = isVid ? (v || img) : (img || v);"
        "  var src = primary ? (primary.currentSrc || primary.src || '') : '';"
        "  if(src && !seen.has(src)){"
        "    seen.add(src);"
        "    list.push({"
        "      tid: tid || el.getAttribute('data-testid') || (isVid ? 'video' : 'image'),"
        "      hasVideo: !!v,"
        "      hasImg: !!img,"
        "      src: src,"
        "      vSrc: v ? (v.currentSrc || v.src || '') : '',"
        "      iSrc: img ? (img.currentSrc || img.src || '') : '',"
        "      w: primary ? (primary.videoWidth || primary.naturalWidth || 0) : 0,"
        "      h: primary ? (primary.videoHeight || primary.naturalHeight || 0) : 0"
        "    });"
        "  }"
        "}"
        "document.querySelectorAll('[data-testid^=\"hatch-chat-attachment-presentation-\"]').forEach(function(a){ addEl(a, a.getAttribute('data-testid')); });"
        "document.querySelectorAll('div[class*=\"hatch-agent-bubble-bg\"] img, div[class*=\"hatch-agent-bubble-bg\"] video').forEach(function(m){"
        "  var s = m.currentSrc || m.src || '';"
        "  if(s && !s.includes('avatar') && !s.includes('emoji')) addEl(m.parentElement || m, 'agent-media');"
        "});"
        "return JSON.stringify(list);"
        "})()"
    )

    def attachments(self) -> list[dict]:
        try:
            raw = self.page.js(self._ATT_JS)
            return json.loads(raw) if raw else []
        except Exception:  # noqa: BLE001
            return []

    # ---------------- Gửi tin nhắn (Send Message) ----------------
    # Kiểm tra "văn bản đã thực sự vào ô nhập liệu + nút Send đã thực sự được render".
    # Cả hai điều kiện đều bắt buộc: nút Send chỉ được render khi React state có chứa văn bản —
    # nút xuất hiện chứng tỏ React đã thực sự nhận được dữ liệu nhập (chứ không đơn thuần là thay đổi DOM value).
    _SEND_STATE_JS = (
        "(function(){var ta=document.querySelector('textarea');"
        "var b=[...document.querySelectorAll('button,[role=button]')]"
        ".find(function(x){return /send/i.test(x.getAttribute('aria-label')||'');});"
        "return JSON.stringify({v:ta?ta.value:'',btn:b?(b.disabled?2:1):0});})()"
    )

    def _send(self, prompt: str) -> str:
        """Điền câu lệnh / câu nhắc (prompt) vào textarea và kích hoạt hành động gửi tin nhắn.
        
        Cơ chế:
          1. Cuộn textarea vào trung tâm màn hình và phát sự kiện click chuột trái để nhận tiêu điểm (focus).
          2. Sử dụng setter nguyên mẫu `HTMLTextAreaElement.prototype.value` để cập nhật trạng thái trong React 18,
             kèm phát sự kiện 'input' và 'change' (tốc độ <1s ngay cả với văn bản siêu dài >100KB).
          3. Tìm và click nút Send khi chuyển sang trạng thái kích hoạt (enabled). Nếu nút không xuất hiện,
             dùng cơ chế fallback phát phím tắt Ctrl+Enter và Enter.
             
        Args:
            prompt (str): Nội dung câu nhắc người dùng muốn gửi.
            
        Returns:
            str: Trạng thái kích hoạt thành công ('clicked' hoặc 'enter-sent').
            
        Raises:
            MuseGenerationError: Nếu không tìm thấy phần tử textarea trên trang.
        """
        # 1. Cuộn textarea vào giữa viewport và kích hoạt focus thực tế
        try:
            self.page.js("""(function(){
                var ta = document.querySelector('textarea');
                if (ta) {
                    ta.scrollIntoView({block: 'center', inline: 'nearest'});
                    ta.focus();
                }
            })()""")
        except Exception:
            pass
        time.sleep(0.1)

        rect = self.page.js(
            "(function(){var t=document.querySelector('textarea');if(!t)return null;"
            "var r=t.getBoundingClientRect();"
            "return JSON.stringify({x:Math.round(r.left+r.width/2),"
            "y:Math.round(r.top+r.height/2)});})()")
        if not rect:
            raise MuseGenerationError("Không tìm thấy ô nhập trò chuyện")
        c = json.loads(rect)
        for t in ("mousePressed", "mouseReleased"):
            self.page.send("Input.dispatchMouseEvent",
                           {"type": t, "x": c["x"], "y": c["y"],
                            "button": "left", "clickCount": 1})
        time.sleep(0.1)

        # Kích hoạt setter nguyên mẫu của React 18 cùng các sự kiện input/change để đồng bộ trạng thái nút gửi
        # (Đối với ngữ cảnh siêu dài 100KB+ như DeepSeek/Codex, việc đi qua setter nguyên mẫu chỉ mất <1s, tránh bị treo do chèn từng ký tự bằng Input.insertText)
        _SETTER_JS = (
            "(function(t){var ta=document.querySelector('textarea');"
            "if(!ta) return 0;"
            "ta.focus();"
            "var s=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;"
            "s.call(ta,t);"
            "ta.dispatchEvent(new Event('input',{bubbles:true}));"
            "ta.dispatchEvent(new Event('change',{bubbles:true}));"
            "return (ta.value||'').length;})(%s)")
        val_len = self.page.js(_SETTER_JS % json.dumps(prompt)) or 0
        if not val_len and len(prompt) < 500:
            self.page.send("Input.insertText", {"text": prompt})
            self.page.js(_SETTER_JS % json.dumps(prompt))

        # Chờ nút gửi sẵn sàng và nhấp chuột
        clicked = "no-button"
        t_deadline = time.time() + 3.0
        while time.time() < t_deadline:
            res = self.page.js(
                "(function(){var b=[...document.querySelectorAll('button,[role=button]')]"
                ".filter(function(x){return x.offsetParent!==null;})"
                ".find(function(x){return /发送|send/i.test(x.getAttribute('aria-label')||'')"
                "||/发送|send/i.test(x.getAttribute('data-testid')||'')"
                "||/send/i.test(x.innerText||'');});"
                "if(!b)return 'no-button';"
                "if(b.disabled)return 'disabled';"
                "b.click();return 'clicked';})()")
            if res == "clicked":
                clicked = "clicked"
                break
            time.sleep(0.08)

        if clicked != "clicked":
            # Phương án dự phòng: Ctrl+Enter hoặc phím Enter thông thường
            for combo in ({"modifiers": 1}, {}):
                for t in ("keyDown", "char", "keyUp"):
                    params = {"type": t, "key": "Enter", "code": "Enter",
                              "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13,
                              "modifiers": combo.get("modifiers", 0)}
                    if t == "char":
                        params["text"] = "\r"
                        params["unmodifiedText"] = "\r"
                    self.page.send("Input.dispatchKeyEvent", params)
                time.sleep(1.0)
                try:
                    if self.page.js("!(document.querySelector('textarea')||{value:''}).value"):
                        clicked = "enter-sent"
                        break
                except Exception:
                    pass
        time.sleep(0.3)
        return clicked

    # ---------------- Chờ sinh nội dung (Wait for Generation) ----------------
    def _last_attachment(self) -> dict | None:
        atts = self.attachments()
        return atts[-1] if atts else None

    def _scroll_bottom(self):
        """Cuộn xuống đáy cuộc trò chuyện. Khung cuộn trò chuyện của muse.ai là div bên trong (không phải document),
        danh sách ảo (virtual list) render node theo vị trí cuộn — nếu không cuộn xuống đáy, tin nhắn mới sẽ hoàn toàn không có trong DOM."""
        try:
            self.page.js(
                "(function(){"
                "var els=[...document.querySelectorAll('*')].filter(function(e){"
                "var s=getComputedStyle(e);"
                "return (s.overflowY==='auto'||s.overflowY==='scroll')"
                "&&e.scrollHeight>e.clientHeight+100;});"
                "els.sort(function(a,b){return b.scrollHeight-a.scrollHeight;});"
                "if(els[0])els[0].scrollTop=els[0].scrollHeight;"
                "var s=document.scrollingElement||document.body;"
                "s.scrollTop=s.scrollHeight;"
                "var el=document.querySelector('textarea');"
                "if(el)el.scrollIntoView({block:'end'});return 1;})()")
        except Exception:  # noqa: BLE001
            pass

    def _wait_attachment(self, baseline_src: str, timeout: int, expect: str,
                         on_progress=None, base_agent_cnt: int = 0,
                         base_att_cnt: int = 0, stop_event=None, baseline_sources=None) -> dict | None:
        """Vòng lặp lắng nghe tệp đính kèm kết quả mới (ảnh hoặc video) được sinh ra trong hội thoại.
        
        Theo dõi sự thay đổi của DOM, tự động cuộn trang xuống đáy để cập nhật danh sách ảo,
        kiểm tra thuộc tính hình ảnh (w, h > 0) hoặc định dạng video (vSrc, thẻ video),
        đồng thời phát hiện nhanh các tình huống model từ chối tạo nội dung (Model Refusal) để ngắt sớm.
        
        Args:
            baseline_src (str): URL nguồn của attachment cuối cùng trước khi gửi prompt (để so sánh).
            timeout (int): Thời gian chờ tối đa (giây).
            expect (str): Loại định dạng mong muốn ('image' hoặc 'video').
            on_progress (callable | None, optional): Callback thông báo phần trăm tiến độ sinh.
            base_agent_cnt (int, optional): Số lượng bong bóng tin nhắn của bot trước khi gửi.
            base_att_cnt (int, optional): Số lượng attachment trước khi gửi.
            stop_event (threading.Event | None, optional): Cờ dừng sớm nếu client ngắt kết nối.
            baseline_sources (set | None, optional): Tập hợp URL các attachment cũ cần loại trừ.
            
        Returns:
            dict | None: Dictionary thông tin attachment mới được chọn hoặc None nếu quá hạn.
            
        Raises:
            MuseGenerationError: Khi client ngắt kết nối hoặc lỗi sinh nghiêm trọng.
            MuseModelRefusalError: Khi model muse.ai hoàn thành lượt trò chuyện bằng văn bản từ chối.
        """
        baseline_sources = set(baseline_sources or ()) | {baseline_src}
        deadline = time.time() + timeout
        t_start = time.time()
        stable_src, stable_n = "", 0
        last_txt, txt_stable = "", 0
        refusal_last, refusal_stable = "", 0
        seen_stop = False
        previous_state = None
        last_activity = t_start
        progress_sent = 0
        while time.time() < deadline:
            if stop_event is not None and stop_event.is_set():
                raise MuseGenerationError("Client đã ngắt kết nối, hủy tác vụ tạo nội dung")
            time.sleep(0.6)
            self._scroll_bottom()
            atts = self.attachments()
            # Chọn tệp đính kèm nghiêm ngặt theo đúng loại kỳ vọng, tuyệt đối không chấp nhận dự phòng sai modal (như hạ cấp yêu cầu video thành ảnh bìa)
            matching_atts = []
            for a in atts:
                tid = (a.get("tid") or "").lower()
                has_video = bool(a.get("hasVideo"))
                src = a.get("src") or ""
                v_src = a.get("vSrc") or ""
                if expect == "video":
                    # tid chứa "video" là chưa đủ để xác nhận: muse sẽ đánh dấu data-testid thành
                    # ...-presentation-video từ sớm, khi đó thẻ <video> có thể chưa được gắn vào, _ATT_JS với
                    # primary = v || img sẽ quay về lấy img bìa, khiến src/w/h toàn là ảnh tĩnh.
                    # Chỉ công nhận nguồn video thực sự (vSrc / hasVideo / phần mở rộng video).
                    is_match = (
                        has_video
                        or bool(v_src)
                        or src.endswith((".mp4", ".webm", ".mov"))
                    )
                else:
                    is_match = ("image" in tid) or (not has_video and not src.endswith((".mp4", ".webm", ".mov")))
                if is_match:
                    matching_atts.append(a)

            att = matching_atts[-1] if matching_atts else None
            if att:
                src = att.get("src") or ""
                v_src = att.get("vSrc") or ""
                w = att.get("w", 0) or 0
                h = att.get("h", 0) or 0
                # Nhiệm vụ video nghiêm cấm lấy src ảnh bìa giả mạo sản phẩm hoàn thiện; khi không có vSrc chỉ chấp nhận src có đuôi video rõ ràng
                if expect == "video":
                    check_src = v_src if v_src else (
                        src if src.endswith((".mp4", ".webm", ".mov")) else ""
                    )
                else:
                    check_src = src
                if check_src and check_src not in baseline_sources:
                    if w > 0 and h > 0:
                        return att
                    if check_src == stable_src:
                        stable_n += 1
                    else:
                        stable_src, stable_n = check_src, 0
                    if stable_n >= 1:
                        return att
            elapsed = time.time() - t_start
            cur_cnt = base_agent_cnt
            cur_txt = ""
            has_stop = False
            tail = ""
            try:
                st_raw = self.page.js("""(function(){
                    var bs=[].slice.call(document.querySelectorAll('div[class*="hatch-chat-groupable-bubble"]'))
                        .filter(function(b){return /hatch-agent-bubble-bg/.test(b.className||'');});
                    var lastTxt = bs.length ? (bs[bs.length-1].innerText||'').trim() : '';
                    var hasStop = !!(document.querySelector('[data-testid="hatch-composer-stop-button"]')
                        || document.querySelector('button[aria-label*="Stop" i]')
                        || document.querySelector('button[aria-label*="停止"]'));
                    var tail = document.body ? (document.body.innerText||'').slice(-1200) : '';
                    return JSON.stringify({cnt: bs.length, txt: lastTxt, stop: hasStop, tail: tail,
                        path: location.pathname || '', href: location.href || ''});
                })()""")
                st = json.loads(st_raw) if st_raw else {}
            except Exception:
                st = {}
            tail = st.get("tail") or ""
            cur_cnt = int(st.get("cnt") or 0)
            cur_txt = st.get("txt") or ""
            has_stop = bool(st.get("stop"))
            path = st.get("path") or ""
            seen_stop = seen_stop or has_stop
            state = (cur_cnt, cur_txt, len(atts), has_stop, path)
            if previous_state is None or state != previous_state:
                last_activity = time.time()
                previous_state = state

            if on_progress:
                milestone = 25 if seen_stop else 20
                if cur_cnt > base_agent_cnt:
                    milestone = 40
                if milestone > progress_sent:
                    try:
                        on_progress(milestone)
                        progress_sent = milestone
                    except Exception:
                        pass

            if re.search(r"额度不足|积分不足|out of credits|达到上限|token limit", tail, re.I):
                raise MuseGenerationError("Tài khoản đã hết hạn mức")
            # Nút Stop cũng có thể hiển thị cho các tin nhắn chưa từng được gateway xác nhận.
            if elapsed > 30.0 and cur_cnt == base_agent_cnt and re.search(
                    r"Still sending|Delivery not confirmed|正在发送|未确认送达", tail, re.I):
                raise MuseGenerationError(
                    "Prompt chưa được gửi tới backend thành công (Still sending / Delivery not confirmed), dừng chờ và thử lại")

            refusal_source = cur_txt if cur_cnt > base_agent_cnt else (
                tail if seen_stop and not has_stop and elapsed > 20.0 else "")
            refusal = self._media_refusal_text(refusal_source, expect)
            if refusal and not has_stop and len(atts) <= base_att_cnt:
                if refusal == refusal_last:
                    refusal_stable += 1
                else:
                    refusal_last, refusal_stable = refusal, 0
                if refusal_stable >= 4 and elapsed > 8.0:
                    raise MuseModelRefusalError(f"Mô hình không tạo media, chỉ trả về văn bản: {refusal}")
            else:
                refusal_last, refusal_stable = "", 0

            if cur_cnt > base_agent_cnt and cur_txt and not has_stop and len(atts) <= base_att_cnt:
                # Văn bản báo trạng thái media có thể xuất hiện trước tệp đính kèm thực tế; không coi đây là lỗi.
                is_media_report = bool(re.search(
                    r"\.(?:webp|png|jpe?g|mp4|webm)|imagine_media|deliverable|"
                    r"generated\s+.*image|verified\s+generated|artifact", cur_txt, re.I))
                if not is_media_report:
                    if cur_txt == last_txt:
                        txt_stable += 1
                    else:
                        last_txt, txt_stable = cur_txt, 0
                    if txt_stable >= 15 and elapsed > 8.0:
                        clean = self._clean_model_text(cur_txt)
                        raise MuseModelRefusalError(
                            f"Mô hình không tạo media, chỉ trả về văn bản: {clean}")
                else:
                    txt_stable = 0
            else:
                txt_stable = 0

            # Muse đã nhận cú nhấp chuột nhưng không tạo thread. Việc yêu cầu hoàn tất
            # vòng đời nút Stop, trang nhàn rỗi, không có tin nhắn/tệp đính kèm và đang ở /thread/new
            # giúp tránh nhầm lẫn quá trình render video dài thông thường là lỗi thất bại.
            if (expect == "video" and seen_stop and not has_stop
                    and path.rstrip("/").endswith("/thread/new")
                    and cur_cnt <= base_agent_cnt and len(atts) <= base_att_cnt
                    and elapsed >= 180.0 and time.time() - last_activity >= 90.0):
                raise MuseGenerationError(
                    "Muse chưa tạo luồng tác vụ video, trang web không phản hồi liên tục sau khi gửi (đã dừng chờ sớm)")
        return None

    @staticmethod
    def _clean_model_text(text: str, limit: int = 240) -> str:
        clean = re.sub(r"\s+", " ", text or "").strip()
        return clean[:limit]

    @classmethod
    def _media_refusal_text(cls, text: str, expect: str) -> str:
        """Return only an explicit media refusal line, never an arbitrary page tail."""
        if not text:
            return ""
        patterns = [
            r"^(?:没生成成|视频没生成成功|视频未生成成功|视频生成失败)[^\n]{0,240}"
            r"(?:国家|地区|country|region)[^\n]{0,160}(?:不支持|不可用|无法|not available|unavailable|not supported)",
            r"^(?:could not|couldn't|cannot|can't|unable to)[^\n]{0,120}video[^\n]{0,160}"
            r"(?:country|region|not available|unavailable|not supported)",
        ] if expect == "video" else [
            r"^(?:图片没生成成功|图片未生成成功|图片生成失败|无法生成图片)",
            r"^(?:could not|couldn't|cannot|can't|unable to)[^\n]{0,120}image",
        ]
        for line in reversed((text or "").splitlines()):
            clean = cls._clean_model_text(line)
            if clean and any(re.search(pattern, clean, re.I) for pattern in patterns):
                return clean
        return ""

    # ---------------- Lấy dữ liệu nhị phân (Fetch Bytes) ----------------
    _EXTRACT_JS = r"""
    (async function(src, expect){
      try{
        var u = src;
        if(!u) return JSON.stringify({ok:false,err:'no-media-src'});
        var r = await fetch(u);
        if(!r.ok) return JSON.stringify({ok:false,err:'media-http-'+r.status});
        var b = await r.blob();
        var ab = await b.arrayBuffer();
        var bytes = new Uint8Array(ab);
        var s = '';
        for(var i=0; i<bytes.length; i+=65536){
          s += String.fromCharCode.apply(null, bytes.subarray(i, i+65536));
        }
        return JSON.stringify({ok:true, mime:b.type||'', size:b.size, url:u, b64:btoa(s)});
      }catch(e){
        return JSON.stringify({ok:false, err:String(e)});
      }
    })(%s, %s)
    """

    # ---------------- Hội thoại Văn bản / Code (Text & Code Chat) ----------------
    _AGENT_TEXT_JS = (
        "(function(){"
        "var bs=[].slice.call(document.querySelectorAll("
        "'div[class*=\"hatch-chat-groupable-bubble\"]'));"
        "for(var i=bs.length-1;i>=0;i--){"
        "var cs=bs[i].className||'';"
        "if(/hatch-agent-bubble-bg/.test(cs))return bs[i].innerText||'';}"
        "return '';})()"
    )
    _USER_COUNT_JS = (
        "(function(){"
        "var bs=[].slice.call(document.querySelectorAll("
        "'div[class*=\"hatch-chat-groupable-bubble\"]'));"
        "var n=0;for(var i=0;i<bs.length;i++){"
        "if(/chat-user-bubble/.test(bs[i].className||''))n++;}"
        "return String(n);})()"
    )
    _AGENT_COUNT_JS = (
        "(function(){"
        "var bs=[].slice.call(document.querySelectorAll("
        "'div[class*=\"hatch-chat-groupable-bubble\"]'));"
        "var n=0;for(var i=0;i<bs.length;i++){"
        "if(/hatch-agent-bubble-bg/.test(bs[i].className||''))n++;}"
        "return String(n);})()"
    )
    _POLL_CHAT_JS = (
        "(function(){"
        "var els=[...document.querySelectorAll('*')].filter(function(e){"
        "var s=getComputedStyle(e);"
        "return (s.overflowY==='auto'||s.overflowY==='scroll')&&e.scrollHeight>e.clientHeight+100;});"
        "els.sort(function(a,b){return b.scrollHeight-a.scrollHeight;});"
        "if(els[0])els[0].scrollTop=els[0].scrollHeight;"
        "var scope=document.querySelector('main,[class*=\"chat-scroll\"],[class*=\"hatch-chat-scroll\"]')||document.body;"
        "var bs=[].slice.call(scope.querySelectorAll('div[class*=\"hatch-chat-groupable-bubble\"]'))"
        ".filter(function(b){return /hatch-agent-bubble-bg/.test(b.className||'');});"
        "var nonEmpty=bs.filter(function(b){return ((b.innerText||'').trim().length)>0;});"
        "var txt=nonEmpty.length?(nonEmpty[nonEmpty.length-1].innerText||'').trim():'';"
        "var stop=!!(document.querySelector('[data-testid=\"hatch-composer-stop-button\"]')"
        "||document.querySelector('button[aria-label*=\"Stop\" i]')"
        "||document.querySelector('button[aria-label*=\"停止\"]'));"
        "return JSON.stringify({cnt:nonEmpty.length,total:bs.length,txt:txt,stop:stop});})()"
    )

    def _agent_text(self) -> str:
        """Lấy văn bản của bong bóng trợ lý cuối cùng (nếu không lấy được thì trả về chuỗi rỗng)."""
        try:
            return (self.page.js(self._AGENT_TEXT_JS) or "").strip()
        except Exception:  # noqa: BLE001
            return ""

    def _agent_count(self) -> int:
        try:
            return int(self.page.js(self._AGENT_COUNT_JS) or 0)
        except Exception:  # noqa: BLE001
            return 0

    def _user_count(self) -> int:
        try:
            return int(self.page.js(self._USER_COUNT_JS) or 0)
        except Exception:  # noqa: BLE001
            return 0

    def _poll_chat(self) -> tuple[int, str, bool]:
        try:
            raw = self.page.js(self._POLL_CHAT_JS)
            if raw:
                d = json.loads(raw)
                return int(d.get("cnt") or 0), (d.get("txt") or "").strip(), bool(d.get("stop"))
        except Exception:
            pass
        return 0, "", False

    def chat_stream(self, cookies: dict, prompt: str, expires: dict | None = None,
                    timeout: int | None = None, account_id: str | None = None,
                    stop_event=None):
        """Gửi tin nhắn văn bản và stream từng đoạn token phản hồi gia tăng (Generator Yield).
        
        Áp dụng thuật toán polling tần số cao (chu kỳ 60ms) để bắt ngay ký tự đầu tiên chỉ sau 2-3 giây.
        Theo dõi trạng thái nút Stop để nhận biết thời điểm kết thúc sinh phản hồi của mô hình.
        
        Args:
            cookies (dict): Cookies xác thực phiên tài khoản.
            prompt (str): Câu lệnh hoặc chuỗi ngữ cảnh hội thoại cần gửi.
            expires (dict | None, optional): Hạn dùng của cookies.
            timeout (int | None, optional): Thời gian chờ phản hồi tối đa (giây).
            account_id (str | None, optional): ID tài khoản được gán.
            stop_event (threading.Event | None, optional): Cờ dừng nếu client hủy kết nối SSE.
            
        Yields:
            str: Từng đoạn văn bản gia tăng (delta text) vừa xuất hiện.
            
        Raises:
            MuseGenerationError: Nếu chờ ký tự đầu tiên hoặc hoàn thành phản hồi quá hạn timeout.
        """
        timeout = int(timeout or getattr(self.cfg, "chat_timeout", 300))
        self.ensure_page(cookies, expires, account_id=account_id)
        self.reset_thread(for_chat=True)
        base_agent, base_text, _ = self._poll_chat()
        self._send(prompt)

        t_sent = time.time()
        deadline = t_sent + timeout
        first_token_deadline = min(deadline, t_sent + 40.0)
        sent, last, stable = "", None, 0
        got_first = False

        # 1. Chờ trợ lý sinh nội dung và bắt đầu xuất chữ (lấy mẫu tần suất cao 60ms, yield ngay tức thì khi bắt được những ký tự gia tăng đầu tiên)
        while time.time() < first_token_deadline:
            if stop_event is not None and stop_event.is_set():
                return
            time.sleep(0.06)
            cnt, cur, has_stop = self._poll_chat()
            if not cur or (cnt <= base_agent and cur == base_text):
                if time.time() - t_sent > 14.0:
                    try:
                        tail = self.page.js("document.body.innerText.slice(-500)") or ""
                    except Exception:
                        tail = ""
                    if "Still sending" in tail or "Connecting..." in tail:
                        raise MuseGenerationError("Quá thời gian kết nối VM đám mây (Still sending)")
                continue

            delta = cur[len(sent):] if cur.startswith(sent) else cur
            if delta:
                sent = cur
                yield delta
                last = cur
                got_first = True
                break

        if not got_first:
            raise MuseGenerationError("Quá thời gian chờ phản hồi ký tự đầu tiên từ trợ lý")

        # 2. Liên tục thu nhận văn bản gia tăng (incremental text)
        while time.time() < deadline:
            if stop_event is not None and stop_event.is_set():
                return
            time.sleep(0.06)
            cnt, cur, has_stop = self._poll_chat()
            if not cur:
                continue

            if cur != last:
                delta = cur[len(sent):] if cur.startswith(sent) else cur
                if delta:
                    sent = cur
                    yield delta
                last, stable = cur, 0
            else:
                stable += 1
                # Nút Stop biến mất cho thấy frontend đã hoàn tất sinh nội dung, thoát bình thường sau 3 lần liên tiếp (~0.18s) không có văn bản mới
                if not has_stop and stable >= 3:
                    return
                # Khi nút Stop vẫn còn thì tuyệt đối không cắt sớm (mô hình đang suy nghĩ, khối mã hoặc mạng chập chờn), cho phép chờ đến stable >= 80 (~5s) để chống treo
                if has_stop and stable >= 80:
                    return

        raise MuseGenerationError("Quá thời gian chờ phản hồi từ trợ lý")

    def chat(self, cookies: dict, prompt: str, expires: dict | None = None,
             timeout: int | None = None, account_id: str | None = None) -> str:
        """Gửi một tin nhắn và trả về toàn bộ chuỗi văn bản phản hồi hoàn chỉnh (chế độ đồng bộ non-streaming).
        
        Args:
            cookies (dict): Cookies của tài khoản.
            prompt (str): Câu nhắc cần gửi.
            expires (dict | None, optional): Hạn dùng của cookies.
            timeout (int | None, optional): Thời gian timeout (giây).
            account_id (str | None, optional): ID tài khoản.
            
        Returns:
            str: Toàn bộ nội dung văn bản trả lời của mô hình.
        """
        out = ""
        for chunk in self.chat_stream(cookies, prompt, expires, timeout, account_id=account_id):
            out += chunk
        return out

    def extract_bytes(self, src: str, expect: str = "image", retries: int = 4):
        """Trích xuất mảng byte dữ liệu nhị phân của ảnh/video trực tiếp từ DOM qua JavaScript Blob Fetch.
        
        Args:
            src (str): URL nguồn hoặc định danh của phần tử đa phương tiện.
            expect (str, optional): Loại định dạng mong đợi ('image' hoặc 'video').
            retries (int, optional): Số lần thử lại tối đa nếu fetch chưa sẵn sàng (mặc định: 4).
            
        Returns:
            tuple[bytes, str, str]: Bộ ba gồm (dữ liệu nhị phân byte, chuỗi MIME type, URL gốc).
            
        Raises:
            MuseGenerationError: Nếu không thể giải mã hoặc lấy dữ liệu nhị phân sau số lần thử lại.
        """
        last = "không rõ"
        for _ in range(retries):
            raw = self.page.js(self._EXTRACT_JS % (json.dumps(src), json.dumps(expect)),
                               await_promise=True, timeout=600)
            try:
                info = json.loads(raw) if isinstance(raw, str) else raw
            except Exception:  # noqa: BLE001
                info = {"ok": False, "err": f"phân tích thất bại {str(raw)[:150]}"}
            if info.get("ok"):
                return base64.b64decode(info["b64"]), info.get("mime", ""), info.get("url", "")
            last = info.get("err", "không rõ")
            time.sleep(2)
        raise MuseGenerationError(f"Không thể lấy về kết quả đã tạo: {last}")

    # ---------------- Cơ chế tải về dự phòng (Download Fallback) ----------------
    def _download_fallback(self, src: str, timeout: int = 180) -> str | None:
        """Cơ chế dự phòng: Kích hoạt nút Tải xuống (Download) của phần tử trên giao diện và đón file trong thư mục downloads.
        
        Args:
            src (str): URL nguồn của phần tử cần tải xuống.
            timeout (int, optional): Thời gian chờ file xuất hiện hoàn tất (mặc định: 180 giây).
            
        Returns:
            str | None: Đường dẫn file cục bộ đã tải về thành công hoặc None nếu thất bại.
        """
        before = set(os.listdir(self.cfg.download_dir))
        # ponytail: đóng luồng an toàn khi kết quả được chọn không có nút tải cục bộ;
        # tuyệt đối không nhấp vào nút không liên quan/toàn cục có thể làm tải lại file upload.
        clicked = self.page.js("""(function(src){
            var media=[...document.querySelectorAll('img,video')]
                .find(m=>(m.currentSrc||m.src||'')===src);
            var node=media && media.closest('[data-testid^="hatch-chat-attachment-presentation-"]');
            if(!node) return 'none';
            node=node.closest('[class*="group/widget-presentation"]')||node;
            var b=[...node.querySelectorAll('button,[role=button]')]
                .find(x=>/下载|保存|download/i.test(x.getAttribute('aria-label')||''));
            if(!b) return 'none';
            b.click();return 'ok';
        })(%s)""" % json.dumps(src))
        if clicked == "none":
            return None
        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(1.5)
            new = [f for f in (set(os.listdir(self.cfg.download_dir)) - before)
                   if not f.endswith(".crdownload")]
            if new:
                p = os.path.join(self.cfg.download_dir, max(
                    new, key=lambda f: os.path.getmtime(os.path.join(self.cfg.download_dir, f))))
                if os.path.getsize(p) > 0:
                    return p
        return None

    def _normalize_image(self, img: str) -> tuple[str, str]:
        """Chuẩn hóa dữ liệu ảnh tham chiếu và thực thi chính sách kiểm duyệt MIME type, kích thước và nguồn gốc.
        
        Hỗ trợ: Data URL base64, URL Internet công khai, chuỗi Base64 thô và đường dẫn file cục bộ (nếu bật cờ cho phép).
        
        Args:
            img (str): Chuỗi đại diện cho ảnh (URL, Data URL, Base64 hoặc filepath).
            
        Returns:
            tuple[str, str]: Cặp gồm (chuỗi Base64 đã chuẩn hóa, chuỗi MIME type như 'image/png').
            
        Raises:
            MuseGenerationError: Nếu file không phải là ảnh, định dạng không hợp lệ hoặc vượt quá 10 MiB.
            RefImageSafetyError: Nếu URL trỏ về mạng nội bộ hoặc cố tình đọc file cục bộ bị cấm.
        """
        if not img:
            return "", "image/png"
        img = str(img).strip()

        def checked(data: bytes, mime: str) -> tuple[str, str]:
            mime = (mime or "image/png").split(";", 1)[0].strip().lower()
            if not mime.startswith("image/"):
                raise MuseGenerationError(f"Tệp tham chiếu không phải là hình ảnh ({mime or 'unknown'})")
            if len(data) > MAX_REFERENCE_IMAGE_BYTES:
                raise MuseGenerationError("Ảnh tham chiếu đơn lẻ vượt quá giới hạn 10 MiB")
            return base64.b64encode(data).decode("ascii"), mime

        if img.startswith("data:"):
            head, sep, payload = img.partition(",")
            if not sep:
                raise MuseGenerationError("Định dạng Data URL của ảnh tham chiếu không hợp lệ")
            mime = head[5:].split(";", 1)[0] or "image/png"
            try:
                data = (base64.b64decode(payload.strip(), validate=True)
                        if ";base64" in head.lower()
                        else urllib.parse.unquote_to_bytes(payload))
            except (binascii.Error, ValueError) as exc:
                raise MuseGenerationError("Mã hóa Data URL của ảnh tham chiếu không hợp lệ") from exc
            return checked(data, mime)

        if img.startswith(("http://", "https://")):
            try:
                req = urllib.request.Request(img, headers={"User-Agent": "Mozilla/5.0"})
                response = (urllib.request.urlopen(req, timeout=20)
                            if self.cfg.ref_image_private_fetch
                            else _open_public_ref_image(img))
                with response as resp:
                    mime = resp.headers.get_content_type() or "image/png"
                    data = resp.read(MAX_REFERENCE_IMAGE_BYTES + 1)
                return checked(data, mime)
            except (RefImageSafetyError, MuseGenerationError):
                raise
            except Exception as exc:
                raise MuseGenerationError(
                    f"Tải ảnh tham chiếu từ xa thất bại: {type(exc).__name__}") from exc

        # Chuỗi Base64 thô không chứa đường dẫn phía máy chủ và vẫn an toàn trong chế độ hạn chế.
        try:
            return checked(base64.b64decode(img, validate=True), "image/png")
        except (binascii.Error, ValueError):
            pass

        if not self.cfg.ref_image_local_files:
            raise RefImageSafetyError(
                "Đường dẫn cục bộ của ảnh tham chiếu bị từ chối; nếu thực sự cần đọc tệp trên máy chủ, vui lòng đặt tường minh "
                "MUSE2API_REF_IMAGE_LOCAL_FILES=1")
        if os.path.isfile(img):
            try:
                if os.path.getsize(img) > MAX_REFERENCE_IMAGE_BYTES:
                    raise MuseGenerationError("Ảnh tham chiếu đơn lẻ vượt quá giới hạn 10 MiB")
                with open(img, "rb") as f:
                    return checked(f.read(MAX_REFERENCE_IMAGE_BYTES + 1),
                                   mimetypes.guess_type(img)[0] or "image/png")
            except MuseGenerationError:
                raise
            except Exception as exc:
                raise MuseGenerationError(
                    f"Đọc ảnh tham chiếu cục bộ thất bại: {type(exc).__name__}") from exc
        raise MuseGenerationError("Ảnh tham chiếu phải là URL, Data URL, ảnh cục bộ hoặc chuỗi Base64 hợp lệ")

    def _clear_attachments(self):
        """Xóa ảnh thu nhỏ của tệp đính kèm còn sót lại trong ô nhập trò chuyện (tương thích giao diện Trung/Anh)."""
        try:
            self.page.js(
                "(function(){"
                "var btns=Array.from(document.querySelectorAll('button[aria-label]')).filter(function(b){"
                "var al=b.getAttribute('aria-label')||'';"
                "return /remove\\s*attachment|移除附件|删除附件|移除|删除/i.test(al);"
                "});"
                "btns.forEach(function(b){b.click();});"
                "Array.from(document.querySelectorAll('input[type=\"file\"]')).forEach(function(inp){inp.value='';});"
                "return btns.length;"
                "})()")
            time.sleep(0.3)
        except Exception:
            pass

    def _attach_images(self, image_data: list[str]):
        """Bơm tuần tự các ảnh tham chiếu vào input file của khung soạn thảo và xác nhận đã hiển thị đầy đủ.
        
        Args:
            image_data (list[str]): Danh sách ảnh tham chiếu (tối đa 4 ảnh, tổng dung lượng không quá 24 MiB).
            
        Raises:
            MuseGenerationError: Nếu vượt quá số lượng, tổng dung lượng hoặc giao diện không xuất hiện nút xác nhận đính kèm.
        """
        if len(image_data) > MAX_REFERENCE_IMAGES:
            raise MuseGenerationError(f"Ảnh tham chiếu tối đa {MAX_REFERENCE_IMAGES} ảnh")
        images = []
        total_bytes = 0
        for index, value in enumerate(image_data):
            if not value:
                continue
            b64, mime = self._normalize_image(value)
            if not b64:
                raise MuseGenerationError(f"Đọc ảnh tham chiếu thứ {index + 1} thất bại, đã dừng tạo")
            try:
                total_bytes += len(base64.b64decode(b64, validate=True))
            except (binascii.Error, ValueError) as exc:
                raise MuseGenerationError(f"Mã hóa ảnh tham chiếu thứ {index + 1} không hợp lệ") from exc
            if total_bytes > MAX_REFERENCE_TOTAL_BYTES:
                raise MuseGenerationError("Tổng dung lượng ảnh tham chiếu vượt quá giới hạn 24 MiB")
            images.append({"b64": b64, "mime": mime, "index": index + 1})
        if not images:
            return

        self._clear_attachments()

        _INJECT_JS = """
        (async function(images) {
            try {
                // Trong composer thực tế có thể có nhiều input file; ưu tiên lấy input nằm bên trong composer
                var inputs = Array.from(document.querySelectorAll('input[type="file"]'));
                if (!inputs.length) return JSON.stringify({ok: false, err: 'no-file-input'});
                var ov = document.querySelector('[data-testid="hatch-composer-placeholder-overlay"]');
                var composer = ov ? ov.closest('form') : null;
                var input = null;
                if (composer) {
                    input = inputs.find(function(x){ return composer.contains(x); }) || null;
                }
                if (!input) {
                    // Phương án dự phòng tiếp theo: lấy input không nằm trong bong bóng trò chuyện
                    input = inputs.find(function(x){
                        return !x.closest('[class*=chat-user-bubble], [class*="group/msg"]');
                    }) || inputs[0];
                }
                // Một số phiên bản có accept để trống, bổ sung image/* để trang web chấp nhận File lần này
                if (!input.getAttribute('accept')) input.setAttribute('accept', 'image/*');
                for (var image of images) {
                    var byteChars = atob(image.b64);
                    var byteNumbers = new Array(byteChars.length);
                    for (var i = 0; i < byteChars.length; i++) {
                        byteNumbers[i] = byteChars.charCodeAt(i);
                    }
                    var mime = image.mime || 'image/png';
                    var byteArray = new Uint8Array(byteNumbers);
                    var blob = new Blob([byteArray], {type: mime});
                    var ext = mime.split('/')[1] || 'png';
                    if (ext === 'jpeg') ext = 'jpg';
                    var dt = new DataTransfer();
                    dt.items.add(new File(
                        [blob], 'reference_image_' + image.index + '.' + ext, {type: mime}));
                    input.files = dt.files;
                    input.dispatchEvent(new Event('change', {bubbles: true}));
                    input.dispatchEvent(new Event('input', {bubbles: true}));
                    await new Promise(function(resolve){ setTimeout(resolve, 350); });
                }
                return JSON.stringify({ok: true, count: images.length});
            } catch(e) {
                return JSON.stringify({ok: false, err: String(e)});
            }
        })(%s)
        """
        try:
            raw_res = self.page.js(
                _INJECT_JS % json.dumps(images), await_promise=True,
                timeout=max(15, len(images) * 3))
            res_obj = json.loads(raw_res) if isinstance(raw_res, str) else raw_res
            if not res_obj.get("ok") or res_obj.get("count") != len(images):
                raise MuseGenerationError("Đính kèm ảnh tham chiếu thất bại, đã dừng tạo")
        except Exception as e:
            raise MuseGenerationError("Đính kèm ảnh tham chiếu thất bại, đã dừng tạo") from e

        # Chờ xác nhận tệp đính kèm trong ô nhập liệu; hình ảnh lịch sử không chứng minh được lần tải lên này thành công.
        # Giao diện hiện tại hỗ trợ nút xác nhận aria-label = "附加文件"/"移除附件";
        # đồng thời tương thích tiếng Anh (Remove attachment / Attach file), và dự phòng bằng ảnh thu nhỏ bên trong composer.
        deadline = time.time() + 15.0
        attached_count = 0
        while time.time() < deadline:
            attached_count = self.page.js(
                """(function(){
                var ov = document.querySelector('[data-testid="hatch-composer-placeholder-overlay"]');
                var composer = ov ? (ov.closest('form') || ov.parentElement.parentElement.parentElement) : null;
                if (!composer) return 0;
                var btns = Array.from(composer.querySelectorAll('button[aria-label]'));
                var removeCount = btns.filter(function(b){
                    return /remove\\s*attachment|移除附件|删除附件/i.test(b.getAttribute('aria-label') || '');
                }).length;
                if (removeCount) return removeCount;
                return composer.querySelectorAll('img, video').length;
                })()"""
            )
            if int(attached_count or 0) >= len(images):
                break
            time.sleep(0.3)
        else:
            raise MuseGenerationError(
                f"Chưa xác nhận tải lên ảnh tham chiếu ({int(attached_count or 0)}/{len(images)}), đã dừng tạo")
        time.sleep(0.5)

    def _attach_image(self, image_data: str):
        """Hàm bọc tương thích ngược hỗ trợ đính kèm 1 ảnh tham chiếu duy nhất.
        
        Args:
            image_data (str): Dữ liệu ảnh tham chiếu đơn lẻ.
        """
        self._attach_images([image_data])
    # ---------------- Luồng chính (Main Generation Workflow) ----------------
    def generate(self, cookies: dict, prompt: str, expect: str = "image",
                 timeout: int = 240, expires: dict | None = None, account_id: str | None = None,
                 on_progress=None, reference_image: str | None = None,
                 reference_images: list[str] | None = None,
                 stop_event=None) -> dict:
        """Quy trình toàn diện điều khiển sinh hình ảnh hoặc video trên giao diện web muse.ai.
        
        Trình tự các bước:
          1. Đảm bảo tab trình duyệt sẵn sàng (`ensure_page`) và điều hướng về phiên sạch (`reset_thread`).
          2. Nếu có ảnh tham chiếu: chuẩn hóa và inject vào composer (`_attach_images`); nếu không, xóa ảnh cũ (`_clear_attachments`).
          3. Gửi câu nhắc (`_send`).
          4. Chờ attachment kết quả mới xuất hiện (`_wait_attachment`).
          5. Trích xuất mảng byte qua Blob (`extract_bytes`) hoặc fallback click Download (`_download_fallback`).
          6. Lưu file vào thư mục `media_dir` với tên UUID duy nhất và trả về metadata chi tiết.
          
        Args:
            cookies (dict): Danh sách cookies phiên tài khoản.
            prompt (str): Câu lệnh miêu tả hình ảnh/video cần tạo.
            expect (str, optional): Loại sản phẩm mong đợi ('image' hoặc 'video'). Mặc định là 'image'.
            timeout (int, optional): Thời gian timeout tối đa cho toàn bộ tác vụ (giây).
            expires (dict | None, optional): Hạn dùng của các cookie.
            account_id (str | None, optional): ID tài khoản thực hiện.
            on_progress (callable | None, optional): Callback nhận cập nhật tiến độ sinh nội dung.
            reference_image (str | None, optional): Đường dẫn/URL một ảnh tham chiếu (tương thích cũ).
            reference_images (list[str] | None, optional): Danh sách nhiều ảnh tham chiếu (tối đa 4 ảnh).
            stop_event (threading.Event | None, optional): Cờ dừng sớm nếu client hủy yêu cầu.
            
        Returns:
            dict: Thông tin sản phẩm hoàn thành gồm path, filename, size, ext, mime, kind, w, h...
            
        Raises:
            MuseGenerationError: Khi gặp lỗi gửi prompt, timeout chờ attachment hoặc sai lệch loại media.
        """
        deadline = time.monotonic() + timeout
        self.ensure_page(cookies, expires, account_id=account_id)
        self.reset_thread(for_chat=False)
        self._scroll_bottom()
        refs = list(reference_images or ([] if not reference_image else [reference_image]))
        if refs:
            self._attach_images(refs)
        else:
            self._clear_attachments()
        atts_before = self.attachments()
        baseline_sources = {a.get(k) for a in atts_before for k in ("src", "vSrc", "iSrc") if a.get(k)}
        base = atts_before[-1] if atts_before else {}
        baseline_src = base.get("src") or ""
        base_agent_cnt = self._agent_count()
        if time.monotonic() >= deadline:
            raise MuseGenerationError("Quá thời gian chuẩn bị tác vụ, đã dừng gửi")
        if self._send(prompt) not in ("clicked", "enter-sent"):
            raise MuseGenerationError("Chưa xác nhận gửi prompt, đã dừng tạo")
        att = self._wait_attachment(
            baseline_src, max(0, deadline - time.monotonic()), expect, on_progress=on_progress,
            base_agent_cnt=base_agent_cnt, base_att_cnt=len(atts_before),
            stop_event=stop_event, baseline_sources=baseline_sources
        )
        if not att:
            self._debug_dump("no-attachment")
            raise MuseGenerationError("Quá thời gian chờ tạo nội dung, không xuất hiện kết quả mới")

        os.makedirs(self.cfg.media_dir, exist_ok=True)
        data = mime = url = None
        selected_src = (att.get("vSrc") if expect == "video" else None) or att.get("src") or ""
        try:
            data, mime, url = self.extract_bytes(selected_src, expect=expect)
        except Exception:  # noqa: BLE001
            self._debug_dump("extract-fail")

        if data:
            ext = self._pick_ext(mime, url, expect)
            name = f"{uuid.uuid4().hex}{ext}"
            dst = os.path.join(self.cfg.media_dir, name)
            with open(dst, "wb") as f:
                f.write(data)
            kind = "video" if ext in (".mp4", ".webm", ".mov") else "image"
            if expect == "video" and kind != "video":
                raise MuseGenerationError(f"Kỳ vọng tạo video nhưng thành phẩm trích xuất là hình ảnh ({ext}), từ chối trả về ảnh thay cho video")
            return {"path": dst, "filename": name, "size": len(data), "ext": ext, "mime": mime,
                    "kind": kind,
                    "via": "blob", "attachment": att.get("tid"),
                    "w": att.get("w"), "h": att.get("h")}

        path = self._download_fallback(selected_src)
        if not path:
            raise MuseGenerationError("Đã tạo xong nhưng không thể lấy tệp về")
        ext = os.path.splitext(path)[1].lower() or ".bin"
        name = f"{uuid.uuid4().hex}{ext}"
        dst = os.path.join(self.cfg.media_dir, name)
        shutil.move(path, dst)
        kind = "video" if ext in (".mp4", ".webm", ".mov") else "image"
        if expect == "video" and kind != "video":
            raise MuseGenerationError(f"Kỳ vọng tạo video nhưng thành phẩm tải về là hình ảnh ({ext}), từ chối trả về ảnh thay cho video")
        return {"path": dst, "filename": name, "size": os.path.getsize(dst), "ext": ext, "mime": "",
                "kind": kind,
                "via": "download", "attachment": att.get("tid"),
                "w": att.get("w"), "h": att.get("h")}

    @staticmethod
    def _pick_ext(mime: str, url: str, expect: str) -> str:
        m = (mime or "").lower()
        for key, ext in (("mp4", ".mp4"), ("webm", ".webm"), ("png", ".png"),
                         ("jpeg", ".jpg"), ("jpg", ".jpg"), ("webp", ".webp"),
                         ("gif", ".gif")):
            if key in m:
                return ext
        for e in (".mp4", ".webm", ".png", ".jpg", ".webp"):
            if e in (url or "").lower():
                return e
        return ".mp4" if expect == "video" else ".png"

    def _debug_dump(self, tag: str):
        try:
            info = self.page.js(
                "JSON.stringify({atts:[...document.querySelectorAll('" + ATT_SEL + "')]"
                ".map(function(a){var m=a.querySelector('img,video');return {"
                "tid:a.getAttribute('data-testid'),"
                "src:m?(m.currentSrc||m.src||'').slice(0,60):''};}),"
                "buttons:[...document.querySelectorAll('button,[role=button]')]"
                ".filter(b=>b.offsetParent!==null)"
                ".map(b=>b.getAttribute('aria-label')||b.innerText.trim().slice(0,20))"
                ".filter(Boolean).slice(-40),"
                "tail:document.body.innerText.slice(-500)})")
            with open(os.path.join(self.cfg.data_dir, f"debug-{tag}.json"), "w",
                      encoding="utf-8") as f:
                f.write(str(info))
        except Exception:  # noqa: BLE001
            pass
