from adminfilters.autocomplete import LinkedAutoCompleteFilter
from django.contrib import admin
from django.db import models
from django.http import HttpRequest

from ...modules.hope.models import Program
from ._base import BaseHopeAdmin


@admin.register(Program)
class ProgramAdmin(BaseHopeAdmin):
    list_display = (
        "name",
        "status",
        "start_date",
        "end_date",
    )
    search_fields = ("name",)

    list_filter = (("business_area", LinkedAutoCompleteFilter.factory(parent=None)),)

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[Program]:
        return super().get_queryset(request).select_related("business_area")
