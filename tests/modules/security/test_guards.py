import uuid

import pytest

from hope_portal.modules.security.guards import CookieAttemptGuard, RegistrationAttemptGuard, config


@pytest.mark.django_db
def test_registration_guard_lockout():
    registration_number = uuid.uuid4().hex
    guard = RegistrationAttemptGuard(registration_number)
    assert not guard.is_locked_out()
    for _ in range(config.MAX_REGISTRATION_ATTEMPTS):
        guard.record_attempt()
    assert guard.is_locked_out()
    message = guard.get_lockout_message()
    assert "Too many attempts" in message


@pytest.mark.django_db
def test_cookie_guard_lockout(rf):
    request = rf.get("/")
    request.COOKIES[CookieAttemptGuard.COOKIE_NAME] = uuid.uuid4().hex

    guard = CookieAttemptGuard(request)
    assert not guard.is_locked_out()
    for _ in range(config.MAX_VISITOR_ATTEMPTS):
        guard.record_attempt()
    assert guard.is_locked_out()
    message = guard.get_lockout_message()
    assert "Too many attempts" in message
