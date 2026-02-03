import logging
from requests import Session
from typing import TYPE_CHECKING, Any, cast
from urllib.error import HTTPError, URLError

from django.apps import AppConfig
from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.db.models import Model

if TYPE_CHECKING:
    from hope_portal.models import User
    from hope_portal.modules.hope.models import HopeUser
    from django.contrib.auth.models import AbstractBaseUser


logger = logging.getLogger(__name__)


class HopeAPIClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        business_area_slug: str,
        timeout: int,
    ) -> None:
        self.base_url = base_url
        self.token = token
        self.business_area_slug = business_area_slug
        self.timeout = timeout

        self._session = Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Token {self.token}",
            }
        )

    def _post(self, endpoint: str, payload: dict[str, Any]) -> None:
        url = f"{self.base_url.rstrip('/')}/api/{self.business_area_slug}/{endpoint}"
        try:
            response = self._session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except HTTPError as exc:
            logger.warning(
                "Failed to create beneficiary ticket",
                extra={"status": exc.code, "reason": exc.reason},
                exc_info=True,
            )
        except URLError:
            logger.warning("Failed to reach HOPE API", exc_info=True)
        except Exception:  # noqa: BLE001
            logger.warning("Unexpected error creating beneficiary ticket", exc_info=True)

    def create_beneficiary_ticket(self, description: str) -> None:
        payload = {"description": description}
        self._post("beneficiary-tickets/", payload)


class Config(AppConfig):
    name = "hope_portal.modules.security"
    verbose_name = "Security"


def on_login(sender: type[Model], user: "User", request: Any = None, **kwargs: Any) -> None:
    if user.email in settings.SUPERUSERS or user.username in settings.SUPERUSERS:
        user.is_superuser = True
        user.is_staff = True
        user.save()

    hope_user = _fetch_hope_user_data(user, request)
    _create_beneficiary_ticket(user, hope_user, request)


def _fetch_hope_user_data(user: "User", request: Any = None) -> "HopeUser | None":
    from hope_portal.modules.hope.helpers import retrieve_hope_user  # noqa: PLC0415

    try:
        hope_user = retrieve_hope_user(cast("AbstractBaseUser", user))

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

        return hope_user

    except Exception:  # noqa: BLE001
        logger.error("Error fetching hope user data", exc_info=True)

    return None


def _create_beneficiary_ticket(user: "User", hope_user: "HopeUser | None", request: Any = None) -> None:
    if not hope_user:
        return
    if not settings.HOPE_API_BASE_URL:
        return
    if not settings.HOPE_API_TOKEN:
        return
    if not settings.HOPE_API_BUSINESS_AREA_SLUG:
        return

    identifier = user.email or user.username or str(user.pk)
    description = f"Beneficiary portal login for {identifier}"
    if hope_user:
        description = f"{description} (hope_user_id={hope_user.id})"
    if request:
        user_agent = request.META.get("HTTP_USER_AGENT")
        if user_agent:
            description = f"{description}; user_agent={user_agent}"

    client = HopeAPIClient(
        base_url=settings.HOPE_API_BASE_URL,
        token=settings.HOPE_API_TOKEN,
        business_area_slug=settings.HOPE_API_BUSINESS_AREA_SLUG,
        timeout=settings.HOPE_API_TIMEOUT,
    )
    client.create_beneficiary_ticket(description)


user_logged_in.connect(on_login)
