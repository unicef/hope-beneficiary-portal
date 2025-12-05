import os
from datetime import datetime
from typing import Any

from django import forms
from django.conf import settings
from django.http import HttpRequest

from .. import VERSION


class SiteMedia(forms.Media):
    js_files = ["js/js.cookie%s.js", "js/theme%s.js", "js/auto_logout%s.js"]

    def __init__(self) -> None:
        extra = "" if settings.DEBUG else ".min"
        super().__init__(None, None, [*[f % extra for f in self.js_files]])


def app(request: HttpRequest) -> dict[str, Any]:
    return {
        "year": datetime.now().year,
        "app": {
            "version": VERSION,
            "build_date": os.environ.get("BUILD_DATE", ""),
            "commit": os.environ.get("GIT_SHA", "-"),
            "branch": os.environ.get("BRANCH", "-"),
        },
    }


def theme(request: HttpRequest) -> dict[str, Any]:
    mode = request.COOKIES.get("theme-mode", "light")
    size = request.COOKIES.get("theme-size", "font-size-normal")
    return {"site_media": SiteMedia(), "theme": {"mode": mode, "size": size}}
