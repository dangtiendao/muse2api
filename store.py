"""Hồ chứa tài khoản và lưu trữ nhiệm vụ (Lưu trữ JSON, ghi tệp nguyên tử) (Account Pool & Task Store with Atomic JSON Persistence).

Module này đảm nhiệm:
  - Quản lý danh sách tài khoản muse.ai (Account Pool) và trạng thái phiên đăng nhập.
  - Quản lý danh sách nhiệm vụ bất đồng bộ (Task Store: tạo ảnh, tạo video, v.v.).
  - Tính toán thời hạn sống chính xác của tài khoản dựa trên các cookie cốt lõi (hatch_sess, hatch_vml).
  - Thuật toán điều phối chọn tài khoản thông minh (Warm-Tab Sticky Affinity kết hợp LRU Balancing).
  - Đảm bảo an toàn dữ liệu đa luồng (threading.Lock) và an toàn ghi đĩa (Atomic Write qua file tạm).
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
import time
import uuid

# Khóa đồng bộ hóa toàn cục đảm bảo an toàn truy cập file và danh sách đa luồng
_LOCK = threading.Lock()

# Cookie cốt lõi quyết định trạng thái tài khoản (đồng bộ nhất quán với engine.ESSENTIAL_COOKIES)
# Các cookie cốt lõi quyết định phiên sống còn của tài khoản muse.ai:
# - hatch_sess: Cookie phiên làm việc chính (thời hạn ~30 ngày).
# - hatch_vml: Cookie máy ảo/container làm việc (thời hạn cố định ~48 giờ, không tự động tăng khi dùng).
# Lưu ý: hatch_gw là bộ nhớ đệm định tuyến gateway (~1 năm), thiếu gw vẫn có thể tự xin cấp lại;
# nhưng thiếu 2 cookie trên thì phiên sẽ bị xem là hết hạn hoàn toàn.
ESSENTIAL_COOKIES = ("hatch_sess", "hatch_vml")


def _is_pos(v) -> bool:
    """Kiểm tra xem giá trị đầu vào có thể chuyển thành số nguyên dương (> 0) hay không.
    
    Args:
        v: Giá trị cần kiểm tra (số hoặc chuỗi số).
        
    Returns:
        bool: True nếu là số nguyên dương hợp lệ, ngược lại False.
    """
    try:
        return int(v) > 0
    except (TypeError, ValueError):
        return False


# hatch_vml cố định khoảng 2 ngày và không được gia hạn thêm khi sử dụng — đây chính là cookie quyết định vòng đời tài khoản.
# Thời hạn sống mặc định của hatch_vml: 2 ngày (tính bằng giây).
# Khi không đọc được expires trực tiếp từ trình duyệt, hệ thống sẽ ước lượng bằng: thời điểm import + 2 ngày.
VML_TTL = 2 * 86400


def min_expiry(cookies_exp: dict | None) -> int | None:
    """Tìm mốc thời gian hết hạn sớm nhất (Unix timestamp) trong các cookie thiết yếu.
    
    Đóng vai trò cơ chế fallback chung nếu không xác định được cookie cụ thể.
    
    Args:
        cookies_exp (dict | None): Dictionary chứa thời hạn hết hạn dạng {cookie_name: timestamp}.
        
    Returns:
        int | None: Timestamp hết hạn sớm nhất hoặc None nếu không có dữ liệu hợp lệ.
    """
    if not cookies_exp:
        return None
    vals = []
    for name in ESSENTIAL_COOKIES:
        v = cookies_exp.get(name)
        try:
            v = int(v)
        except (TypeError, ValueError):
            continue
        if v > 0:
            vals.append(v)
    if not vals:
        for v in cookies_exp.values():
            try:
                v = int(v)
            except (TypeError, ValueError):
                continue
            if v > 0:
                vals.append(v)
    return min(vals) if vals else None


def account_expiry(cookies_exp: dict | None,
                   base_ts: int | None = None) -> int | None:
    """Xác định thời gian hết hạn thực tế của tài khoản theo thứ tự ưu tiên chặt chẽ.

    Thứ tự ưu tiên:
      1) Thuộc tính expires thực tế của `hatch_vml` (chính xác nhất).
      2) Nếu thiếu expires của hatch_vml: ước tính bằng base_ts (thời điểm import/đồng bộ) + VML_TTL (2 ngày).
      3) Nếu không có base_ts: fallback về cookie hết hạn sớm nhất trong min_expiry.
      
    Args:
        cookies_exp (dict | None): Dictionary chứa thời hạn các cookie.
        base_ts (int | None, optional): Mốc thời gian làm gốc để cộng dồn ước lượng.
        
    Returns:
        int | None: Unix timestamp đại diện thời điểm tài khoản hết hạn.
    """
    ce = cookies_exp or {}
    vml = ce.get("hatch_vml")
    if _is_pos(vml):
        return int(vml)
    if base_ts:
        return int(base_ts) + VML_TTL
    return min_expiry(ce)


def _read(path: str, default):
    """Đọc và giải mã dữ liệu JSON từ file an toàn.
    
    Args:
        path (str): Đường dẫn file JSON cần đọc.
        default: Giá trị trả về mặc định nếu file không tồn tại hoặc lỗi đọc.
        
    Returns:
        Dữ liệu đã parse từ JSON hoặc giá trị `default`.
    """
    if not os.path.isfile(path):
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return default


def _write(path: str, obj):
    """Ghi dữ liệu JSON xuống đĩa theo cơ chế ghi nguyên tử (Atomic Write).
    
    Tạo file tạm (mkstemp) trong cùng thư mục, ghi nội dung JSON hoàn chỉnh,
    sau đó đổi tên nguyên tử (atomic replace) đè lên file đích. Điều này ngăn
    ngừa triệt để nguy cơ file bị hỏng hoặc mất dữ liệu khi mất điện hoặc crash ứng dụng.
    
    Args:
        path (str): Đường dẫn file đích cần ghi.
        obj: Đối tượng dữ liệu cần serialize sang JSON.
    """
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


class Store:
    """Kho lưu trữ dữ liệu trung tâm của muse2api (Data Storage Layer).
    
    Quản lý danh sách tài khoản muse.ai trong accounts.json và hàng đợi tác vụ trong tasks.json.
    Cung cấp các API thread-safe cho tầng ứng dụng.
    """

    def __init__(self, cfg):
        """Khởi tạo kho lưu trữ và nạp dữ liệu từ đĩa.
        
        Args:
            cfg (Config): Thể hiện cấu hình hệ thống chứa đường dẫn file dữ liệu.
        """
        self.cfg = cfg
        self.accounts: list[dict] = _read(cfg.accounts_file, [])
        for a in self.accounts:
            ce = a.get("cookies_exp") or {}
            if _is_pos(ce.get("hatch_vml")):
                a["expires_at"] = int(ce["hatch_vml"])
        self.tasks: dict[str, dict] = _read(cfg.tasks_file, {})

    # ---------- Quản lý Tài khoản (Accounts) ----------
    def add_account(self, cookies: dict, label: str = "",
                    cookies_exp: dict | None = None) -> dict:
        """Thêm một tài khoản muse.ai mới vào hồ chứa tài khoản (Account Pool).
        
        Args:
            cookies (dict): Dictionary chứa các cặp cookie dạng {name: value}.
            label (str, optional): Nhãn đặt cho tài khoản (mặc định lấy theo ID).
            cookies_exp (dict | None, optional): Dictionary chứa hạn dùng của các cookie.
            
        Returns:
            dict: Bản ghi tài khoản vừa được tạo và lưu trữ.
        """
        with _LOCK:
            aid = uuid.uuid4().hex[:12]
            exp = {k: int(v) for k, v in (cookies_exp or {}).items()
                   if _is_pos(v)}
            now = int(time.time())
            acc = {"id": aid, "label": label or aid, "cookies": cookies,
                   "cookies_exp": exp, "expires_at": account_expiry(exp, now),
                   "expiry_anchor": None,
                   "enabled": True, "created_at": now,
                   "last_used": None, "last_keepalive": None, "use_count": 0,
                   "ok": None, "note": "", "synced_at": None}
            self.accounts.append(acc)
            _write(self.cfg.accounts_file, self.accounts)
            return acc

    def list_accounts(self) -> list[dict]:
        """Liệt kê toàn bộ tài khoản trong hồ chứa (đã loại trừ trường cookies nhạy cảm).
        
        Bổ sung các trường tính toán phục vụ giao diện: cookie_count, essential_ok, expires_estimated.
        
        Returns:
            list[dict]: Danh sách tài khoản an toàn để trả về cho client / Admin Web UI.
        """
        out = []
        for a in self.accounts:
            item = {k: v for k, v in a.items() if k != "cookies"}
            ce = a.get("cookies_exp") or {}
            if _is_pos(ce.get("hatch_vml")):
                item["expires_at"] = int(ce["hatch_vml"])
            item["cookie_count"] = len(a.get("cookies", {}))
            item["essential_ok"] = all(
                a.get("cookies", {}).get(n) for n in ESSENTIAL_COOKIES)
            # Thời hạn hiệu lực là expires đo được thực tế của hatch_vml, hay được ước lượng theo "vòng đời 2 ngày"
            item["expires_estimated"] = not _is_pos(ce.get("hatch_vml"))
            out.append(item)
        return out

    def delete_account(self, aid: str) -> bool:
        """Xóa tài khoản khỏi hồ chứa theo ID.
        
        Args:
            aid (str): ID tài khoản cần xóa.
            
        Returns:
            bool: True nếu tìm thấy và xóa thành công, ngược lại False.
        """
        with _LOCK:
            n = len(self.accounts)
            self.accounts = [a for a in self.accounts if a["id"] != aid]
            _write(self.cfg.accounts_file, self.accounts)
            return len(self.accounts) != n

    def pick_account(self, preferred_id: str | None = None, rotate: bool = True,
                     force_rotate: bool = False, exclude_id: str | None = None,
                     exclude_ids: set[str] | list[str] | None = None,
                     record_use: bool = True) -> dict | None:
        """Thuật toán chọn tài khoản tối ưu từ hồ chứa tài khoản khả dụng.
        
        Chiến lược điều phối:
          1. Lọc các tài khoản đang bật (`enabled=True`) và có cookie.
          2. Loại bỏ các tài khoản đang bị khóa bởi các luồng concurrent khác (`exclude_ids`, `exclude_id`).
          3. Ưu tiên giữ kết nối ấm (Warm-Tab Sticky Affinity): Nếu truyền `preferred_id` và tài khoản vẫn khỏe,
             tiếp tục tái sử dụng tài khoản này tối đa 15 lần liên tiếp để tránh mất thời gian reload tab.
          4. Khi đạt giới hạn 15 lần hoặc cần xoay tua: sắp xếp các tài khoản khỏe theo thứ tự LRU
             (last_used nhỏ nhất và use_count nhỏ nhất) để chia đều tải trọng.
        
        Args:
            preferred_id (str | None): ID tài khoản ưu tiên tái sử dụng (đang có tab ấm).
            rotate (bool): Cho phép luân chuyển sang tài khoản khác khi đủ ngưỡng sticky (mặc định: True).
            force_rotate (bool): Bắt buộc luân chuyển ngay lập tức, bỏ qua tài khoản preferred.
            exclude_id (str | None): ID tài khoản cần tránh (ví dụ vừa gặp lỗi).
            exclude_ids (set[str] | list[str] | None): Tập hợp các ID tài khoản đang bận xử lý song song.
            record_use (bool): Có ghi nhận tăng `use_count` và cập nhật `last_used` hay không.
            
        Returns:
            dict | None: Tài khoản được chọn hoặc None nếu toàn bộ tài khoản đều bận/không khả dụng.
        """
        with _LOCK:
            live = [a for a in self.accounts if a.get("enabled", True) and a.get("cookies")]
            if not live:
                return None
            blocked = set(exclude_ids or [])
            if exclude_id:
                blocked.add(exclude_id)
            if blocked:
                available = [a for a in live if a["id"] not in blocked]
                if available:
                    live = available
                elif exclude_ids is not None:
                    # Trong chế độ đồng thời yêu cầu tránh toàn bộ tài khoản bận, nhưng hiện không còn tài khoản trống
                    return None
                elif len(live) > 1:
                    live = [a for a in live if a["id"] != exclude_id] or live
            if preferred_id and not force_rotate:
                for a in live:
                    if a["id"] == preferred_id and a.get("ok") is not False:
                        sticky_n = getattr(self, "_sticky_count", 0) if getattr(self, "_sticky_id", None) == preferred_id else 0
                        if not rotate or sticky_n < 15:
                            self._sticky_id = preferred_id
                            self._sticky_count = sticky_n + 1
                            if record_use:
                                a["last_used"] = time.time()
                                a["use_count"] = a.get("use_count", 0) + 1
                                _write(self.cfg.accounts_file, self.accounts)
                            return a
            healthy = [a for a in live if a.get("ok") is not False]
            candidates = healthy if healthy else live
            candidates.sort(key=lambda a: (a.get("last_used") or 0.0, a.get("use_count") or 0))
            acc = candidates[0]
            self._sticky_id = acc["id"]
            self._sticky_count = 1
            if record_use:
                acc["last_used"] = time.time()
                acc["use_count"] = acc.get("use_count", 0) + 1
                _write(self.cfg.accounts_file, self.accounts)
            return acc

    def touch_keepalive(self, aid: str, ok: bool | None = True, note: str = ""):
        """Cập nhật mốc thời gian và trạng thái kiểm tra bảo hoạt (Keepalive) của tài khoản.
        
        Args:
            aid (str): ID tài khoản cần ghi nhận.
            ok (bool | None, optional): Kết quả kiểm tra (True: thành công; False: thất bại; None: chưa xác định).
            note (str, optional): Ghi chú bổ sung hoặc chi tiết lỗi.
        """
        with _LOCK:
            now_ts = int(time.time())
            for a in self.accounts:
                if a["id"] == aid:
                    if ok is not None:
                        a["ok"] = ok
                    if ok is True:
                        a["last_keepalive"] = now_ts
                        # Chỉ tin cậy thời hạn cookie thực tế hoặc mốc import gốc, không tự tiện cộng khống 48h
                        a["expires_at"] = account_expiry(
                            a.get("cookies_exp"), a.get("expiry_anchor") or a.get("created_at"))
                    if note:
                        a["note"] = note[:300]
                    a["checked_at"] = now_ts
            _write(self.cfg.accounts_file, self.accounts)

    def mark(self, aid: str, ok: bool, note: str = ""):
        """Đánh dấu trạng thái sức khỏe (health status) cho tài khoản sau một thao tác.
        
        Args:
            aid (str): ID tài khoản cần đánh dấu.
            ok (bool): True nếu tài khoản hoạt động bình thường, False nếu gặp lỗi.
            note (str, optional): Ghi chú tóm tắt nguyên nhân lỗi hoặc trạng thái.
        """
        with _LOCK:
            for a in self.accounts:
                if a["id"] == aid:
                    a["ok"] = ok
                    a["note"] = note[:300]
                    a["checked_at"] = int(time.time())
            _write(self.cfg.accounts_file, self.accounts)

    def get_account(self, aid: str) -> dict | None:
        """Lấy thông tin chi tiết đầy đủ (kèm cả cookie) của một tài khoản theo ID.
        
        Args:
            aid (str): ID tài khoản cần tìm.
            
        Returns:
            dict | None: Đối tượng tài khoản hoặc None nếu không tồn tại.
        """
        for a in self.accounts:
            if a["id"] == aid:
                return a
        return None

    def update_account(self, aid: str, **kw) -> dict | None:
        """Cập nhật linh hoạt các thuộc tính của tài khoản (nhãn, trạng thái kích hoạt, cookies...).
        
        Nếu truyền vào `cookies_exp`, hệ thống sẽ tự động tính toán lại `expires_at`.
        Quy tắc duy trì mốc neo ước lượng `expiry_anchor` (tránh bị đẩy lùi hạn dùng sai lệch):
          - Đọc được expires thực tế của hatch_vml -> Xóa mốc neo, dùng trực tiếp giá trị thực.
          - Không đọc được expires và mốc neo trống -> Cố định mốc neo tại thời điểm hiện tại (chỉ neo 1 lần).
          - Bổ sung cookie phiên mới tinh (đăng nhập lại) -> Gọi hàm kèm expiry_anchor=now để làm mới.
        
        Args:
            aid (str): ID tài khoản cần cập nhật.
            **kw: Các trường giá trị cần thay đổi (các trường có giá trị None sẽ bị bỏ qua).
            
        Returns:
            dict | None: Đối tượng tài khoản sau khi cập nhật hoặc None nếu không tìm thấy.
        """
        with _LOCK:
            for a in self.accounts:
                if a["id"] == aid:
                    for k, v in kw.items():
                        if v is not None:
                            a[k] = v
                    if "cookies_exp" in kw and kw["cookies_exp"] is not None:
                        ce = a["cookies_exp"]
                        if _is_pos(ce.get("hatch_vml")):
                            a["expiry_anchor"] = None
                        elif not a.get("expiry_anchor"):
                            a["expiry_anchor"] = int(time.time())
                        a["expires_at"] = account_expiry(
                            ce, a.get("expiry_anchor") or a.get("created_at"))
                    _write(self.cfg.accounts_file, self.accounts)
                    return a
        return None

    def stats(self) -> dict:
        """Thống kê tổng quan tình trạng hồ chứa tài khoản.
        
        Returns:
            dict: Tổng số tài khoản, số đang bật, số tắt, số tài khoản khỏe, số lỗi,
                  số tài khoản sắp hết hạn (<3 ngày) và số đã quá hạn.
        """
        now = int(time.time())
        total = len(self.accounts)
        enabled = sum(1 for a in self.accounts if a.get("enabled", True))
        bad = sum(1 for a in self.accounts
                  if a.get("enabled", True) and a.get("ok") is False)
        healthy = sum(1 for a in self.accounts
                      if a.get("enabled", True) and a.get("ok") is True)
        expiring = sum(1 for a in self.accounts
                       if a.get("enabled", True)
                       and a.get("expires_at")
                       and a["expires_at"] - now < 3 * 86400)
        expired = sum(1 for a in self.accounts
                      if a.get("enabled", True)
                      and a.get("expires_at") and a["expires_at"] <= now)
        return {"total": total, "enabled": enabled, "disabled": total - enabled,
                "healthy": healthy, "error": bad,
                "expiring": expiring, "expired": expired}

    # ---------- Quản lý Nhiệm vụ Bất đồng bộ (Tasks) ----------
    def create_task(self, kind: str, prompt: str) -> dict:
        """Tạo một bản ghi nhiệm vụ mới trong hàng đợi xử lý bất đồng bộ.
        
        Args:
            kind (str): Thể loại nhiệm vụ (ví dụ: 'image', 'video').
            prompt (str): Nội dung câu lệnh / câu nhắc của người dùng.
            
        Returns:
            dict: Bản ghi nhiệm vụ với trạng thái ban đầu là 'queued'.
        """
        with _LOCK:
            tid = "task_" + uuid.uuid4().hex[:20]
            t = {"id": tid, "object": "task", "kind": kind, "prompt": prompt,
                 "status": "queued", "created_at": int(time.time()),
                 "updated_at": int(time.time()), "result": None, "error": None}
            self.tasks[tid] = t
            _write(self.cfg.tasks_file, self.tasks)
            return t

    def update_task(self, tid: str, **kw):
        """Cập nhật trạng thái hoặc dữ liệu kết quả của một nhiệm vụ theo ID.
        
        Args:
            tid (str): ID nhiệm vụ cần cập nhật.
            **kw: Các trường thông tin cần cập nhật (status, result, error...).
            
        Returns:
            dict | None: Đối tượng nhiệm vụ sau khi cập nhật hoặc None nếu không tồn tại.
        """
        with _LOCK:
            t = self.tasks.get(tid)
            if not t:
                return None
            t.update(kw)
            t["updated_at"] = int(time.time())
            _write(self.cfg.tasks_file, self.tasks)
            return t

    def get_task(self, tid: str) -> dict | None:
        """Lấy thông tin một nhiệm vụ theo ID.
        
        Args:
            tid (str): ID nhiệm vụ cần lấy.
            
        Returns:
            dict | None: Đối tượng nhiệm vụ hoặc None.
        """
        return self.tasks.get(tid)

    def list_tasks(self, limit: int = 50) -> list[dict]:
        """Liệt kê danh sách các nhiệm vụ, sắp xếp theo thời gian tạo mới nhất lên trước.
        
        Args:
            limit (int, optional): Số lượng nhiệm vụ tối đa cần lấy (mặc định: 50).
            
        Returns:
            list[dict]: Danh sách nhiệm vụ.
        """
        items = sorted(self.tasks.values(),
                       key=lambda t: t.get("created_at") or 0, reverse=True)
        return items[:limit]

    def delete_task(self, tid: str) -> bool:
        """Xóa một nhiệm vụ khỏi bộ nhớ và file lưu trữ.
        
        Args:
            tid (str): ID nhiệm vụ cần xóa.
            
        Returns:
            bool: True nếu xóa thành công, False nếu không tìm thấy.
        """
        with _LOCK:
            if tid in self.tasks:
                del self.tasks[tid]
                _write(self.cfg.tasks_file, self.tasks)
                return True
            return False

    def clear_tasks(self, keep: int = 0) -> int:
        """Dọn dẹp hàng loạt các nhiệm vụ cũ, tùy chọn giữ lại N bản ghi mới nhất.
        
        Args:
            keep (int, optional): Số lượng bản ghi mới nhất muốn giữ lại (mặc định: 0 - xóa hết).
            
        Returns:
            int: Số lượng nhiệm vụ đã bị xóa khỏi hệ thống.
        """
        with _LOCK:
            items = sorted(self.tasks.values(),
                           key=lambda t: t.get("created_at") or 0, reverse=True)
            keep_ids = {t["id"] for t in items[:keep]}
            removed = len(self.tasks) - len(keep_ids)
            self.tasks = {k: v for k, v in self.tasks.items() if k in keep_ids}
            _write(self.cfg.tasks_file, self.tasks)
            return max(0, removed)
