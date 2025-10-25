from django.contrib import admin
from django.db import models
from django.http import HttpRequest

from ...modules.hope.models import Household
from ._base import BaseHopeAdmin


@admin.register(Household)
class HouseholdAdmin(BaseHopeAdmin):
    list_display = (
        "unicef_id",
        "head_of_household__full_name",
        "detail_id",
    )
    search_fields = ("unicef_id", "detail_id")

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[Household]:
        return (
            super()
            .get_queryset(request)
            .select_related(
                "head_of_household",
            )
        )
