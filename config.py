"""muse2api 配置与环境变量管理模块 (Configuration & Environment Management).

Module này chịu trách nhiệm:
  - Tự động nạp cấu hình từ file `.env` tại thư mục gốc dự án.
  - Tự động phát hiện đường dẫn thực thi trình duyệt Chromium/Chrome/Edge trên nhiều hệ điều hành.
  - Quản lý tập trung các tham số runtime: cổng mạng, bảo mật API key, thư mục dữ liệu,
    thời gian timeout, giới hạn tài nguyên và các cờ tính năng (feature flags).
"""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field

_DEFAULT_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_dotenv():
    """Tự động tải file `.env` từ thư mục gốc dự án (không ghi đè các biến môi trường hệ thống đã tồn tại).
    
    Đọc từng dòng cấu hình định dạng KEY=VALUE, loại bỏ khoảng trắng và dấu ngoặc kép/đơn.
    """
    base = os.environ.get("MUSE2API_HOME") or _DEFAULT_BASE_DIR
    env_path = os.path.join(base, ".env")
    if not os.path.isfile(env_path):
        return
    try:
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#") or "=" not in s:
                    continue
                k, v = s.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v
    except OSError:
        pass


_load_dotenv()


def _env(key: str, default: str) -> str:
    """Helper lấy giá trị biến môi trường dạng chuỗi với giá trị fallback mặc định.
    
    Args:
        key (str): Tên biến môi trường cần truy xuất.
        default (str): Giá trị mặc định nếu biến không tồn tại.
        
    Returns:
        str: Giá trị biến môi trường hoặc fallback mặc định.
    """
    return os.environ.get(key, default)


