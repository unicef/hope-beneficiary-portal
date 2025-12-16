from typing import Any

from constance import config
from django.contrib.auth.models import Group, User
from social_core.backends.base import BaseAuth
from hope_portal.modules.hope.helpers import retrieve_hope_user


def save_to_group(backend: BaseAuth, user: User | None = None, **kwargs: Any) -> dict[str, Any]:
    if user and config.NEW_USER_DEFAULT_GROUP:
        grp = Group.objects.get(name=config.NEW_USER_DEFAULT_GROUP)
        user.groups.add(grp)
    return {}


def process_hope_user(backend: BaseAuth, user: User | None = None, **kwargs: Any) -> dict[str, Any]:
    if not user:
        return {}

    try:
        hope_user = retrieve_hope_user(user)
        if not hope_user:
            return {}

        if hasattr(backend, "strategy") and hasattr(backend.strategy, "session"):
            backend.strategy.session_set("hope_user_id", str(hope_user.id))
            backend.strategy.session_set("hope_user_data", {
                "id": str(hope_user.id),
                "username": hope_user.username,
                "email": hope_user.email,
                "first_name": hope_user.first_name,
                "last_name": hope_user.last_name,
            })

    except Exception:
        pass

    return {}
