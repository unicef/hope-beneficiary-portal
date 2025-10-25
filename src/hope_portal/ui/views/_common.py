from typing import Any

from django import forms
from django.conf import settings
from django.views import View
from django.views.generic.base import ContextMixin


class MediaMixin(ContextMixin, View):
    js_files: list[str]

    @property
    def media(self) -> forms.Media:
        extra = "" if settings.DEBUG else ".min"
        js_files = [*[f % extra for f in self.js_files]]
        return forms.Media(js=js_files)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        if "media" in self.kwargs:
            self.kwargs["media"] += self.media
        else:
            self.kwargs["media"] = self.media
        base = super().get_context_data(**kwargs)
        if "media" not in base:
            base["media"] = self.media
        return base
