FROM python:3.11-slim-bookworm

# Môi trường cơ sở và cài đặt Chromium
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    MUSE2API_HOME=/app \
    MUSE2API_HOST=0.0.0.0 \
    MUSE2API_PORT=18610 \
    MUSE2API_CHROMIUM=/usr/bin/chromium \
    MUSE2API_CDP_PORT=19210

WORKDIR /app

# Cài đặt Chromium, phông chữ và các thư viện phụ thuộc cốt lõi
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    fonts-wqy-zenhei \
    fonts-freefont-ttf \
    procps \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn và các thư mục cần thiết
COPY admin.html app.py cdp.py config.py engine.py store.py version.json ./
COPY deploy/ ./deploy/
COPY extension/ ./extension/
COPY tools/ ./tools/

# Tạo thư mục dữ liệu bền vững (persistence)
RUN mkdir -p /app/data/media /app/data/downloads /root/muse2api-profiles

VOLUME ["/app/data"]

EXPOSE 18610

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "18610"]
