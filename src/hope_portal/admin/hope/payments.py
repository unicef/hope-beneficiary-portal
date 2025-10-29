from admin_extra_buttons.decorators import button
from adminfilters.autocomplete import LinkedAutoCompleteFilter
from django.contrib import admin
from django.db import models
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse

from ...modules.hope.models import Payment, PaymentPlan
from ._base import BaseHopeAdmin


@admin.register(PaymentPlan)
class PaymentPlanAdmin(BaseHopeAdmin):
    list_display = ("unicef_id",)


@admin.register(Payment)
class PaymentAdmin(BaseHopeAdmin):
    list_display = ("unicef_id", "business_area", "program__name", "household", "status")

    list_filter = (
        ("business_area", LinkedAutoCompleteFilter.factory(parent=None)),
        ("program", LinkedAutoCompleteFilter.factory(parent="business_area")),
        "status",
    )

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[Payment]:
        return (
            super()
            .get_queryset(request)
            .select_related(
                "program",
                "business_area",
                "household",
                "head_of_household",
            )
        )

    @button()  # type: ignore[arg-type]
    def inspect_household(self, request: HttpRequest, pk: str) -> HttpResponse | None:
        hh = self.get_object(request, pk)
        if hh:
            return HttpResponseRedirect(reverse("ui:flow:inspect", args=[hh.household.unicef_id]))
        return None
