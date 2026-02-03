from django.contrib.auth.models import AbstractBaseUser
from django.db import connections

from hope_portal.modules.hope.models import HopeUser


def _hope_conn_alias() -> str:
    # Prefer the read-only hope connection when configured, otherwise fall back to default.
    if "hope_ro" in connections.databases:
        return "hope_ro"
    return "default"


def retrieve_hope_user(user: AbstractBaseUser | None = None) -> HopeUser | None:
    if not user:
        return None

    hope_user = None
    qs = HopeUser.objects.using(_hope_conn_alias())

    if user.email:
        hope_user = qs.filter(email=user.email).first()

    if not hope_user and user.username:
        hope_user = qs.filter(username=user.username).first()

    return hope_user
