import os

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False

SECRET_KEY = os.environ.get("SECRET_KEY")  # noqa: F405
if not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY environment variable is required in production.")

_allowed = os.environ.get("ALLOWED_HOSTS", "")  # noqa: F405
ALLOWED_HOSTS = [host.strip() for host in _allowed.split(",") if host.strip()]
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS environment variable is required in production.")

_csrf_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")  # noqa: F405
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in _csrf_origins.split(",") if origin.strip()]

SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True") == "True"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = os.environ.get("SECURE_HSTS_PRELOAD", "False") == "True"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

MIDDLEWARE = list(MIDDLEWARE)  # noqa: F405
if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

_database_url = os.environ.get("DATABASE_URL")
if _database_url:
    DATABASES = {  # noqa: F811
        "default": dj_database_url.parse(
            _database_url,
            conn_max_age=600,
            ssl_require=os.environ.get("DATABASE_SSL_REQUIRE", "True") == "True",
        )
    }

USE_S3_STORAGE = os.environ.get("USE_S3_STORAGE", "False") == "True"
if USE_S3_STORAGE:
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "")
    AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "us-east-1")
    if not AWS_STORAGE_BUCKET_NAME:
        raise ImproperlyConfigured(
            "AWS_STORAGE_BUCKET_NAME is required when USE_S3_STORAGE=True."
        )
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = True
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "format": (
                '{"level":"%(levelname)s","logger":"%(name)s",'
                '"message":"%(message)s"}'
            ),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "structured",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "itinerary.services.llm": {"level": "WARNING", "propagate": True},
        "itinerary.views": {"level": "INFO", "propagate": True},
        "itinerary.api": {"level": "INFO", "propagate": True},
    },
}
