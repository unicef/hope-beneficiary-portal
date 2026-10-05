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
        if not (business_area_slug := self._business_area_slug()):
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

        The ticket itself is only ever about the programme tied to `self.household`, but a household can
        be enrolled in more than one programme (a separate Household row per programme, sharing the same
        household_collection/unicef_id). When that's the case, spell out which programme this ticket is
        for and list the others only as extra context, so staff aren't left guessing which one applies.
        """
        if not self.household.unicef_id:
            return description

        lines = [description, "", f"Household ID: {self.household.unicef_id}"]
        current_label, other_labels = self._programme_labels()
        if other_labels:
            if current_label:
                lines.append(f"Programme for this ticket: {current_label}")
                lines.append("Household is also enrolled in:")
            else:
                lines.append("Household is enrolled in multiple programmes:")
            lines.extend(f"- {label}" for label in other_labels)
        return "\n".join(lines)

    def _programme_labels(self) -> tuple[str | None, list[str]]:
        """Return the label for this ticket's own programme, and labels for any other programmes."""
        rows = (
            Household.objects.select_related("program__business_area")
            .filter(
                household_collection_id=self.household.household_collection_id,
                unicef_id=self.household.unicef_id,
            )
            .exclude(program__isnull=True)
            .values_list("program_id", "program__name", "program__business_area__name")
            .distinct()
        )
        current_label = None
        other_labels = set()
        for program_id, program_name, business_area_name in rows:
            if not program_name:
                continue
            label = f"{program_name} ({business_area_name})" if business_area_name else program_name
            if program_id == self.household.program_id:
                current_label = label
            else:
                other_labels.add(label)
        return current_label, sorted(other_labels)

    def _household_program_id(self) -> str | None:
        program_id = getattr(self.household, "program_id", None)
        return str(program_id) if program_id else None

    def get_success_url(self) -> str:
        return reverse("ui:flow:info", kwargs={"signed_data": self.kwargs["signed_data"]})

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        kwargs["signed_data"] = self.kwargs["signed_data"]
        return super().get_context_data(**kwargs)

    def _business_area_slug(self) -> str | None:
        """Return the business area of the programme this ticket is opened for.

        The same household can be enrolled in several programmes, and those programmes can sit in
        different business areas. The slug must come from the programme we also send as program_id,
        which is the programme on the current household, not whichever sibling row the query hits first.
        """
        program = self.household.program
        if program is None or program.business_area is None:
            return None
        return program.business_area.slug or None
