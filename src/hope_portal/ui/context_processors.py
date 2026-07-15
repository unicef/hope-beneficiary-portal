from typing import Any

from django import forms
from django.conf import settings
from django.http import HttpRequest


class SiteMedia(forms.Media):
    js_files = ["js/js.cookie%s.js", "js/theme%s.js", "js/auto_logout%s.js"]

    def __init__(self) -> None:
        extra = "" if settings.DEBUG else ".min"
        super().__init__(None, None, [*[f % extra for f in self.js_files]])


def theme(request: HttpRequest) -> dict[str, Any]:
    mode = request.COOKIES.get("theme-mode", "light")
    size = request.COOKIES.get("theme-size", "font-size-normal")
    return {
        "site_media": SiteMedia(),
        "theme": {"mode": mode, "size": size},
        "LOGOUT_TIMEOUT_MS": settings.LOGOUT_TIMEOUT_MS,
        "ISSUES_CONFIGURED": settings.ISSUES_CONFIGURED,
    }
