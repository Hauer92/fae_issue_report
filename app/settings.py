import os
from whitenoise.storage import CompressedManifestStaticFilesStorage
from pathlib import Path

# --- Base paths ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Security & debug ---
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret")
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

# --- Feature toggles (避免未安裝套件導致爆錯) ---
API_ENABLED = os.environ.get("API_ENABLED", "false").lower() == "true"
OIDC_ENABLED = os.environ.get("OIDC_ENABLED", "false").lower() == "true"
WHITENOISE_ENABLED = os.environ.get("WHITENOISE_ENABLED", "true").lower() == "true"  # 可用環境變數關閉

# --- Installed apps ---
INSTALLED_APPS = [
    # Django built-ins
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    # Your apps
    "core.apps.CoreConfig",
    "issues",
]

if API_ENABLED:
    INSTALLED_APPS += ["rest_framework"]

if OIDC_ENABLED:
    INSTALLED_APPS += ["mozilla_django_oidc"]

# --- Middleware ---
MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.security.SecurityMiddleware",
]

# WhiteNoise（簡單服務 static；正式可加壓縮/版本化 storage）
if WHITENOISE_ENABLED:
    MIDDLEWARE += ["whitenoise.middleware.WhiteNoiseMiddleware"]

MIDDLEWARE += [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

# 可選：提供更佳的壓縮與雜湊版本管理（正式環境）
# 僅在啟用 WhiteNoise 時設定，避免未安裝套件時爆錯
if WHITENOISE_ENABLED and os.environ.get("WHITENOISE_MANIFEST", "false").lower() == "true":
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- URL / WSGI ---
ROOT_URLCONF = "app.urls"
WSGI_APPLICATION = "app.wsgi.application"

# --- Database ---
# 優先使用 DATABASE_URL；若未安裝 dj_database_url 則安全回退到 SQLite
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    try:
        import dj_database_url
        DATABASES = {
            "default": dj_database_url.parse(DATABASE_URL)
        }
    except Exception:
        # 回退：簡易解析常見 Postgres/SQLite URL；若不識別則用 SQLite
        if DATABASE_URL.startswith("sqlite:///"):
            DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": DATABASE_URL.replace("sqlite:///", ""),
                }
            }
        else:
            # 回退到 SQLite（避免因套件缺失而無法啟動）
            DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": BASE_DIR / "db.sqlite3",
                }
            }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# --- i18n / tz ---
LANGUAGE_CODE = "zh-hant"
TIME_ZONE = os.environ.get("TIME_ZONE", "Asia/Taipei")
USE_I18N = True
USE_L10N = True
USE_TZ = True
DEFAULT_CHARSET = 'utf-8'

# --- Static & media ---
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"  # 對應 compose 的 static_volume 掛載點

MEDIA_URL = "/media/"
MEDIA_ROOT = "/app/media"

# --- Templates（Django Admin 必備 DjangoTemplates 引擎）---
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # 原本是 [BASE_DIR / "app" / "templates"]
        # 改成同時包含專案根的 templates 目錄
        "DIRS": [BASE_DIR / "templates", BASE_DIR / "app" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# --- REST Framework（僅在 API_ENABLED 時生效）---
if API_ENABLED:
    DEFAULT_AUTH_CLASSES = [
        "rest_framework.authentication.SessionAuthentication",
    ]
    if OIDC_ENABLED:
        DEFAULT_AUTH_CLASSES.insert(
            0, "mozilla_django_oidc.contrib.drf.OIDCAuthentication"
        )

    REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": DEFAULT_AUTH_CLASSES,
        "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    }

# --- OIDC（僅在 OIDC_ENABLED 時會被用到）---
TENANT = os.environ.get("OIDC_TENANT_ID", "")
OIDC_BASE = f"https://login.microsoftonline.com/{TENANT}/v2.0" if TENANT else ""
OIDC_RP_CLIENT_ID = os.environ.get("OIDC_CLIENT_ID", "")
OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_CLIENT_SECRET", "")
OIDC_OP_AUTHORIZATION_ENDPOINT = f"{OIDC_BASE}/oauth2/v2.0/authorize" if OIDC_BASE else ""
OIDC_OP_TOKEN_ENDPOINT = f"{OIDC_BASE}/oauth2/v2.0/token" if OIDC_BASE else ""
OIDC_OP_USER_ENDPOINT = f"{OIDC_BASE}/openid/userinfo" if OIDC_BASE else ""
OIDC_RP_SCOPES = "openid profile email offline_access"

LOGIN_URL = "/oidc/authenticate/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]
if OIDC_ENABLED:
    AUTHENTICATION_BACKENDS += ["mozilla_django_oidc.auth.OIDCAuthenticationBackend"]

# --- Redis / Celery ---
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TIMEZONE = TIME_ZONE

# --- App base URL & Microsoft Graph ---
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8080")
GRAPH = {
    "TENANT_ID": os.environ.get("GRAPH_TENANT_ID", ""),
    "CLIENT_ID": os.environ.get("GRAPH_CLIENT_ID", ""),
    "CLIENT_SECRET": os.environ.get("GRAPH_CLIENT_SECRET", ""),
    "TEAM_ID": os.environ.get("TEAMS_TEAM_ID", ""),
    "CHANNEL_ID": os.environ.get("TEAMS_CHANNEL_ID", ""),
}
# --- WhiteNoise: ensure compressed static storage (.br/.gz on collectstatic) ---
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
try:
    STORAGES
except NameError:
    STORAGES = {}
STORAGES["staticfiles"] = {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}

# --- enforced by script: WhiteNoise order ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

# --- enforced for Django admin ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
