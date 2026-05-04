from typing import Any

from constance import config
from django.contrib.auth.models import Group, User
from social_core.backends.base import BaseAuth


def save_to_group(backend: BaseAuth, user: User | None = None, **kwargs: Any) -> dict[str, Any]:
    if user and (group_name := config.NEW_USER_DEFAULT_GROUP):
        grp, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(grp)
    return {}
