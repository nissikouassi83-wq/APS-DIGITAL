import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured("Définissez la variable d’environnement DJANGO_SECRET_KEY.")

DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "::1", "aps-taupe-eight.vercel.app"] + [
    host
    for host in (
        os.environ.get("VERCEL_URL"),
        os.environ.get("VERCEL_PROJECT_PRODUCTION_URL"),
    )
    if host
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=0,
            ssl_require=bool(os.environ.get("VERCEL")),
        )
    }
elif os.environ.get("VERCEL"):
    raise ImproperlyConfigured(
        "Configurez DATABASE_URL avec une base PostgreSQL persistante sur Vercel."
    )
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "index"
LOGOUT_REDIRECT_URL = "login"
SESSION_COOKIE_SECURE = bool(os.environ.get("VERCEL"))
CSRF_COOKIE_SECURE = bool(os.environ.get("VERCEL"))
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = [
    f"https://{host}"
    for host in (
        os.environ.get("VERCEL_URL"),
        os.environ.get("VERCEL_PROJECT_PRODUCTION_URL"),
    )
    if host
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Abidjan"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Dossier où l'on dépose les rapports hebdo .pptx
PPTX_DIR = BASE_DIR / "data" / "pptx"
