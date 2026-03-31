from typing import TYPE_CHECKING

from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import FormView, TemplateView
from flags.decorators import flag_check

from hope_portal.exception import FlowLockoutError
from hope_portal.models.beneficiary import Beneficiary
from hope_portal.modules.hope.models import Individual
from hope_portal.modules.security.otp import generate_otp, send_otp_sms, store_otp
from hope_portal.ui.forms.flow import AuthForm, EmailForm, SMSForm, StartForm
from hope_portal.ui.views.flow.crypt import sign_household

if TYPE_CHECKING:
    from hope_portal.modules.hope.models import Household


@method_decorator(flag_check("FLOW_START_REGISTRATION", True), name="dispatch")
class StartView(FormView[StartForm]):
    form_class = StartForm
    template_name = "pages/flow/start_reg.html"

    def form_valid(self, form: forms.Form) -> TemplateResponse | HttpResponseRedirect:
        try:
            hh: Household = form.cleaned_data["registration_number"]
            key = sign_household(self.request, hh)
            url = reverse("ui:flow:ask", kwargs={"signed_data": key})
            return HttpResponseRedirect(url)
        except FlowLockoutError as e:
            return TemplateResponse(self.request, "pages/flow/locked_out.html", {"message": e})


@method_decorator(flag_check("FLOW_START_SMS", True), name="dispatch")
class SMSView(FormView[SMSForm]):
    form_class = SMSForm
    template_name = "pages/flow/start_sms.html"

    def form_valid(self, form: forms.Form) -> TemplateResponse | HttpResponseRedirect:
        try:
            url = reverse("ui:flow:sms-sent")
            phone_number = form.cleaned_data["number"]
            try:
                Individual.objects.get(phone_no=phone_number)
                otp = generate_otp()
                store_otp(phone_number, otp)
                send_otp_sms(phone_number, otp)
            except (Individual.DoesNotExist, Individual.MultipleObjectsReturned):
                pass
            return HttpResponseRedirect(url)
        except FlowLockoutError as e:
            return TemplateResponse(self.request, "pages/flow/locked_out.html", {"message": e})


@method_decorator(flag_check("FLOW_START_EMAIL", True), name="dispatch")
class EmailView(FormView[EmailForm]):
    form_class = EmailForm
    template_name = "pages/flow/start_email.html"

    def form_valid(self, form: forms.Form) -> TemplateResponse | HttpResponseRedirect:
        try:
            url = reverse("ui:flow:email-sent")
            email = form.cleaned_data["email"]
            try:
                Individual.objects.get(email=email)
                send_mail("subject", "message", from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[email])
            except (Individual.DoesNotExist, Individual.MultipleObjectsReturned):
                pass
            return HttpResponseRedirect(url)
        except FlowLockoutError as e:
            return TemplateResponse(self.request, "pages/flow/locked_out.html", {"message": e})


@method_decorator(flag_check("FLOW_START_AUTH", True), name="dispatch")
class AuthView(FormView[AuthForm]):
    form_class = AuthForm
    template_name = "pages/flow/start_auth.html"

    def form_valid(self, form: forms.Form) -> TemplateResponse | HttpResponseRedirect:
        try:
            url = reverse("ui:index")
            ben = Beneficiary.objects.get(username=form.cleaned_data["username"])
            if ben.check_password(form.cleaned_data["password"]):
                url = reverse("ui:flow:info", kwargs={"signed_data": sign_household(self.request, ben.household)})
            return HttpResponseRedirect(url)
        except FlowLockoutError as e:
            return TemplateResponse(self.request, "pages/flow/locked_out.html", {"message": e})


class NotAvailable(TemplateView):
    template_name = "pages/flow/not_available.html"
