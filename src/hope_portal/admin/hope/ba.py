from django.contrib import admin

from ...modules.hope.models import BusinessArea
from ._base import BaseHopeAdmin


@admin.register(BusinessArea)
class BusinessAreaAdmin(BaseHopeAdmin):
    list_display = (
        "name",
        "code",
    )
    search_fields = ("name",)