def _detect_chromium() -> str:
    """Tự động phát hiện đường dẫn thực thi Chromium/Chrome/Edge trên hệ thống.
    
    Ưu tiên biến môi trường `MUSE2API_CHROMIUM`; nếu chưa đặt hoặc file không tồn tại,
    hàm sẽ duyệt danh sách các đường dẫn nhị phân phổ biến trên Linux, Windows và macOS.
    
    Returns:
        str: Đường dẫn file nhị phân hoặc tên lệnh trong PATH; fallback về 'chromium'.
    """
    configured = os.environ.get("MUSE2API_CHROMIUM", "").strip()
    if configured and (os.path.isfile(configured) or shutil.which(configured)):
        return configured
    candidates = [
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/snap/bin/chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "chromium",
        "chromium-browser",
        "google-chrome",
        "chrome",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for c in candidates:
        if os.path.isfile(c) or shutil.which(c):
            return c
    return configured or "chromium"


@dataclass
class Config:
    """Lớp lưu trữ toàn bộ cấu hình hệ thống của muse2api (Singleton Configuration DataClass).
    
    Chứa các nhóm thiết lập:
      - Máy chủ mạng: host, port, public_base, cors_origins.
      - Trình duyệt điều khiển: chromium, cdp_port, profile_root, site_url.
      - Bảo mật: api_key, ref_image_local_files, ref_image_private_fetch.
      - Quá trình sinh nội dung: timeouts, max_concurrency, tool_protocol.
    """
    base_dir: str = field(default_factory=lambda: _env("MUSE2API_HOME", _DEFAULT_BASE_DIR))
    host: str = field(default_factory=lambda: _env("MUSE2API_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(_env("MUSE2API_PORT", "18610")))

    # Cấu hình trình duyệt (Browser & CDP Settings)
    chromium: str = field(default_factory=_detect_chromium)
    cdp_port: int = field(default_factory=lambda: int(_env("MUSE2API_CDP_PORT", "19210")))
    home_dir: str = field(default_factory=lambda: _env("MUSE2API_HOME_DIR", os.path.expanduser("~")))
    extra_path: str = field(default_factory=lambda: _env("MUSE2API_EXTRA_PATH", "/snap/bin"))
    site_url: str = field(default_factory=lambda: _env("MUSE2API_SITE", "https://muse.ai/"))
    login_wait: int = field(default_factory=lambda: int(_env("MUSE2API_LOGIN_WAIT", "60")))

    # Thư mục gốc profile trình duyệt.
    # Lưu ý bảo mật & sandbox: Snap Chromium chịu ràng buộc AppArmor, chỉ được đọc/ghi thư mục dưới $HOME.
    # Nếu truyền --user-data-dir=/opt/... hoặc /tmp/... sẽ bị âm thầm chuyển về ~/snap/chromium/common/chromium.
    # Vì vậy profile_root bắt buộc phải nằm dưới $HOME (không dùng thư mục ẩn bắt đầu bằng dấu chấm).
    profile_root: str = field(
        default_factory=lambda: _env("MUSE2API_PROFILE_ROOT",
                                     os.path.join(os.path.expanduser("~"),
                                                  "muse2api-profiles")))

    # Xác thực bảo mật (Authentication)
    api_key: str = field(default_factory=lambda: _env("MUSE2API_KEY", ""))

    # Địa chỉ công khai bên ngoài (dùng hiển thị địa chỉ truy cập trên giao diện quản trị Admin)
    public_base: str = field(
        default_factory=lambda: _env("MUSE2API_PUBLIC_BASE", ""))

    # Các nguồn CORS cho phép gọi API import cookie từ trang web muse.ai
    cors_origins: str = field(
        default_factory=lambda: _env("MUSE2API_CORS_ORIGINS",
                                     "https://muse.ai,https://www.muse.ai"))

    # Thời gian timeout và giới hạn tác vụ sinh nội dung (Generation Timeouts & Limits)
    image_timeout: int = field(default_factory=lambda: int(_env("MUSE2API_IMAGE_TIMEOUT", "240")))
    video_timeout: int = field(default_factory=lambda: int(_env("MUSE2API_VIDEO_TIMEOUT", "600")))
    chat_timeout: int = field(default_factory=lambda: int(_env("MUSE2API_CHAT_TIMEOUT", "300")))
    max_concurrency: int = field(default_factory=lambda: max(1, int(_env("MUSE2API_CONCURRENCY", "2"))))

    # Chính sách an toàn ảnh tham chiếu (Reference Image Safety):
    # Mặc định chỉ cho phép cung cấp trực tiếp base64 hoặc URL Internet công khai.
    # Chỉ bật cờ này khi triển khai trong môi trường tin cậy một người dùng.
    ref_image_local_files: bool = field(
        default_factory=lambda: _env("MUSE2API_REF_IMAGE_LOCAL_FILES", "0").strip() == "1")
    ref_image_private_fetch: bool = field(
        default_factory=lambda: _env("MUSE2API_REF_IMAGE_PRIVATE_FETCH", "0").strip() == "1")

    # Cờ tương thích giao thức Function Calling (Tools Protocol) - Mặc định tắt (0).
    # Model muse.ai có thể từ chối xuất ra JSON giả lập gọi tool, việc inject prompt có thể làm nhiễu câu trả lời.
    tool_protocol: bool = field(
        default_factory=lambda: _env("MUSE2API_TOOL_PROTOCOL", "0").strip() != "0")

    # Cờ tự động giữ phiên (Keepalive) cho tài khoản đã vô hiệu hóa - Mặc định tắt (0).
    # Khi bật, các tài khoản bị tắt thủ công vẫn được daemon ngầm gia hạn session và đánh thức VM.
    keepalive_disabled_accounts: bool = field(
        default_factory=lambda: _env("MUSE2API_KEEPALIVE_DISABLED_ACCOUNTS", "0").strip() != "0")

    @property
    def data_dir(self) -> str:
        """Đường dẫn thư mục lưu trữ dữ liệu chính (data/)."""
        return os.path.join(self.base_dir, "data")

    @property
    def media_dir(self) -> str:
        """Đường dẫn thư mục lưu trữ tệp hình ảnh, video đã tạo (data/media/)."""
        return os.path.join(self.data_dir, "media")

    @property
    def download_dir(self) -> str:
        """Đường dẫn thư mục nhận file tải về từ trình duyệt CDP (data/downloads/)."""
        return os.path.join(self.data_dir, "downloads")

    @property
    def profile_dir(self) -> str:
        """Đường dẫn thư mục user data profile dành riêng cho Chromium."""
        return os.path.join(self.profile_root, "generate")

    @property
    def accounts_file(self) -> str:
        """Đường dẫn file JSON danh sách tài khoản (data/accounts.json)."""
        return os.path.join(self.data_dir, "accounts.json")

    @property
    def tasks_file(self) -> str:
        """Đường dẫn file JSON danh sách nhiệm vụ bất đồng bộ (data/tasks.json)."""
        return os.path.join(self.data_dir, "tasks.json")

    def ensure_dirs(self):
        """Khởi tạo toàn bộ các thư mục lưu trữ cần thiết nếu chưa tồn tại."""
        for d in (self.base_dir, self.data_dir, self.media_dir, self.download_dir,
                  self.profile_dir):
            os.makedirs(d, exist_ok=True)


CFG = Config()
