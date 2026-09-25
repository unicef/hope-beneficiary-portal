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

    def form_valid(self, form: TicketCreateForm) -> HttpResponse:
        if not settings.HOPE_API_BASE_URL or not settings.HOPE_API_TOKEN:
            form.add_error(None, "Ticket service is not configured.")
            return self.form_invalid(form)
        if not (business_area_slug := self._first_business_area_slug()):
            form.add_error(None, "No business area available for this household.")
            return self.form_invalid(form)

        client = HopeAPIClient(
            base_url=settings.HOPE_API_BASE_URL,
            token=settings.HOPE_API_TOKEN,
            timeout=settings.HOPE_API_TIMEOUT,
        )
        client.create_beneficiary_ticket(
            business_area_slug=business_area_slug,
            description=self._description_with_household_context(form.cleaned_data["description"]),
            program_id=self._household_program_id(),
        )
        return redirect(self.get_success_url())

    def _description_with_household_context(self, description: str) -> str:
        """Append the household id, since beneficiary tickets have no other link back to a household in HOPE.

        If the household is enrolled in more than one programme, also list every programme so staff
        can tell which one the beneficiary means.
        """
        if not self.household.unicef_id:
            return description

        lines = [description, "", f"Household ID: {self.household.unicef_id}"]
        programmes = self._programme_labels()
        if len(programmes) > 1:
            lines.append("Programmes:")
            lines.extend(f"- {label}" for label in programmes)
        return "\n".join(lines)

    def _programme_labels(self) -> list[str]:
        rows = (
            Household.objects.select_related("program__business_area")
            .filter(
                household_collection_id=self.household.household_collection_id,
                unicef_id=self.household.unicef_id,
            )
            .exclude(program__isnull=True)
            .values_list("program__name", "program__business_area__name")
            .distinct()
        )
        labels = {
            f"{program_name} ({business_area_name})" if business_area_name else program_name
            for program_name, business_area_name in rows
            if program_name
        }
        return sorted(labels)

    def _household_program_id(self) -> str | None:
        program_id = getattr(self.household, "program_id", None)
        return str(program_id) if program_id else None

    def get_success_url(self) -> str:
        return reverse("ui:flow:info", kwargs={"signed_data": self.kwargs["signed_data"]})

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        kwargs["signed_data"] = self.kwargs["signed_data"]
        return super().get_context_data(**kwargs)

    def _first_business_area_slug(self) -> str | None:
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
        for slug, _name in rows:
            if slug:
                return slug
        return None
