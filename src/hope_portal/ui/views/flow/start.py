from typing import TYPE_CHECKING

from django import forms
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.generic import FormView, TemplateView

from hope_portal.exception import FlowLockoutError
from hope_portal.ui.forms.flow import StartForm
from hope_portal.ui.views.flow.crypt import sign_household

if TYPE_CHECKING:
    from hope_portal.modules.hope.models import Household


class StartView(FormView[StartForm]):
    form_class = StartForm
    template_name = "pages/flow/start.html"

    def form_valid(self, form: forms.Form) -> TemplateResponse | HttpResponseRedirect:
        try:
            hh: Household = form.cleaned_data["registration_number"]
            key = sign_household(self.request, hh)
            url = reverse("ui:flow:ask", kwargs={"signed_data": key})
            return HttpResponseRedirect(url)
        except FlowLockoutError as e:
            return TemplateResponse(self.request, "pages/flow/locked_out.html", {"message": e})


class NotAvailable(TemplateView):
    template_name = "pages/flow/not_available.html"
