# Hướng Dẫn Cài Đặt Chi Tiết MUSE2API

---

## 1. Phương Pháp 1: Triển Khai Nhanh Bằng Docker Compose (Khuyến nghị)

Phương pháp này là cách đơn giản và an toàn nhất, tự động đóng gói sẵn Chromium, phông chữ và Python môi trường cô lập.

### Bước 1: Sao chép mã nguồn về máy
```bash
git clone https://github.com/czg86389-hub/muse2api.git
cd muse2api
```

### Bước 2: Tạo và chỉnh sửa file cấu hình môi trường
```bash
cp .env.example .env
# Chỉnh sửa file .env bằng nano hoặc vim
nano .env
```
*Lưu ý: Bạn nên thiết lập `MUSE2API_KEY` thành một mật khẩu mạnh của riêng bạn.*

### Bước 3: Khởi chạy dịch vụ
```bash
docker compose up -d
```

### Bước 4: Kiểm tra trạng thái container
```bash
docker compose ps
docker compose logs -f
```
Khi thấy log xuất hiện: `Uvicorn running on http://0.0.0.0:18610`, dịch vụ đã sẵn sàng!

---

## 2. Phương Pháp 2: Cài Đặt Trực Tiếp Trên Máy Chủ Linux (Ubuntu / Debian)

### Bước 1: Cài đặt Chromium, phông chữ và Python
```bash
sudo apt-get update
sudo apt-get install -y chromium fonts-wqy-zenhei python3 python3-pip python3-venv git
```

### Bước 2: Thiết lập môi trường và tải mã nguồn
```bash
sudo mkdir -p /opt/muse2api
sudo chown -R $USER:$USER /opt/muse2api
cd /opt/muse2api

git clone https://github.com/czg86389-hub/muse2api.git .
```

### Bước 3: Tạo môi trường ảo (Virtualenv) và cài đặt dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Bước 4: Thiết lập file môi trường
```bash
cp .env.example .env
nano .env
```

### Bước 5: Chạy thử nghiệm
```bash
python app.py
```
Truy cập `http://<IP_SERVER>:18610/admin?key=<YOUR_KEY>` để kiểm tra giao diện quản trị.

---

## 3. Phương Pháp 3: Cài Đặt Trên Windows / macOS Cho Môi Trường Phát Triển

### Trên Windows:
1. Đảm bảo đã cài đặt [Python 3.10+](https://www.python.org/) và tích vào ô **"Add python.exe to PATH"**.
2. Đảm bảo máy tính đã cài Google Chrome hoặc Microsoft Edge.
3. Mở PowerShell trong thư mục dự án:
```powershell
# Tạo môi trường ảo
python -m venv venv
.\venv\Scripts\Activate.ps1

# Cài đặt thư viện
pip install -r requirements.txt

# Thiết lập file .env
Copy-Item .env.example .env

# Chạy server
python app.py
```

### Trên macOS:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 app.py
```

---

## 4. Thiết Lập Dịch Vụ Tự Chạy Cùng Hệ Thống (Systemd Trên Linux)

Để dịch vụ tự động khởi động cùng hệ điều hành và tự phục hồi khi crash, cấu hình systemd như sau:

1. Chỉnh sửa file `deploy/muse2api.service` sao cho đường dẫn phù hợp với thư mục của bạn.
2. Sao chép vào thư mục dịch vụ của hệ thống:
```bash
sudo cp deploy/muse2api.service /etc/systemd/system/muse2api.service
sudo systemctl daemon-reload
sudo systemctl enable muse2api
sudo systemctl start muse2api
sudo systemctl status muse2api
```

---

## 5. Liên kết Liên quan

- [Yêu Cầu Hệ Thống](yeu-cau-he-thong.md)
- [Cấu Hình Biến Môi Trường](cau-hinh.md)
- [Lệnh Chạy Dự Án](chay-du-an.md)
- [Mục lục Tài liệu](../README.md)
