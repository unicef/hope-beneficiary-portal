import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_sso_login_uses_post():
    """social-auth-app-django >= 6 accepts `social:begin` only as a CSRF-protected POST."""
    client = Client()
    begin = reverse("social:begin", kwargs={"backend": "azuread-tenant-oauth2"})
    assert client.get(begin).status_code == 405

    for url in ("/login/", reverse("admin:login")):
        res = client.get(url)
        assert res.status_code == 200
        content = res.content.decode()
        assert f'action="{begin}"' in content
        assert 'method="post"' in content
        assert f'href="{begin}"' not in content
