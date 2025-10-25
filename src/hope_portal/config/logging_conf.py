import os

level = os.environ.get("LOG_LEVEL", "ERROR").upper()

LOGGING = {
    "default_level": "INFO",
    "version": 1,
    "disable_existing_loggers": True,
    "root": {
        "level": "WARNING",
        "handlers": ["sentry"],
    },
    "formatters": {
        "verbose": {"format": "%(levelname)s %(asctime)s %(name)s %(lineno)d %(message)s"},
        "short": {"format": "%(levelname)-10s %(name)s :%(lineno)d %(message)s"},
    },
    "handlers": {
        "sentry": {
            "level": "INFO",  # To capture more than ERROR, change to WARNING, INFO, etc.
            "class": "logging.NullHandler",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "null": {
            "class": "logging.NullHandler",
            "formatter": "short",
        },
        "db": {
            "level": "ERROR",
            "class": "django_db_logging.handlers.AsyncDBHandler",
        },
    },
    "loggers": {
        "django": {
            "level": level,
            "handlers": ["console"],
            "propagate": False,
        },
        "gunicorn": {
            "level": level,
            "handlers": ["console"],
            "propagate": False,
        },
        "celery": {
            "level": level,
            "handlers": ["console", "sentry"],
            "propagate": False,
        },
        "django.template": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": False,
        },
        "social_django": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
        "hope_portal": {
            "level": level,
            "handlers": ["console", "sentry"],
            "propagate": False,
        },
    },
}
