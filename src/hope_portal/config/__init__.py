import os
import tempfile

from smart_env import SmartEnv

DJANGO_HELP_BASE = "https://docs.djangoproject.com/en/5.2/ref/settings"


def setting(anchor: str) -> str:
    return f"@see {DJANGO_HELP_BASE}#{anchor}"


DEFAULTS = {
    "ADMIN_EMAIL": (str, "", "admin", True, "Initial user created at first deploy"),
    "ADMIN_PASSWORD": (str, "", "", True, "Password for initial user created at first deploy"),
    "ALLOWED_HOSTS": (list, [], ["127.0.0.1", "localhost"], True, setting("allowed-hosts")),
    "ANYMAIL_IGNORE_RECIPIENT_STATUS": (bool, False, True),
    "ANYMAIL_IGNORE_UNSUPPORTED_FEATURES": (bool, False, True),
    "ANYMAIL_REQUESTS_TIMEOUT": (int, 30, 30),
    "ANYMAIL_DEBUG_API_REQUESTS": (bool, False, True),
    "CELERY_BROKER_URL": (str, "redis://localhost:6379/2"),
    "CELERY_TASK_ALWAYS_EAGER": (bool, False),
    "CONSTANCE_DATABASE_CACHE_BACKEND": (str, ""),
    "CORS_ALLOWED_ORIGINS": (list, []),
    "CSP_REPORT_ONLY": (bool, False, True),
    "CSRF_COOKIE_NAME": (str, "hope_portal"),
    "CSRF_COOKIE_SECURE": (bool, True, False),
    "CSRF_TRUSTED_ORIGINS": (list, [], []),
    "DATABASE_URL": (str, "psql://postgres:@127.0.0.1:5432/hope_portal"),
    "DATABASE_HOPE_URL": (str, "psql://postgres:@127.0.0.1:5432/hope?options=-c%20default_transaction_read_only=on"),
    "DEBUG": (bool, False),
    "DEVELOPMENT": (bool, False),
    "EMAIL_BACKEND": (str, "django.core.mail.backends.smtp.EmailBackend"),
    "EMAIL_DEFAULT_SENDER": (str, "hope+noreply@unicef.org", "hope+noreply@unicef.org", False, ""),
    "EMAIL_HOST": (str, ""),
    "EMAIL_HOST_PASSWORD": (str, ""),
    "EMAIL_HOST_USER": (str, ""),
    "EMAIL_PORT": (int, ""),
    "EMAIL_USE_TLS": (bool, True),
    "ENVIRONMENT": (str, "production", "develop", False, "Environment"),
    "EXTRA_APPS": (list, "", "", False, ""),  # nosec
    "EXTRA_AUTHENTICATION_BACKENDS": (list, [], [], False, "Extra authentications backends enabled to add."),
    "EXTRA_MIDDLEWARES": (list, "", "", False, ""),  # nosec
    "FILE_STORAGE_DEFAULT": (str, "django.core.files.storage.FileSystemStorage", setting("storages")),
    "FILE_STORAGE_HOPE": (str, "django.core.files.storage.FileSystemStorage", setting("storages")),
    "FILE_STORAGE_MEDIA": (str, "django.core.files.storage.FileSystemStorage", setting("storages")),
    "FILE_STORAGE_STATIC": (str, "django.contrib.staticfiles.storage.StaticFilesStorage", setting("storages")),
    "GDAL_LIBRARY_PATH": (str, None),
    "GEOS_LIBRARY_PATH": (str, None),
    "LOGGING_LEVEL": (str, "CRITICAL", "DEBUG", False, setting("logging-level")),
    "LOGIN_LOCAL": (bool, True),
    "LOGIN_SSO": (bool, True),
    "MAILJET_API_URL": (str, "https://api.mailjet.com/v3.1/", "https://api.mailjet.com/v3.1/", False, "Mailjet API"),
    "MAILJET_API_KEY": (str, "", "", False, "Mailjet API key"),
    "MAILJET_SECRET_KEY": (str, "", "", False, "Mailjet API secret key"),
    "MEDIA_ROOT": (str, os.path.join(tempfile.gettempdir(), "hope_portal", "media")),
    "OTP_VALIDITY_MINUTES": (int, 5, 5, False, ""),
    "REDIS_CACHE_URL": (str, "redis://localhost:6379/0"),
    "REDIS_LOCK_URL": (str, "redis://localhost:6379/1?backend=django_redis.cache.RedisCache"),
    "REDIS_TSDB_URL": (str, "redis://localhost:6379/2"),
    "SECRET_KEY": (str, ""),
    "SENTRY_DSN": (str, ""),
    "SESSION_COOKIE_SECURE": (bool, True, False, False, ""),
    "SENTRY_ENABLED": (bool, False),
    "STATIC_ROOT": (str, os.path.join(tempfile.gettempdir(), "hope_portal", "static")),
    "STREAMING_BROKER_URL": (str, "", ""),
    "SUPERUSERS": (
        list,
        [],
        [],
        False,
        """"list of emails/or usernames that will automatically granted superusers privileges
 ONLY the first time they are created. This is designed to be used in dev/qa environments deployed by CI,
 where database can be empty.
        """,
    ),
    "TIME_ZONE": (str, "UTC"),
    "TWILIO_ACCOUNT_SID": (str, "", "", False, "Twilio Account SID"),
    "TWILIO_AUTH_TOKEN": (str, "", "", False, "Twilio Account Token"),
    "TWILIO_FROM_NUMBER": (str, "", "", False, "Twilio Default Sender"),
    "URL_PREFIX": (str, ""),
}

env = SmartEnv(**DEFAULTS)
