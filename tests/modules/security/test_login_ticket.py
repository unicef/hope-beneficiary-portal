import pytest
from django.contrib.sessions.middleware import SessionMiddleware

from hope_portal.modules.hope.models import HopeUser
from hope_portal.modules.security.apps import HopeAPIClient, on_login

from testutils.factories.auth import UserFactory


def _add_session(request):
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()


@pytest.mark.django_db
def test_on_login_creates_ticket_when_configured(rf, settings, monkeypatch):
    settings.HOPE_API_BASE_URL = "https://hope.example.org"
    settings.HOPE_API_BUSINESS_AREA_SLUG = "ba-slug"
    settings.HOPE_API_TOKEN = "token"
    settings.HOPE_API_TIMEOUT = 5

    user = UserFactory(email="user@example.org", username="user1")
    hope_user = HopeUser.objects.create(
        id="4f86fe57-3dc1-4e77-b16e-9b3d4c2a5a3c",
        email=user.email,
        username=user.username,
    )

    request = rf.get("/", HTTP_USER_AGENT="test-agent")
    _add_session(request)

    captured = {}

    def _capture_create(self, description):
        captured["description"] = description

    monkeypatch.setattr(HopeAPIClient, "create_beneficiary_ticket", _capture_create)

    on_login(sender=type(user), user=user, request=request)

    assert request.session["hope_user_id"] == str(hope_user.id)
    assert request.session["hope_user_data"]["email"] == user.email
    assert "Beneficiary portal login for user@example.org" in captured["description"]
    assert f"hope_user_id={hope_user.id}" in captured["description"]
    assert "user_agent=test-agent" in captured["description"]


@pytest.mark.django_db
def test_on_login_skips_ticket_without_hope_user(rf, settings, monkeypatch):
    settings.HOPE_API_BASE_URL = "https://hope.example.org"
    settings.HOPE_API_BUSINESS_AREA_SLUG = "ba-slug"
    settings.HOPE_API_TOKEN = "token"
    settings.HOPE_API_TIMEOUT = 5

    user = UserFactory(email="user@example.org", username="user1")
    request = rf.get("/")
    _add_session(request)

    def _fail_create(self, description):
        raise AssertionError("Ticket creation should not be called")

    monkeypatch.setattr(HopeAPIClient, "create_beneficiary_ticket", _fail_create)

    on_login(sender=type(user), user=user, request=request)
