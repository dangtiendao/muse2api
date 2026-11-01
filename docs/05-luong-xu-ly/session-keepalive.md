# Luồng Xử Lý: Tự Động Duy Trì Phiên & Đánh Thức VM (Keepalive)

---

## 1. Mô Tả Luồng Nghiệp Vụ

Nhằm giải quyết triệt để vấn đề cookie `hatch_vml` hết hạn sau 48 giờ và máy ảo muse.ai ngủ đông dẫn đến timeout khi có request người dùng, hệ thống triển khai một tiểu trình daemon chạy ngầm liên tục:
1. Chu kỳ lặp: Mỗi 10 đến 15 phút một lần.
2. Quét toàn bộ tài khoản đang được kích hoạt (`enabled=True`) trong `store.accounts`.
3. Gửi request HTTP GET tới `https://muse.ai/api/session` để gia hạn cookie.
4. Nếu trạng thái VM chưa đạt `RUNNING`, gửi request POST tới `https://muse.ai/api/hatch/vm/wake` để đánh thức.
5. Cập nhật cookie mới và mốc thời gian `last_keepalive` vào `store.py`.

---

## 2. Sơ Đồ Tuần Tự (Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    participant Daemon as Keepalive Daemon Thread
    participant Store as store.py
    participant Engine as engine.py (renew_session_http)
    participant MuseAPI as muse.ai /api/session
    participant MuseVM as muse.ai /api/hatch/vm/wake

    loop Mỗi 10-15 phút
        Daemon->>Store: list_accounts()
        Store-->>Daemon: Danh sách tài khoản cần duy trì
        
        loop Từng tài khoản (aid)
            Daemon->>Engine: renew_session_http(cookies, wake_vm=True)
            Engine->>MuseAPI: GET /api/session (kèm cookies hiện tại)
            
            alt HTTP 401 (Phiên bị thu hồi)
                MuseAPI-->>Engine: 401 Unauthorized
                Engine-->>Daemon: MuseAuthError
                Daemon->>Store: mark(aid, ok=False, note='Session expired')
            else HTTP 200 (Thành công)
                MuseAPI-->>Engine: Set-Cookie mới (hatch_vml +48h) + vm_id, vm_state
                
                opt vm_state != 'RUNNING' & wake_vm == True
                    Engine->>MuseVM: POST /api/hatch/vm/wake {vm_id}
                    MuseVM-->>Engine: HTTP 200 (Đã gửi tín hiệu đánh thức)
                    Engine->>MuseAPI: GET /api/session xác nhận vm_state == 'RUNNING'
                end
                
                Engine-->>Daemon: Trả về cookies mới, vm_id, vm_state, wake_ok
                Daemon->>Store: update_account(aid, cookies=new, cookies_exp=new)
                Daemon->>Store: touch_keepalive(aid, ok=True, note='VM: RUNNING')
            end
        end
    end
```

---

## 3. Liên kết Liên quan
- [Module Store Storage](../03-module/store-storage.md)
- [Module Engine Core](../03-module/engine-core.md)
- [Mục lục Tài liệu](../README.md)
