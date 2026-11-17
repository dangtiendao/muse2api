#!/usr/bin/env python3
"""Hòm thư tạm thời Mail.tm: Đăng ký địa chỉ + Lắng nghe lấy mã xác thực OTP (Mail.tm Disposable Email & OTP Poller).

Mục đích:
  Hỗ trợ quy trình tạo hoặc đăng nhập tài khoản muse.ai khi có yêu cầu nhập mã xác thực OTP qua email.
  Script tự động đăng ký một hòm thư tạm thời trên Mail.tm, hiển thị địa chỉ để điền vào muse.ai,
  sau đó chạy vòng lặp polling kiểm tra hòm thư đến và trích xuất mã số xác thực (4-8 số).

Đặc điểm:
  Hoàn toàn không có phụ thuộc bên ngoài (chỉ sử dụng thư viện chuẩn của Python).

Cách sử dụng:
  python3 tools/mailtm_otp.py                          # Tạo email mới và bắt đầu lắng nghe OTP
  python3 tools/mailtm_otp.py --addr a@b.c --pass xxx  # Tái sử dụng địa chỉ và mật khẩu cũ
  python3 tools/mailtm_otp.py --timeout 600            # Thời gian timeout chờ (giây), mặc định 900s
"""
import argparse, json, random, re, string, sys, time, urllib.request, urllib.error

API = "https://api.mail.tm"


def req(path, method="GET", token=None, body=None):
    """Gửi yêu cầu HTTP tới Mail.tm REST API và giải mã dữ liệu JSON trả về.
    
    Args:
        path (str): Endpoint API (ví dụ: '/accounts', '/token', '/messages').
        method (str, optional): Phương thức HTTP ('GET', 'POST', ...). Mặc định là 'GET'.
        token (str | None, optional): Bearer JWT token dùng để xác thực quyền truy cập.
        body (dict | None, optional): Payload dữ liệu gửi kèm ở dạng JSON.
        
    Returns:
        dict | list: Dữ liệu JSON phản hồi từ máy chủ.
        
    Raises:
        SystemExit: Thoát chương trình nếu máy chủ trả về mã lỗi HTTP.
    """
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    r.add_header("Accept", "application/json")
    if token:
        r.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:300]
        raise SystemExit(f"[!] {method} {path} -> HTTP {e.code}: {detail}")


def new_account():
    """Tạo mới một tài khoản hòm thư ngẫu nhiên trên Mail.tm.
    
    Returns:
        tuple[str, str, str]: Bộ ba gồm (địa chỉ email, mật khẩu tạo tự động, token JWT).
    """
    d = req("/domains")
    domains = d["hydra:member"] if isinstance(d, dict) else d  # Hỗ trợ cả định dạng mảng mới và hydra wrapper cũ
    domain = next(x["domain"] for x in domains if x.get("isActive", True))
    user = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
    addr, pwd = f"{user}@{domain}", "".join(random.choices(string.ascii_letters + string.digits, k=16))
    req("/accounts", "POST", body={"address": addr, "password": pwd})
    token = req("/token", "POST", body={"address": addr, "password": pwd})["token"]
    return addr, pwd, token


def login(addr, pwd):
    """Đăng nhập vào hòm thư Mail.tm đã có sẵn để lấy token xác thực mới.
    
    Args:
        addr (str): Địa chỉ email.
        pwd (str): Mật khẩu tài khoản.
        
    Returns:
        str: Chuỗi JWT token xác thực.
    """
    return req("/token", "POST", body={"address": addr, "password": pwd})["token"]


# Biểu thức chính quy phát hiện dãy 4 đến 8 chữ số độc lập (mã xác nhận OTP)
CODE_RE = re.compile(r"(?<!\d)(\d{4,8})(?!\d)")


def poll(token, timeout):
    """Vòng lặp định kỳ truy vấn danh sách thư mới, trích xuất và hiển thị mã OTP.
    
    Args:
        token (str): JWT token xác thực tài khoản email.
        timeout (int): Thời gian chờ tối đa (tính theo giây).
        
    Returns:
        str | None: Mã OTP phát hiện được hoặc None nếu hết thời gian chờ mà không có thư.
    """
    seen, deadline = set(), time.time() + timeout
    print(f"[*] Đang lắng nghe hộp thư đến (tối đa {timeout}s, nhấn Ctrl-C để dừng)...\n")
    while time.time() < deadline:
        try:
            r = req("/messages?page=1", token=token)
            msgs = r["hydra:member"] if isinstance(r, dict) else r
        except SystemExit:
            time.sleep(3); continue
        for m in msgs:
            if m["id"] in seen:
                continue
            seen.add(m["id"])
            full = req(f"/messages/{m['id']}", token=token)
            frm = (full.get("from") or {}).get("address", "?")
            subj = full.get("subject", "")
            body = full.get("text") or full.get("intro") or ""
            print(f"[+] Thư mới từ {frm}\n    Chủ đề: {subj}")
            codes = CODE_RE.findall(f"{subj}\n{body}")
            print(f"    Nội dung: {body.strip()[:500]}")
            if codes:
                print(f"\n>>> Mã xác thực OTP: {codes[0]}\n")
                return codes[0]
            print("    (Chưa tìm thấy mã OTP phù hợp, tiếp tục chờ...)\n")
        left = int(deadline - time.time())
        print(f"    Đang chờ thư mới... Còn lại {left}s", end="\r", flush=True)
        time.sleep(3)
    print("\n[!] Hết thời gian chờ, không nhận được mã xác thực.")
    return None


def main():
    """Hàm thực thi chính khi gọi script từ Command Line Interface (CLI)."""
    ap = argparse.ArgumentParser(description="Tự động lấy mã OTP đăng nhập muse.ai từ mail.tm")
    ap.add_argument("--addr", help="Tái sử dụng địa chỉ email đã có")
    ap.add_argument("--pass", dest="pwd", help="Mật khẩu của email đã có")
    ap.add_argument("--timeout", type=int, default=900, help="Thời gian chờ tối đa (giây)")
    a = ap.parse_args()
    if a.addr and a.pwd:
        addr, pwd, token = a.addr, a.pwd, login(a.addr, a.pwd)
        print(f"[*] Tái sử dụng hòm thư đã có: {addr}")
    else:
        addr, pwd, token = new_account()
        print(f"[*] Đã đăng ký hòm thư tạm mới: {addr}\n    Mật khẩu: {pwd} (lưu lại nếu muốn dùng tiếp)")
    print(f"\n=== Sao chép địa chỉ sau điền vào trang đăng nhập muse.ai ===\n    {addr}\n")
    code = poll(token, a.timeout)
    sys.exit(0 if code else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Đã dừng chương trình.")
