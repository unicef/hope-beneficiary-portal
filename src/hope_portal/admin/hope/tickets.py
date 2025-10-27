from adminfilters.autocomplete import LinkedAutoCompleteFilter
from django.contrib import admin
from django.db import models
from django.http import HttpRequest

from ...modules.hope.models import GrievanceticketPrograms
from ._base import BaseHopeAdmin


@admin.register(GrievanceticketPrograms)
class GrievanceticketProgramsAdmin(BaseHopeAdmin):
    list_display = (
        "grievanceticket",
        "program",
    )
    search_fields = ("name",)

    list_filter = (
        ("program__business_area", LinkedAutoCompleteFilter.factory(parent=None)),
        ("program", LinkedAutoCompleteFilter.factory(parent="program__business_area")),
        "grievanceticket__status",
        "grievanceticket__category",
        "grievanceticket__issue_type",
    )

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[GrievanceticketPrograms]:
        return super().get_queryset(request).select_related("grievanceticket")
