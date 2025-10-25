import os
from typing import Any

from django.http import HttpRequest

from .. import VERSION


def app(request: HttpRequest) -> dict[str, Any]:
    return {
        "app": {
            "version": VERSION,
            "build_date": os.environ.get("BUILD_DATE", ""),
            "commit": os.environ.get("GIT_SHA", "-"),
            "branch": os.environ.get("BRANCH", "-"),
        }
    }


def theme_processor(request: HttpRequest) -> dict[str, Any]:
    mode = request.COOKIES.get("theme", "light")
    size = request.COOKIES.get("size", "font-size-normal")
    return {"theme": {"mode": mode, "size": size}}
