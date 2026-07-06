from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from django.db.models import QuerySet
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.views.generic.edit import ProcessFormView
from flags.decorators import flag_check

from hope_portal.modules.hope.models import GrievanceticketPrograms, Household, Payment
from hope_portal.ui.views.flow.crypt import unsign


@dataclass
class HHInfo:
    id: str
    head: str
    program: str
    unicef_id: str
    program_registration_id: str
    tickets: QuerySet[GrievanceticketPrograms]
    payments: QuerySet[Payment, Any]


def collect_household_infos(hh: Household) -> dict[str, list[HHInfo]]:
    ret: dict[str, list[HHInfo]] = defaultdict(list)
    for entry in Household.objects.select_related("head_of_household", "program").filter(
        household_collection_id=hh.household_collection_id, unicef_id=hh.unicef_id
    ):
        program_name = entry.program.name if entry.program else _("Unknown program")
        head = entry.head_of_household.full_name if entry.head_of_household else ""
        ret[program_name].append(
            HHInfo(
                id=entry.id.hex,
                unicef_id=entry.unicef_id,  # type: ignore[arg-type]
                head=head,  # type: ignore[arg-type]
                program=program_name,
                program_registration_id=str(entry.program_registration_id),
                payments=Payment.objects.select_related(
                    "delivery_type", "financial_service_provider", "parent_split__payment_plan"
                )
                .filter(household=entry, program=entry.program)
                .only("status", "delivery_type", "parent_split__payment_plan")
                .values("status", "delivery_type__name", "parent_split__payment_plan__start_date"),
                tickets=GrievanceticketPrograms.objects.select_related("grievanceticket").filter(
                    grievanceticket__household_unicef_id=entry.unicef_id, program=entry.program
                ),
            )
        )
    return ret


@method_decorator(flag_check("FLOW_INFO", True), name="dispatch")
class InfoView(TemplateResponseMixin, ContextMixin, ProcessFormView):
    template_name = "pages/flow/info.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        hh: Household
        data = unsign(self.request, self.kwargs["signed_data"])
        hh = Household.objects.get(id=data["id"])
        hhs = collect_household_infos(hh)
        kwargs["hhs"] = dict(hhs)
        kwargs["program_registration_id"] = hh.program_registration_id
        kwargs["household"] = hh
        kwargs["signed_data"] = self.kwargs["signed_data"]
        kwargs["linked_grievances_count"] = GrievanceticketPrograms.objects.filter(
            grievanceticket__household_unicef_id=hh.unicef_id
        ).count()

        return super().get_context_data(**kwargs)


@method_decorator(flag_check("DEVELOP_UNSAFE_INFO", True), name="dispatch")
class InspectView(TemplateResponseMixin, ContextMixin, ProcessFormView):
    template_name = "pages/flow/info.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        if hh := Household.objects.filter(unicef_id=self.kwargs["uniced_id"]).first():
            hhs = collect_household_infos(hh)
            kwargs["hhs"] = dict(hhs)
            kwargs["program_registration_id"] = hh.program_registration_id
            kwargs["household"] = hh
        return super().get_context_data(**kwargs)
