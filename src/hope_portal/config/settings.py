import logging
from pathlib import Path

from . import env, logging_conf  # noqa

logger = logging.getLogger(__name__)

PACKAGE_DIR = Path(__file__).parent.parent  # hope_portal/
SOURCE_DIR = PACKAGE_DIR.parent  # src/
PROJECT_DIR = SOURCE_DIR.parent
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = [
    # Default apps:
    "hope_portal.apps.Config",
    "hope_portal.api",
    "hope_portal.ui.theme",
    "hope_portal.ui",
    "hope_portal.modules.hope.apps.Config",
    "hope_portal.modules.security",
    "unicef_security",
    "unfold",  # before django.contrib.admin
    "unfold.contrib.filters",  # optional, if special filters are needed
    "unfold.contrib.forms",  # optional, if special form elements are needed
    "unfold.contrib.inlines",  # optional, if special inlines are needed
    "unfold.contrib.import_export",  # optional, if django-import-export package is used
    "unfold.contrib.guardian",  # optional, if django-guardian package is used
    "unfold.contrib.simple_history",  # optional, if django-simple-history package is used
    "unfold.contrib.location_field",  # optional, if django-location-field package is used
    "unfold.contrib.constance",  # optional, if django-constance package is used
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.forms",
    # security
    "csp",
    "corsheaders",
    # REST Api
    "rest_framework",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    # Useful template tags:
    "django.contrib.humanize",
    # Useful libraries and add-ons
    "constance",
    "constance.backends.database",
    "flags",
    "smart_env",
    "debug_toolbar",
    "django_regex",
    "admin_extra_buttons",
    "adminfilters",
    "adminactions",
    "social_django",
    "tailwind",
    "issues",
    *env("EXTRA_APPS"),
]

DATE_INPUT_FORMATS = [
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%m/%d/%y",  # '2006-10-25', '10/25/2006', '10/25/06'
    "%b %d %Y",
    "%b %d, %Y",  # 'Oct 25 2006', 'Oct 25, 2006'
    "%d %b %Y",
    "%d %b, %Y",  # '25 Oct 2006', '25 Oct, 2006'
    "%B %d %Y",
    "%B %d, %Y",  # 'October 25 2006', 'October 25, 2006'
    "%d %B %Y",
    "%d %B, %Y",  # '25 October 2006', '25 October, 2006'
]
DATETIME_FORMAT = "%b, %d %Y %H:%M"
DATE_FORMAT = "%Y-%m-%d"  # or "%b, %d %Y"

DATETIME_INPUT_FORMATS = [
    "%Y-%m-%d %H:%M",  # '2006-10-25 14:30'
    "%Y/%m/%d %H:%M",  # '2006/10/25 14:30'
    "%d %b %Y %H:%M",  # '25 Oct 2006 14:30'
    "%Y %b %d %H:%M",  # '2006 Oct 25 14:30'
    "%Y-%m-%d %H:%M:%S",  # "2006-10-25 14:30:59"
    "%Y-%m-%d %H:%M:%S.%f",  # "2006-10-25 14:30:59.000200"
    "%Y-%m-%d %H:%M",  # "2006-10-25 14:30"
    "%Y-%m-%d",  # "2006-10-25"
    "%m/%d/%Y %H:%M:%S",  # "10/25/2006 14:30:59"
    "%m/%d/%Y %H:%M:%S.%f",  # "10/25/2006 14:30:59.000200"
    "%m/%d/%Y %H:%M",  # "10/25/2006 14:30"
    "%m/%d/%Y",  # "10/25/2006"
    "%m/%d/%y %H:%M:%S",  # "10/25/06 14:30:59"
    "%m/%d/%y %H:%M:%S.%f",  # "10/25/06 14:30:59.000200"
    "%m/%d/%y %H:%M",  # "10/25/06 14:30"
    "%m/%d/%y",  # "10/25/06"
]

# MIDDLEWARE CONFIGURATION
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "hope_portal.modules.security.middleware.VisitorAttemptMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
    "hope_portal.middleware.ExceptionHandlerMiddleware",
    *env("EXTRA_MIDDLEWARES"),
]
SECRET_KEY = env("SECRET_KEY")

AUTH_USER_MODEL = "hope_portal.user"

AUTHENTICATION_BACKENDS = (
    "social_core.backends.azuread_tenant.AzureADTenantOAuth2",
    "django.contrib.auth.backends.ModelBackend",
    *env("EXTRA_AUTHENTICATION_BACKENDS"),
)

SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_NAME = "hope_portal_id"
SESSION_SERIALIZER = "django.contrib.sessions.serializers.JSONSerializer"
# DEBUG
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DEBUG", False)
DEVELOPMENT = env.bool("DEVELOPMENT", False)

# EMAIL CONFIGURATION
# ------------------------------------------------------------------------------
EMAIL_BACKEND = env("EMAIL_BACKEND")
EMAIL_SUBJECT_PREFIX = "[Hope Beneficiary Portal]"
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS")
EMAIL_HOST = env.str("EMAIL_HOST")
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD")
EMAIL_PORT = env("EMAIL_PORT")

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
# Uses django-environ to accept uri format
# See: https://django-environ.readthedocs.io/en/latest/#supported-types
DATABASES = {
    "default": env.db("DATABASE_URL"),
    "hope_ro": env.db("DATABASE_HOPE_URL"),
}

DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASE_ROUTERS = ("hope_portal.utils.dbrouters.DbRouter",)
DATABASE_APPS_MAPPING: dict[str, str] = {
    "hope_portal": "default",
    "hope": "hope_ro",
}

HOPE_API_BASE_URL = env("HOPE_API_BASE_URL")
HOPE_API_TOKEN = env("HOPE_API_TOKEN")
HOPE_API_TIMEOUT = env("HOPE_API_TIMEOUT")

# GENERAL CONFIGURATION
# ------------------------------------------------------------------------------
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = env("TIME_ZONE")

# See: https://docs.djangoproject.com/en/dev/ref/settings/#GUAguage-code
LANGUAGE_CODE = "en"
LANGUAGE_COOKIE_NAME = "language"
LANGUAGES = (
    ("es", "Español"),
    ("fr", "Français"),
    ("en", "English"),
    ("ar", "العربية"),
)

LOCALE_PATHS = (str(PACKAGE_DIR / "LOCALE"),)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True

SILENCED_SYSTEM_CHECKS = [
    "admin.E404",  # 'django.contrib.messages.context_processors.messages' must be enabled ...
    "admin.E409",
]
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        "DIRS": [
            str(PACKAGE_DIR / "ui/templates"),
        ],
        "OPTIONS": {
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-debug
            "debug": DEBUG,
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            "context_processors": [
                "constance.context_processors.config",
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
                "hope_portal.ui.context_processors.app",
                "hope_portal.ui.context_processors.theme",
            ],
        },
    },
]
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"


CSRF_COOKIE_NAME = env("CSRF_COOKIE_NAME")
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE")
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE")
SECURE_SSL_REDIRECT = False

# See: http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = "bootstrap4"
CRISPY_FAIL_SILENTLY = not env.bool("DEBUG", False)

# URL Configuration
# ------------------------------------------------------------------------------
ROOT_URLCONF = "hope_portal.config.urls"
URL_PREFIX = env("URL_PREFIX")
SETUP_URL = "/setup/"
USE_X_FORWARDED_HOST = True

# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = env.str("STATIC_ROOT")

# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = f"/{URL_PREFIX}static/"

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# MEDIA CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = env.str("MEDIA_ROOT")

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = f"/{URL_PREFIX}media/"

# See: https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = "hope_portal.config.wsgi.application"

# PASSWORD STORAGE SETTINGS
# ------------------------------------------------------------------------------
# See https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
PASSWORD_HASHERS = [
    # 'django.contrib.auth.hashers.Argon2PasswordHasher',
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.BCryptPasswordHasher",
]
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# PASSWORD VALIDATION
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
# ------------------------------------------------------------------------------

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

KEY_FUNCTION = "hope_portal.utils.cache.make_key"

CACHES = {
    "default": env.cache("REDIS_CACHE_URL"),
    "lock": env.cache("REDIS_LOCK_URL"),
}

TSDB_STORE = env("REDIS_TSDB_URL")
STORAGES = {
    "default": env.storage("FILE_STORAGE_DEFAULT"),
    "staticfiles": env.storage("FILE_STORAGE_STATIC"),
    "media": env.storage("FILE_STORAGE_MEDIA"),
    "hope": env.storage("FILE_STORAGE_HOPE"),
}

# Custom user app defaults
# Select the correct user model
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "ui:login"

# Location of root django.contrib.admin URL
ADMIN_URL = r"^admin/"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": env("LOGGING_LEVEL"),
            "propagate": False,
        }
    },
}
GDAL_LIBRARY_PATH = env("GDAL_LIBRARY_PATH")
GEOS_LIBRARY_PATH = env("GEOS_LIBRARY_PATH")

from .fragments import *  # noqa
