#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/srv/issue_server"
MEDIA_DIR="/srv/issue_server/media"
BACKUP_DIR="/srv/issue_server/backups"
APP_BASE_URL="http://localhost:8080"

echo "=== 準備目錄 ==="
sudo mkdir -p "$APP_DIR" "$MEDIA_DIR" "$BACKUP_DIR"
sudo chown -R "$(id -u)":"$(id -g)" "$APP_DIR" "$MEDIA_DIR" "$BACKUP_DIR"
cd "$APP_DIR"

# 若 docker 尚未安裝，提醒（不強制）
if ! command -v docker >/dev/null 2>&1; then
  echo "⚠️  系統找不到 docker，請先完成安裝再執行本腳本。"
  exit 1
fi

echo "=== 生成 requirements.txt ==="
cat > requirements.txt <<'EOF'
Django>=5.0
djangorestframework
psycopg[binary]
celery
redis
gunicorn
mozilla-django-oidc
python-dateutil
requests
EOF
echo "=== 生成 Dockerfile ==="
cat > Dockerfile <<'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV DJANGO_SETTINGS_MODULE=app.settings
EOF

echo "=== 生成 docker-compose.yml（固定容器名稱）==="
cat > docker-compose.yml <<EOF
version: "3.8"
services:
  db:
    image: postgres:16
    container_name: fae_db
    environment:
      POSTGRES_DB: \${DB_NAME}
      POSTGRES_USER: \${DB_USER}
      POSTGRES_PASSWORD: \${DB_PASSWORD}
    volumes:
      - db_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: fae_redis
    restart: unless-stopped

  web:
    build: .
    container_name: fae_web
    command: bash -c "python manage.py makemigrations core && python manage.py migrate && gunicorn app.wsgi:application --bind 0.0.0.0:8000 --workers 3"
    env_file: .env
    volumes:
      - .:/app
      - ${MEDIA_DIR}:/app/media
    ports:
      - "8080:8000"
    depends_on: [db, redis]
    restart: unless-stopped

  celery:
    build: .
    container_name: fae_celery
    command: celery -A app worker -l info
    env_file: .env
    volumes:
      - .:/app
      - ${MEDIA_DIR}:/app/media
    depends_on: [web, redis]
    restart: unless-stopped

  beat:
    build: .
    container_name: fae_beat
    command: celery -A app beat -l info
    env_file: .env
    depends_on: [web, redis]
    restart: unless-stopped

volumes:
  db_data:
EOF

echo "=== 生成 .env（如需 OIDC/Teams 請後續填）==="
if [ ! -f .env ]; then
  cat > .env <<EOF
# --- Django ---
DJANGO_SECRET_KEY=$(openssl rand -base64 32)
DJANGO_DEBUG=True
ALLOWED_HOSTS=*

# --- DB ---
DB_NAME=fae_issue
DB_USER=fae
DB_PASSWORD=fae_pass
DB_HOST=db
DB_PORT=5432

# --- Redis/Celery ---
REDIS_URL=redis://redis:6379/0
TIME_ZONE=Asia/Taipei

# --- App ---
APP_BASE_URL=${APP_BASE_URL}

# --- OIDC (Entra ID) ---
OIDC_TENANT_ID=
OIDC_CLIENT_ID=
OIDC_CLIENT_SECRET=

# --- Teams / Graph ---
GRAPH_TENANT_ID=
GRAPH_CLIENT_ID=
GRAPH_CLIENT_SECRET=
TEAMS_TEAM_ID=
TEAMS_CHANNEL_ID=
EOF
fi

echo "=== 產生 Django 專案骨架 ==="
mkdir -p app core app/templates
touch app/__init__.py core/__init__.py

cat > manage.py <<'EOF'
#!/usr/bin/env python3
import os, sys
def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE','app.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
if __name__ == '__main__': main()
EOF
chmod +x manage.py

cat > app/settings.py <<'EOF'
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret")
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin","django.contrib.auth","django.contrib.contenttypes",
    "django.contrib.sessions","django.contrib.messages","django.contrib.staticfiles",
    "rest_framework",
    "mozilla_django_oidc",
    "core.apps.CoreConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware","django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware","django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware","django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "app.urls"
WSGI_APPLICATION = "app.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST", "db"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

LANGUAGE_CODE = "zh-hant"
TIME_ZONE = os.environ.get("TIME_ZONE", "Asia/Taipei")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = "/app/media"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "mozilla_django_oidc.contrib.drf.OIDCAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}

TENANT = os.environ.get("OIDC_TENANT_ID","")
OIDC_BASE = f"https://login.microsoftonline.com/{TENANT}/v2.0" if TENANT else ""
OIDC_RP_CLIENT_ID = os.environ.get("OIDC_CLIENT_ID","")
OID
