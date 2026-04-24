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
    "CACHE_QUESTIONS_TIMEOUT": (86400, "Questions cache time-to-live", int),
    "MAX_QUESTIONS": (20, "Max number if questions to ask to indentify beneficiart", int),
    "MAX_QUESTIONS_PER_FIELD": (2, "Max questions generated from a single field", int),
    "MIN_QUESTIONS": (8, "Min number if questions that must be available to make identification safe", int),
    "MAX_VISITOR_ATTEMPTS": (5, "Max number of attempts per user (cookie based, not really safe)", int),
    "MAX_REGISTRATION_ATTEMPTS": (5, "Max number of attempts per registration number", int),
    "MAX_REGISTRATION_LOCKOUT_HOURS": (
        24,
        "Number of hours to lock out a registration number after too many attempts",
        int,
    ),
}
