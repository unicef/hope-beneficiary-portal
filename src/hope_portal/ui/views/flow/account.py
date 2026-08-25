from typing import Any

from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import FormView
from flags.decorators import flag_check

from hope_portal.models.beneficiary import Beneficiary
from hope_portal.modules.hope.models import Household
from hope_portal.ui.forms.flow import AccountCredentialsForm
from hope_portal.ui.views.flow.crypt import sign_household, unsign_household


@method_decorator(flag_check("FLOW_ACCOUNT_CREATE", True), name="dispatch")
class AccountCreate(FormView[AccountCredentialsForm]):
    form_class = AccountCredentialsForm
    template_name = "pages/flow/account_create.html"
    household: Household
    beneficiary: Beneficiary | None
    signed_data: str

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.household = unsign_household(request, self.kwargs["signed_data"])
        self.beneficiary = Beneficiary.for_household(self.household)
        self.signed_data = sign_household(request, self.household)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.beneficiary
        return kwargs

    def get_initial(self) -> dict[str, Any]:
        if self.beneficiary is not None:
            return {"username": self.beneficiary.username}
        if self.household.unicef_id:
            return {"username": self.household.unicef_id}
        return {}

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        kwargs["signed_data"] = self.signed_data
        kwargs["has_account"] = self.beneficiary is not None
        return super().get_context_data(**kwargs)

    def form_valid(self, form: AccountCredentialsForm) -> HttpResponse:
        created = self.beneficiary is None
        try:
            with transaction.atomic():
                self.beneficiary = Beneficiary.set_credentials(
                    self.household,
                    form.cleaned_data["username"],
                    form.cleaned_data["password"],
                )
        except IntegrityError:
            form.add_error("username", "This username is already taken.")
            return self.form_invalid(form)
        return render(
            self.request,
            "pages/flow/account_created.html",
            {
                "username": self.beneficiary.username,
                "created": created,
                "signed_data": self.signed_data,
            },
        )
