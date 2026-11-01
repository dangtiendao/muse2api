# Luồng Xử Lý: Đồng Bộ & Nhập Cookie Tài Khoản

---

## 1. Mô Tả Luồng Nghiệp Vụ

Để đưa một tài khoản muse.ai vào hệ thống muse2api, người dùng có 3 phương pháp nhập:
1. **Qua Chrome Extension**: Nhấn vào biểu tượng extension trên trình duyệt Chrome đã đăng nhập muse.ai $\rightarrow$ Extension tự đọc `chrome.cookies` $\rightarrow$ POST về `/admin/accounts`.
2. **Qua Userscript Tampermonkey**: Mở trang web `https://muse.ai/` $\rightarrow$ Nhấn vào nút tròn nổi ⚡ $\rightarrow$ Nhấn "Đẩy vào hồ chứa".
3. **Qua CLI Helper (`get_muse_cookie.py`)**: Chạy script dòng lệnh, script tự mở Chrome và bắt cookie qua CDP.

Cả 3 phương thức cuối cùng đều gọi về endpoint `/admin/accounts` của muse2api để xử lý bóc tách và lưu trữ.

---

## 2. Sơ Đồ Tuần Tự (Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng
    participant Source as Extension / Userscript / CLI
    participant AdminAPI as app.py (/admin/accounts)
    participant Parser as app.parse_cookie_text
    participant Engine as engine.py (renew_session_http)
    participant Store as store.py (accounts.json)

    User->>Source: Kích hoạt xuất cookie
    Source->>Source: Lấy danh sách cookie của tên miền muse.ai
    Source->>AdminAPI: POST /admin/accounts {label, cookies, expires}
    
    AdminAPI->>AdminAPI: Xác thực API Key
    AdminAPI->>Parser: Phân tích cú pháp chuỗi cookie hoặc dict
    
    AdminAPI->>AdminAPI: Kiểm tra 2 cookie thiết yếu (hatch_sess, hatch_vml)
    alt Thiếu cookie cốt lõi
        AdminAPI-->>Source: HTTP 400 (Thiếu hatch_sess hoặc hatch_vml)
    else Đủ cookie
        AdminAPI->>Engine: renew_session_http(cookies, wake_vm=True)
        alt Session hợp lệ và gia hạn thành công
            Engine-->>AdminAPI: Cập nhật Set-Cookie mới nhất từ muse.ai
            AdminAPI->>Store: add_account(cookies, label, expires_at)
            Store-->>AdminAPI: Bản ghi tài khoản mới (ID: acc_xxx)
            AdminAPI-->>Source: HTTP 200 {"ok": true, "added": [...]}
            Source-->>User: Hiển thị thông báo thành công (Toast / Log)
        else Session không hợp lệ (401)
            AdminAPI-->>Source: HTTP 400 (Phiên đăng nhập không tồn tại hoặc đã chết)
        end
    end
```

---

## 3. Liên kết Liên quan
- [Module Chrome Extension](../03-module/chrome-extension.md)
- [Module Tools Helpers](../03-module/tools-helpers.md)
- [Chi Tiết API Admin](../06-api/admin-management-api.md)
- [Mục lục Tài liệu](../README.md)
