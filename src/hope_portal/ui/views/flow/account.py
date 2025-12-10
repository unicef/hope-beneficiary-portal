from secrets import token_urlsafe
from typing import Any

from django.contrib.auth.hashers import make_password
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from flags.decorators import flag_check

from hope_portal.models.beneficiary import Beneficiary
from hope_portal.modules.hope.models import Household
from hope_portal.ui.views.flow.crypt import unsign


@method_decorator(flag_check("FLOW_ACCOUNT_CREATE", True), name="dispatch")
class AccountCreate(TemplateView):
    template_name = "pages/flow/account_create.html"

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        hh: Household
        data = unsign(self.request, self.kwargs["signed_data"])
        hh = Household.objects.get(id=data["id"])
        pwd = token_urlsafe(10)
        ben, __ = Beneficiary.objects.get_or_create(
            household_id=hh.id.hex, defaults={"username": hh.unicef_id, "password": make_password(pwd)}
        )
        return render(request, self.template_name, context={"username": ben.username, "password": pwd})
