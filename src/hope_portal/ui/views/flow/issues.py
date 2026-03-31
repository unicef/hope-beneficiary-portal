from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView

from hope_portal.modules.hope.models import Household
from hope_portal.modules.security.clients import HopeAPIClient
from hope_portal.ui.forms.flow import TicketCreateForm
from hope_portal.ui.views.flow.crypt import unsign_household


class IssueView(FormView[TicketCreateForm]):
    form_class = TicketCreateForm
    template_name = "pages/flow/open_issue.html"
    household: Household

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.household = unsign_household(request, self.kwargs["signed_data"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["business_area_choices"] = self._business_area_choices()
        return kwargs

    def form_valid(self, form: TicketCreateForm) -> HttpResponse:
        if not settings.HOPE_API_BASE_URL or not settings.HOPE_API_TOKEN:
            form.add_error(None, "Ticket service is not configured.")
            return self.form_invalid(form)

        client = HopeAPIClient(
            base_url=settings.HOPE_API_BASE_URL,
            token=settings.HOPE_API_TOKEN,
            timeout=settings.HOPE_API_TIMEOUT,
        )
        client.create_beneficiary_ticket(
            business_area_slug=form.cleaned_data["business_area_slug"],
            description=form.cleaned_data["description"],
        )
        return redirect(self.get_success_url())

    def get_success_url(self) -> str:
        return reverse("ui:flow:info", kwargs={"signed_data": self.kwargs["signed_data"]})

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        kwargs["signed_data"] = self.kwargs["signed_data"]
        return super().get_context_data(**kwargs)

    def _business_area_choices(self) -> list[tuple[str, str]]:
        rows = (
            Household.objects.select_related("program__business_area")
            .filter(
                household_collection_id=self.household.household_collection_id,
                unicef_id=self.household.unicef_id,
            )
            .exclude(program__business_area__slug__isnull=True)
            .values_list("program__business_area__slug", "program__business_area__name")
            .distinct()
        )
        return [(slug, name or slug) for slug, name in rows if slug]
