from typing import TYPE_CHECKING, Any

from django.apps import AppConfig
from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.db.models import Model

from hope_portal.modules.hope.helpers import retrieve_hope_user

if TYPE_CHECKING:
    from hope_portal.models import User


class Config(AppConfig):
    name = "hope_portal.modules.security"
    verbose_name = "Security"


def on_login(sender: type[Model], user: "User", request: Any = None, **kwargs: Any) -> None:
    if user.email in settings.SUPERUSERS or user.username in settings.SUPERUSERS:
        user.is_superuser = True
        user.is_staff = True
        user.save()

    _fetch_hope_user_data(user, request)


def _fetch_hope_user_data(user: "User", request: Any = None) -> None:
    try:
        hope_user = retrieve_hope_user(user)

        if hope_user and request and hasattr(request, "session"):
            # Store hope user data in session for later use
            request.session["hope_user_id"] = str(hope_user.id)
            request.session["hope_user_data"] = {
                "id": str(hope_user.id),
                "username": hope_user.username,
                "email": hope_user.email,
                "first_name": hope_user.first_name,
                "last_name": hope_user.last_name,
            }

    except Exception:
        pass


user_logged_in.connect(on_login)
