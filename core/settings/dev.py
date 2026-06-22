from .base import *  # noqa: F403

DEBUG = os.environ.get("DEBUG", "True") == "True"  # noqa: F405

SECRET_KEY = os.environ.get(  # noqa: F405
    "SECRET_KEY",
    "django-insecure-dev-only-change-me",
)

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
