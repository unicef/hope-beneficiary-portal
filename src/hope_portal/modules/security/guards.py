import uuid
from datetime import UTC, datetime, timedelta

from constance import config
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _
from django_countries import settings


class RegistrationAttemptGuard:
    def __init__(self, registration_number: str) -> None:
        self.registration_number = registration_number
        self.lockout_period = timedelta(hours=config.MAX_REGISTRATION_LOCKOUT_HOURS)
        self.cache_key_attempts = f"registration_attempts_{self.registration_number}"
        self.cache_key_lockout = f"registration_lockout_{self.registration_number}"
        self.cache_key_lockout_expiry = f"registration_lockout_expiry_{self.registration_number}"

    @classmethod
    def clear(cls) -> None:
        cache.clear()

    def is_locked_out(self) -> bool:
        return cache.get(self.cache_key_lockout) is not None

    def get_lockout_message(self) -> str:
        if self.is_locked_out():
            expiry_time = cache.get(self.cache_key_lockout_expiry)
            if expiry_time and isinstance(expiry_time, datetime):
                return _("Too many attempts. Please try again after {expiry_time}.").format(
                    expiry_time=expiry_time.strftime("%Y-%m-%d %H:%M:%S %Z")
                )
            return _("Too many attempts. Please try again later.")
        return ""

    def record_attempt(self) -> None:
        if self.is_locked_out():
            return
        attempts = cache.get(self.cache_key_attempts, 0) + 1
        if attempts >= config.MAX_REGISTRATION_ATTEMPTS:
            expiry_time = datetime.now(UTC) + self.lockout_period
            cache.set(self.cache_key_lockout, True, self.lockout_period.total_seconds())
            cache.set(self.cache_key_lockout_expiry, expiry_time, self.lockout_period.total_seconds())
            cache.delete(self.cache_key_attempts)
        else:
            cache.set(self.cache_key_attempts, attempts, self.lockout_period.total_seconds())

    def reset_attempts(self) -> None:
        cache.delete(self.cache_key_attempts)
        cache.delete(self.cache_key_lockout)
        cache.delete(self.cache_key_lockout_expiry)


class CookieAttemptGuard:
    COOKIE_NAME = "visitor_id"
    COOKIE_MAX_AGE = 365 * 24 * 60 * 60  # One year

    def __init__(self, request: HttpRequest) -> None:
        self.request = request
        self.new_visitor_id_created = False
        visitor_id = request.COOKIES.get(self.COOKIE_NAME)
        if not visitor_id:
            visitor_id = uuid.uuid4().hex
            self.new_visitor_id_created = True
        self.visitor_id = visitor_id

        self.lockout_period = timedelta(hours=getattr(config, "MAX_VISITOR_LOCKOUT_HOURS", 24))
        self.max_attempts = getattr(config, "MAX_VISITOR_ATTEMPTS", 20)
        self.cache_key_attempts = f"visitor_attempts_{self.visitor_id}"
        self.cache_key_lockout = f"visitor_lockout_{self.visitor_id}"
        self.cache_key_lockout_expiry = f"visitor_lockout_expiry_{self.visitor_id}"

    def process_response(self, response: HttpResponse) -> HttpResponse:
        if self.new_visitor_id_created:
            response.set_cookie(
                self.COOKIE_NAME,
                self.visitor_id,
                max_age=self.COOKIE_MAX_AGE,
                httponly=True,
                samesite="Lax",
                secure=not settings.DEBUG,
            )
        return response

    def is_locked_out(self) -> bool:
        return cache.get(self.cache_key_lockout) is not None

    def get_lockout_message(self) -> str:
        if self.is_locked_out():
            expiry_time = cache.get(self.cache_key_lockout_expiry)
            if expiry_time and isinstance(expiry_time, datetime):
                return _("Too many attempts. Please try again after {expiry_time}.").format(
                    expiry_time=expiry_time.strftime("%Y-%m-%d %H:%M:%S %Z")
                )
            return _("Too many attempts. Please try again later.")
        return ""

    def record_attempt(self) -> None:
        if self.is_locked_out():
            return
        attempts = cache.get(self.cache_key_attempts, 0) + 1
        if attempts >= self.max_attempts:
            expiry_time = datetime.now(UTC) + self.lockout_period
            cache.set(self.cache_key_lockout, True, self.lockout_period.total_seconds())
            cache.set(self.cache_key_lockout_expiry, expiry_time, self.lockout_period.total_seconds())
            cache.delete(self.cache_key_attempts)
        else:
            cache.set(self.cache_key_attempts, attempts, self.lockout_period.total_seconds())

    def reset_attempts(self) -> None:
        cache.delete(self.cache_key_attempts)
        cache.delete(self.cache_key_lockout)
        cache.delete(self.cache_key_lockout_expiry)
