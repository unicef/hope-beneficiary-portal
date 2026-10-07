from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from django.db.models import F, QuerySet
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.views.generic.edit import ProcessFormView
from flags.decorators import flag_check

from hope_portal.models.beneficiary import Beneficiary
from hope_portal.modules.hope.models import Grievanceticket, GrievanceticketPrograms, Household, Payment
from hope_portal.modules.hope.patcher.tickets import CATEGORY_BENEFICIARY, STATUS_CHOICES, STATUS_CLOSED
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


@dataclass(frozen=True)
class HouseholdGrievance:
    number: str
    status: str
    submitted_at: datetime | None
    closed_at: datetime | None


def household_grievances(household: Household) -> list[HouseholdGrievance]:
    """Portal grievances for this household in its programme business area.

    A household unicef id is unique only within a programme, so the same id can
    exist in another business area. Only tickets created through the beneficiary
    portal are included.
    """
    unicef_id = household.unicef_id
    program = household.program
    business_area_id = program.business_area_id if program is not None else None
    if not unicef_id or not business_area_id:
        return []
    labels = dict(STATUS_CHOICES)
    tickets = Grievanceticket.objects.filter(
        household_unicef_id=unicef_id,
        business_area_id=business_area_id,
        category=CATEGORY_BENEFICIARY,
    ).order_by(F("created_at").desc(nulls_last=True))
    return [
        HouseholdGrievance(
            number=ticket.unicef_id or "",
            status=labels.get(ticket.status, ""),
            submitted_at=ticket.created_at,
            closed_at=ticket.updated_at if ticket.status == STATUS_CLOSED else None,
        )
        for ticket in tickets
    ]


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
        kwargs["has_account"] = Beneficiary.for_household(hh) is not None
        kwargs["linked_grievances_count"] = GrievanceticketPrograms.objects.filter(
            grievanceticket__household_unicef_id=hh.unicef_id
        ).count()
        kwargs["grievances"] = household_grievances(hh)

        return super().get_context_data(**kwargs)


@method_decorator(flag_check("DEVELOP_UNSAFE_INFO", True), name="dispatch")
class InspectView(TemplateResponseMixin, ContextMixin, ProcessFormView):
    template_name = "pages/flow/info.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        kwargs["grievances"] = []
        if hh := Household.objects.filter(unicef_id=self.kwargs["uniced_id"]).first():
            hhs = collect_household_infos(hh)
            kwargs["hhs"] = dict(hhs)
            kwargs["program_registration_id"] = hh.program_registration_id
            kwargs["household"] = hh
            kwargs["grievances"] = household_grievances(hh)
        return super().get_context_data(**kwargs)
