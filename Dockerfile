# Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=120

# 基礎工具（無需 build-essential，因為用 wheels）
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1) 先複製需求檔（很重要）
COPY requirements.txt /app/requirements.txt

# 2) 再複製離線 wheel 倉
COPY wheelhouse/ /app/wheelhouse/

# 3) 完全離線安裝（不連網）
# RUN python -m pip install --upgrade pip \
RUN pip install --no-cache-dir --no-index \
        --find-links=/app/wheelhouse \
        -r /app/requirements.txt

# 4) 最後才複製專案，避免程式改動導致重跑安裝
COPY . /app

# 啟動命令
CMD ["gunicorn", "app.wsgi:application", "--bind", "0.0.0.0:8000"]
