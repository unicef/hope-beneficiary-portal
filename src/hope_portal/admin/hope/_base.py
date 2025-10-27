from admin_extra_buttons.mixins import ExtraButtonsMixin
from adminfilters.mixin import AdminAutoCompleteSearchMixin, AdminFiltersMixin
from django.db import models
from django.http import HttpRequest
from unfold.admin import ModelAdmin


class BaseHopeAdmin(AdminFiltersMixin, ExtraButtonsMixin, AdminAutoCompleteSearchMixin, ModelAdmin):  # type: ignore[misc]
    def has_delete_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return False

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False
