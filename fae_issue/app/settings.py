import os
from pathlib import Path
from dotenv import load_dotenv # <-- 新增：導入 load_dotenv

# ----------------------------------------------------------------------
# 核心修正：載入 .env 檔案
# ----------------------------------------------------------------------
# 這行會尋找並載入與 settings.py 所在目錄 (app/) 的父目錄 (專案根目錄)
# 中的 .env 檔案。
load_dotenv(Path(__file__).resolve().parent.parent / '.env') 
# ----------------------------------------------------------------------


BASE_DIR = Path(__file__).resolve().parent.parent

# 修正 DEBUG 和 SECRET_KEY 的讀取邏輯
# 確保 SECRET_KEY 讀取 DJANGO_SECRET_KEY
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev") 

# 讓 DEBUG 真正從環境變數讀取 True/False 字串
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True" 

# 由於你 .env 中的 ALLOWED_HOSTS=*，可以直接讀取
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", '*').split(',')

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "rest_framework",
    "mozilla_django_oidc",
    "core",
    "issues", # <-- 修正：新增 'issues' 應用程式
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
MEDIA_ROOT = "/app/media"  # 掛載到 NAS 的容器內路徑

# DRF 基本配置（可擴充認證/權限）
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "django.contrib.auth.backends.ModelBackend",  # 先允許本地帳密；OIDC 另行補上
        "mozilla_django_oidc.contrib.drf.OIDCAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}

# OIDC (Entra ID)
TENANT = os.environ.get("OIDC_TENANT_ID")
OIDC_BASE = f"https://login.microsoftonline.com/{TENANT}/v2.0" if TENANT else ""
OIDC_RP_CLIENT_ID = os.environ.get("OIDC_CLIENT_ID")
OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_CLIENT_SECRET")
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

# Celery
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TIMEZONE = TIME_ZONE

# App/Graph
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8080")
GRAPH = {
    "TENANT_ID": os.environ.get("GRAPH_TENANT_ID"),
    "CLIENT_ID": os.environ.get("GRAPH_CLIENT_ID"),
    "CLIENT_SECRET": os.environ.get("GRAPH_CLIENT_SECRET"),
    "TEAM_ID": os.environ.get("TEAMS_TEAM_ID"),
    "CHANNEL_ID": os.environ.get("TEAMS_CHANNEL_ID"),
}

# 確保 MEDIA_ROOT 在 Windows 環境下是 BASE_DIR 下的子目錄
# 由於你的專案結構暗示著 Docker/Linux 環境，但我們在 Windows 開發，
# 這裡建議使用一個更適合 Windows 路徑的 fallback，如果沒有設定 NAS_MEDIA_PATH 的話。
NAS_MEDIA_PATH = os.environ.get("NAS_MEDIA_PATH")
if not NAS_MEDIA_PATH and DEBUG:
    # 如果是 Windows 開發環境，預設使用專案內的 media_root 資料夾
    MEDIA_ROOT = BASE_DIR / "media_root"
    os.makedirs(MEDIA_ROOT, exist_ok=True)
elif NAS_MEDIA_PATH:
    # 如果有設定 NAS 路徑，則使用它 (可能是 Docker 環境)
    MEDIA_ROOT = NAS_MEDIA_PATH
# 否則保持原樣 "/app/media"


# 這是原本你設為固定 "True" 的地方，已經改為從環境變數讀取
# 確保我們之前解決 DEBUG=False 的問題時是正確的讀取方式。

# DEBUG = "True" <-- 移除
# ALLOWED_HOSTS = ['*'] <-- 這裡也從 os.environ.get 讀取了

# 補上 Django 推薦的預設設定
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
