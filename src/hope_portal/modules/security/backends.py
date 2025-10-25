from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser
    from django.http import HttpRequest


class AnyUserAuthBackend(ModelBackend):
    """DEBUG Only smart auth backend  auto-create users."""

    def authenticate(
        self, request: "HttpRequest | None", username: str | None = None, password: str | None = None, **kwargs: Any
    ) -> "AbstractBaseUser | None":
        if settings.DEBUG:
            if username in ["admin", "superuser", "administrator", "sax"]:
                user, __ = get_user_model().objects.update_or_create(  # type: ignore[attr-defined]
                    username=username,
                    defaults={"is_staff": True, "is_active": True, "is_superuser": True},
                )
                return user
            if username in ["staff"]:
                user, __ = get_user_model().objects.update_or_create(  # type: ignore[attr-defined]
                    username=username,
                    defaults={"is_staff": True, "is_active": True, "is_superuser": False},
                )
                return user
        return None
