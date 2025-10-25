from typing import Any

from .. import env
from .mail import MAILJET_API_KEY, MAILJET_SECRET_KEY

CONSTANCE_ADDITIONAL_FIELDS = {
    "write_only_input": [
        "django.forms.fields.CharField",
        {
            "required": False,
            "widget": "hope_portal.utils.constance.WriteOnlyInput",
        },
    ],
    "group_select": [
        "hope_portal.utils.constance.GroupSelect",
        {"initial": None},
    ],
}

CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_DATABASE_CACHE_BACKEND = env("CONSTANCE_DATABASE_CACHE_BACKEND")
CONSTANCE_CONFIG: dict[str, tuple[Any, str, Any]] = {
    "NEW_USER_DEFAULT_GROUP": (None, "Group to assign to any new user", "group_select"),
    "LOGIN_LOCAL": (True, "Enable local accounts login", bool),
    "LOGIN_SSO": (True, "Enable SSO logon", bool),
    "MAILJET_API_KEY": (MAILJET_API_KEY, "Mailjet API key", str),
    "MAILJET_SECRET_KEY": (MAILJET_SECRET_KEY, "Mailjet secret key", "write_only_input"),
}
