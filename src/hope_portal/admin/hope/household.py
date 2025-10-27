from admin_extra_buttons.decorators import button
from adminfilters.autocomplete import LinkedAutoCompleteFilter
from django.contrib import admin
from django.db import models
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse

from ...modules.hope.models import Household
from ._base import BaseHopeAdmin


@admin.register(Household)
class HouseholdAdmin(BaseHopeAdmin):
    list_display = (
        "unicef_id",
        "head_of_household__full_name",
        "detail_id",
        "program",
    )
    search_fields = ("unicef_id", "detail_id")

    list_filter = (
        ("program__business_area", LinkedAutoCompleteFilter.factory(parent=None)),
        ("program", LinkedAutoCompleteFilter.factory(parent="program__business_area")),
    )

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[Household]:
        return (
            super()
            .get_queryset(request)
            .select_related(
                "program",
                "head_of_household",
            )
        )

    @button()  # type: ignore[arg-type]
    def inspect(self, request: HttpRequest, pk: str) -> HttpResponse | None:
        hh = self.get_object(request, pk)
        if hh:
            return HttpResponseRedirect(reverse("ui:flow:inspect", args=[hh.unicef_id]))
        return None
