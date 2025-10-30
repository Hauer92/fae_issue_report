#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/srv/issue_server"
MEDIA_DIR="/srv/issue_server/media"
BACKUP_DIR="/srv/issue_server/backups"
APP_BASE_URL="http://localhost:8080"

echo "=== 準備目錄 ==="
mkdir -p "$APP_DIR" "$MEDIA_DIR" "$BACKUP_DIR"
cd "$APP_DIR"

# 用 Python 一次寫出所有檔案（避免多重 EOF 出錯）
python3 - <<'PY'
import os, stat
from pathlib import Path

APP_DIR = Path("/srv/issue_server")
MEDIA_DIR = APP_DIR / "media"
BACKUP_DIR = APP_DIR / "backups"
APP_BASE_URL = "http://localhost:8080"

def w(path: Path, text: str, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    os.chmod(str(path), mode)

# requirements.txt
w(APP_DIR/"requirements.txt", """\
Django>=5.0
djangorestframework
psycopg[binary]
celery
redis
gunicorn
mozilla-django-oidc
python-dateutil
requests
""")

# Dockerfile
w(APP_DIR/"Dockerfile", """\
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV DJANGO_SETTINGS_MODULE=app.settings
""")

# docker-compose.yml（固定容器名稱）
w(APP_DIR/"docker-compose.yml", f"""\
version: "3.8"
services:
  db:
    image: postgres:16
    container_name: fae_db
    environment:
      POSTGRES_DB: ${{DB_NAME}}
      POSTGRES_USER: ${{DB_USER}}
      POSTGRES_PASSWORD: ${{DB_PASSWORD}}
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
      - {MEDIA_DIR}:/app/media
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
      - {MEDIA_DIR}:/app/media
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
""")

# .env（若不存在才建立，避免覆蓋你已填的機密）
env_path = APP_DIR/".env"
if not env_path.exists():
    import secrets, base64
    secret = base64.b64encode(os.urandom(32)).decode()
    w(env_path, f"""\
# --- Django ---
DJANGO_SECRET_KEY={secret}
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
APP_BASE_URL={APP_BASE_URL}

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
""")

# manage.py
w(APP_DIR/"manage.py", """\
#!/usr/bin/env python3
import os, sys
def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE','app.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
if __name__ == '__main__': main()
""", 0o755)

# app/*
w(APP_DIR/"app/__init__.py", "from .celery import app as celery_app\n__all__ = ('celery_app',)\n")
w(APP_DIR/"app/wsgi.py", """\
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE','app.settings')
application = get_wsgi_application()
""")
w(APP_DIR/"app/urls.py", """\
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("oidc/", include("mozilla_django_oidc.urls")),
    path("api/", include("core.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
""")
w(APP_DIR/"app/celery.py", """\
import os
from celery import Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE","app.settings")
app = Celery("app")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
""")
w(APP_DIR/"app/settings.py", """\
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
OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_CLIENT_SECRET","")
OIDC_OP_AUTHORIZATION_ENDPOINT = f"{OIDC_BASE}/oauth2/v2.0/authorize"
OIDC_OP_TOKEN_ENDPOINT = f"{OIDC_BASE}/oauth2/v2.0/token"
OIDC_OP_USER_ENDPOINT = f"{OIDC_BASE}/openid/userinfo"
OIDC_RP_SCOPES = "openid profile email offline_access"

LOGIN_URL = "/oidc/authenticate/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "mozilla_django_oidc.auth.OIDCAuthenticationBackend",
]

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TIMEZONE = TIME_ZONE

APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8080")
GRAPH = {
    "TENANT_ID": os.environ.get("GRAPH_TENANT_ID",""),
    "CLIENT_ID": os.environ.get("GRAPH_CLIENT_ID",""),
    "CLIENT_SECRET": os.environ.get("GRAPH_CLIENT_SECRET",""),
    "TEAM_ID": os.environ.get("TEAMS_TEAM_ID",""),
    "CHANNEL_ID": os.environ.get("TEAMS_CHANNEL_ID",""),
}
""")

# core/*
w(APP_DIR/"core/__init__.py", "")
w(APP_DIR/"core/apps.py", """\
from django.apps import AppConfig
class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    def ready(self):
        from . import signals  # noqa
""")
w(APP_DIR/"core/models.py", """\
from django.conf import settings
from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=200)
    customer = models.CharField(max_length=200, blank=True)
    def __str__(self): return self.name

class Asset(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    serial_no = models.CharField(max_length=120)
    location = models.CharField(max_length=200, blank=True)
    def __str__(self): return self.serial_no

class Issue(models.Model):
    class Priority(models.IntegerChoices):
        LOW=1,'Low'; NORMAL=2,'Normal'; HIGH=3,'High'; CRITICAL=4,'Critical'
    class Status(models.TextChoices):
        NEW='NEW','New'
        IN_PROGRESS='INP','In Progress'
        ON_SITE='ONS','On-site'
        WAITING_PARTS='WTP','Waiting Parts'
        TESTING='TST','Testing'
        CUSTOMER_CONFIRM='CCF','Customer Confirm'
        RESOLVED='RES','Resolved'
        CLOSED='CLO','Closed'

    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=300)
    description = models.TextField()
    priority = models.IntegerField(choices=Priority.choices, default=Priority.NORMAL)
    status = models.CharField(max_length=3, choices=Status.choices, default=Status.NEW)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='reported_issues')
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_issues')
    sla_due_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return f"#{self.id} {self.title}"

class Attachment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class IssueEvent(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='events')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=50)
    from_value = models.CharField(max_length=100, blank=True)
    to_value = models.CharField(max_length=100, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
""")
w(APP_DIR/"core/admin.py", """\
from django.contrib import admin
from .models import Project, Asset, Issue, Attachment, IssueEvent

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display=("id","name","customer")

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display=("id","serial_no","project","location")
    search_fields=("serial_no","location")

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display=("id","title","project","priority","status","assignee","created_at")
    list_filter=("status","priority","project")
    search_fields=("title","description")

admin.site.register(Attachment)
admin.site.register(IssueEvent)
""")
w(APP_DIR/"core/serializers.py", """\
from rest_framework import serializers
from .models import Issue, Attachment

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ["id","file","uploaded_by","uploaded_at"]
        read_only_fields = ["uploaded_by","uploaded_at"]

class IssueSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)
    reporter_name = serializers.SerializerMethodField()
    assignee_name = serializers.SerializerMethodField()

    class Meta:
        model = Issue
        fields = ["id","project","asset","title","description","priority","status",
                  "reporter","assignee","reporter_name","assignee_name","sla_due_at",
                  "attachments","created_at","updated_at"]
        read_only_fields = ["reporter","created_at","updated_at"]

    def get_reporter_name(self, obj): return obj.reporter.get_full_name() or obj.reporter.username
    def get_assignee_name(self, obj): return obj.assignee.get_full_name() if obj.assignee else None

    def create(self, validated_data):
        validated_data["reporter"] = self.context["request"].user
        return super().create(validated_data)
""")
w(APP_DIR/"core/views.py", """\
from rest_framework import viewsets, permissions
from .models import Issue, Attachment
from .serializers import IssueSerializer, AttachmentSerializer

class IsReporterOrManager(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if isinstance(obj, Issue):
            return obj.reporter_id == request.user.id or (obj.assignee_id == request.user.id)
        return False

class IssueViewSet(viewsets.ModelViewSet):
    queryset = Issue.objects.select_related("project","asset","reporter","assignee").all().order_by("-id")
    serializer_class = IssueSerializer
    permission_classes = [permissions.IsAuthenticated, IsReporterOrManager]

class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.select_related("issue","uploaded_by").all()
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsReporterOrManager]
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
""")
w(APP_DIR/"core/urls.py", """\
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IssueViewSet, AttachmentViewSet

router = DefaultRouter()
router.register(r'issues', IssueViewSet, basename='issue')
router.register(r'attachments', AttachmentViewSet, basename='attachment')
urlpatterns = [ path('', include(router.urls)) ]
""")
w(APP_DIR/"core/signals.py", """\
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Issue, IssueEvent
from .tasks import send_issue_update_to_teams

@receiver(post_save, sender=Issue)
def on_issue_save(sender, instance: Issue, created, **kwargs):
    action = 'created' if created else 'status_changed'
    IssueEvent.objects.create(
        issue=instance,
        actor=(instance.reporter if created else (instance.assignee or instance.reporter)),
        action=action,
        to_value=instance.status
    )
    send_issue_update_to_teams.delay(instance.id, action)
""")
w(APP_DIR/"core/tasks.py", """\
import os, requests
from celery import shared_task
GRAPH_BASE = "https://graph.microsoft.com/v1.0"

def get_graph_token() -> str:
    tenant = os.environ.get("GRAPH_TENANT_ID","")
    client_id = os.environ.get("GRAPH_CLIENT_ID","")
    client_secret = os.environ.get("GRAPH_CLIENT_SECRET","")
    if not (tenant and client_id and client_secret):
        return ""
    url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "https://graph.microsoft.com/.default",
    }
    r = requests.post(url, data=data, timeout=10)
    r.raise_for_status()
    return r.json().get("access_token","")

def post_channel_message(html_content: str):
    team_id = os.environ.get("TEAMS_TEAM_ID","")
    channel_id = os.environ.get("TEAMS_CHANNEL_ID","")
    token = get_graph_token()
    if not (team_id and channel_id and token):
        return
    url = f"{GRAPH_BASE}/teams/{team_id}/channels/{channel_id}/messages"
    payload = {"body": {"contentType": "html", "content": html_content}}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers, timeout=10)
    r.raise_for_status()

@shared_task
def send_issue_update_to_teams(issue_id: int, event: str):
    from .models import Issue
    issue = Issue.objects.get(id=issue_id)
    assignee = issue.assignee.get_full_name() if issue.assignee else "未指派"
    html = (
        f"<b>#{issue.id} {issue.title}</b><br/>"
        f"事件：{event}｜狀態：{issue.get_status_display()}｜優先度：{issue.get_priority_display()}<br/>"
        f"指派：{assignee}<br/>"
        f"{os.environ.get(查看</a>"
    )
    post_channel_message(html)
""")

# 備份腳本
w(APP_DIR/"backup.sh", """\
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="/srv/issue_server"
MEDIA_DIR="/srv/issue_server/media"
BACKUP_DIR="/srv/issue_server/backups"
DB_CONTAINER="fae_db"
DB_USER="$(grep -E '^DB_USER=' "$APP_DIR/.env" | cut -d'=' -f2)"
DB_NAME="$(grep -E '^DB_NAME=' "$APP_DIR/.env" | cut -d'=' -f2)"
TS=$(date +"%Y%m%d-%H%M%S")

mkdir -p "$BACKUP_DIR"

# 1) PostgreSQL 邏輯備份
docker exec -i "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/db-$TS.sql.gz"

# 2) 附件備份
tar -czf "$BACKUP_DIR/media-$TS.tar.gz" -C "$MEDIA_DIR" .

# 3) 保留策略：刪除 30 天前的檔案
find "$BACKUP_DIR" -type f -mtime +30 -delete

echo "Backup done @ $TS → $BACKUP_DIR"
""", 0o755)

# systemd 單位檔（備份）
w(Path("/etc/systemd/system/fae-issue-backup.service"), """\
[Unit]
Description=FAE Issue daily backup

[Service]
Type=oneshot
ExecStart=/srv/issue_server/backup.sh
""")
w(Path("/etc/systemd/system/fae-issue-backup.timer"), """\
[Unit]
Description=Run FAE Issue backup daily at 02:30

[Timer]
OnCalendar=*-*-* 02:30:00
Persistent=true
[Install]
WantedBy=timers.target
""")
PY
echo "=== 啟用備份排程 ==="
systemctl daemon-reload
systemctl enable --now fae-issue-backup.timer || true
systemctl list-timers | grep fae-issue-backup || true

echo "=== 建置並啟動容器 ==="
docker compose up -d --build

echo "=== 建立/套用遷移 ==="
docker compose exec web python manage.py makemigrations core
docker compose exec web python manage.py migrate

echo "=== 完成 ==="
echo "服務位址：${APP_BASE_URL}  或 http://<你的伺服器IP>:8080"
echo "附件目錄：$MEDIA_DIR"
echo "備份目錄：$BACKUP_DIR（每日 02:30 自動備份）"
echo "建立管理者帳號： docker compose exec web python manage.py createsuperuser"
