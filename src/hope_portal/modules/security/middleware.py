from typing import Callable

from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.shortcuts import redirect
from django.urls import reverse

from .guards import CookieAttemptGuard


class VisitorAttemptMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponseBase:
        if request.path == reverse("ui:locked_out"):
            return self.get_response(request)

        guard = CookieAttemptGuard(request)

        if guard.is_locked_out():
            request.session["lockout_message"] = guard.get_lockout_message()
            return redirect("ui:locked_out")

        response = self.get_response(request)

        return guard.process_response(response)
