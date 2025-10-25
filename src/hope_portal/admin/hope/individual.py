from django.contrib import admin
from django.db import models
from django.http import HttpRequest

from ...modules.hope.models import Individual
from ._base import BaseHopeAdmin


@admin.register(Individual)
class IndividualAdmin(BaseHopeAdmin):
    list_display = ("unicef_id", "household")

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[Individual]:
        return super().get_queryset(request).select_related("household")
