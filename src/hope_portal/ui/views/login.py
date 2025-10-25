from typing import Any

from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import LogoutView as BaseLogoutView
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpRequest, HttpResponse
from django.urls import reverse


def terminate_session(request: HttpRequest) -> None:
    s = SessionStore(session_key=request.session.session_key)
    s.delete()


class LoginView(BaseLoginView):
    next_page = "/"
    redirect_authenticated_user = True
    redirect_field_name = None


class LogoutView(BaseLogoutView):
    http_method_names = ["post", "options", "get"]

    def get_success_url(self) -> str:
        return reverse("ui:index")

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        terminate_session(request)
        return super().post(request, *args, **kwargs)
