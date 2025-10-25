from typing import TYPE_CHECKING

from django import forms
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import FormView

from hope_portal.ui.forms.start import StartForm
from hope_portal.ui.views.flow.crypt import sign_household

if TYPE_CHECKING:
    from hope_portal.modules.hope.models import Household


class StartView(FormView[StartForm]):
    form_class = StartForm
    template_name = "pages/flow/start.html"

    def form_valid(self, form: forms.Form) -> HttpResponseRedirect:
        hh: Household = form.cleaned_data["registration_number"]
        key = sign_household(self.request, hh)
        url = reverse("ui:flow:ask", kwargs={"signed_data": key})
        return HttpResponseRedirect(url)
