from adminfilters.autocomplete import LinkedAutoCompleteFilter
from django.contrib import admin
from django.db import models
from django.http import HttpRequest

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
