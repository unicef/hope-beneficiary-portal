from django.db import models
from django.http import HttpRequest
from unfold.admin import ModelAdmin


class BaseHopeAdmin(ModelAdmin):  # type: ignore[misc]
    def has_delete_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return False

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False
