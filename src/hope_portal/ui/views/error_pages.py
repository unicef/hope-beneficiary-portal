from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from ...utils.language import get_attr, repr_list
from ...utils.sentry import capture_exception


def handler_sentry(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    try:
        raise ValueError("Sentry test")
    except ValueError as e:
        code = capture_exception(e)
    return HttpResponse(code, status=500)


def handler410(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    response = render(request, "hope_portal/errors/410.html", {"code": 410, "title": "Gone"})
    response.status_code = 400
    return response


def handler400(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    response = render(request, "hope_portal/errors/400.html", {"code": 400, "title": "Bad Request"})
    response.status_code = 400
    return response


def handler403(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    exc = kwargs.get("exception")
    data = {
        "event_id": None,
        "code": 403,
        "title": "Forbidden",
        "settings": settings,
        "referer": request.META.get("referer", "/"),
        "description": "The client has insufficient authentication credentials for the server to process this request.",
    }
    if exc:
        data["event_id"] = capture_exception(exc)

    if get_attr(exc, "view.permissions", []):
        data["permissions"] = repr_list(exc.view.permissions)  # type: ignore[union-attr]
    return render(request, "hope_portal/errors/403.html", data)


def handler404(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    response = render(
        request,
        "hope_portal/errors/404.html",
        {"code": 404, "title": "Page not found"},
    )
    response.status_code = 404
    return response


def handler500(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    response = render(
        request,
        "hope_portal/errors/500.html",
        {"code": 500, "title": "Server Error", "message": "You've encountered an error, oh noes!"},
    )
    response.status_code = 500
    return response
