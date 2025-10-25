from django.contrib import admin

from ...modules.hope.models import Payment, PaymentPlan
from ._base import BaseHopeAdmin


@admin.register(PaymentPlan)
class PaymentPlanAdmin(BaseHopeAdmin):
    list_display = ("unicef_id",)


@admin.register(Payment)
class PaymentAdmin(BaseHopeAdmin):
    list_display = ("unicef_id",)
