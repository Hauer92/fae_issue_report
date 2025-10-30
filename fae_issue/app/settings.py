import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev")
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "rest_framework",
    "mozilla_django_oidc",
    "core",
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
``
