import pytest
from hope_portal.modules.security.apps import on_login

from testutils.factories.auth import UserFactory


@pytest.mark.django_db
def test_on_login_does_nothing_for_regular_user(settings):
    settings.SUPERUSERS = ["admin@example.org"]
    user = UserFactory(email="user@example.org", username="user1")
    on_login(sender=type(user), user=user)
    user.refresh_from_db()
    assert user.is_superuser is False
    assert user.is_staff is False
