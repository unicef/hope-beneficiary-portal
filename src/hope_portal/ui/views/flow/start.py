import logging

from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import FormView, TemplateView
from flags.decorators import flag_check

from hope_portal.exception import FlowLockoutError, FlowTimeoutError
from hope_portal.models.beneficiary import Beneficiary
from hope_portal.modules.hope.models import Household, Individual
from hope_portal.modules.security.otp import generate_otp, send_otp_sms, store_otp, verify_otp
from hope_portal.ui.forms.flow import AuthForm, EmailForm, OTPForm, SMSForm, StartForm
from hope_portal.ui.views.flow.crypt import sign, sign_candidates, sign_household, unsign


logger = logging.getLogger(__name__)


@method_decorator(flag_check("FLOW_START_REGISTRATION", True), name="dispatch")
class StartView(FormView[StartForm]):
    form_class = StartForm
    template_name = "pages/flow/start_reg.html"

    def form_valid(self, form: forms.Form) -> TemplateResponse | HttpResponseRedirect:
        try:
            candidates: list[Household] = form.cleaned_data["registration_number"]
            key = sign_candidates(self.request, candidates)
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
                individual = Individual.objects.get(phone_no=phone_number)
                otp = generate_otp()
                store_otp(f"sms:{phone_number}", otp)
                send_otp_sms(phone_number, otp)
                key = sign(
                    self.request,
                    {"id": str(individual.household_id), "identifier": phone_number, "channel": "sms"},
                )
                url = reverse("ui:flow:verify-otp", kwargs={"channel": "sms", "signed_data": key})
            except (Individual.DoesNotExist, Individual.MultipleObjectsReturned):
                logger.warning("Individual not found for phone number", extra={"phone_number": phone_number})
            return HttpResponseRedirect(url)
        except FlowLockoutError as e:
            logger.warning("Flow lockout error", extra={"message": str(e)})
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
                individual = Individual.objects.get(email=email)
                otp = generate_otp()
                store_otp(f"email:{email}", otp)
                send_mail(
                    "Your verification code",
                    f"Your OTP is: {otp}. It is valid for {settings.OTP_VALIDITY_MINUTES} minutes.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True,
                )
                key = sign(
                    self.request,
                    {"id": str(individual.household_id), "identifier": email, "channel": "email"},
                )
                logger.info("Email sent to", extra={"email": email})
                url = reverse("ui:flow:verify-otp", kwargs={"channel": "email", "signed_data": key})
            except (Individual.DoesNotExist, Individual.MultipleObjectsReturned):
                logger.warning("Individual not found for email", extra={"email": email})
            return HttpResponseRedirect(url)
        except FlowLockoutError as e:
            logger.warning("Flow lockout error", extra={"message": str(e)})
            return TemplateResponse(self.request, "pages/flow/locked_out.html", {"message": e})


class OTPVerifyView(FormView[OTPForm]):
    form_class = OTPForm
    template_name = "pages/flow/start_otp.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        kwargs["channel"] = self.kwargs["channel"]
        return super().get_context_data(**kwargs)

    def form_valid(self, form: forms.Form) -> HttpResponse:
        channel = self.kwargs["channel"]
        try:
            data = unsign(
                self.request,
                self.kwargs["signed_data"],
                max_age=settings.OTP_VALIDITY_MINUTES * 60,
            )
            if data.get("channel") != channel:
                raise FlowTimeoutError()
            identifier = data.get("identifier", "")
            if not verify_otp(f"{channel}:{identifier}", form.cleaned_data["otp"]):
                form.add_error("otp", "Invalid code")
                return self.form_invalid(form)
            household = Household.objects.get(pk=data["id"])
            return HttpResponseRedirect(
                reverse("ui:flow:info", kwargs={"signed_data": sign_household(self.request, household)})
            )
        except (FlowTimeoutError, Household.DoesNotExist):
            logger.warning("OTP verification failed: expired or invalid token", extra={"channel": channel})
            form.add_error("otp", "Verification expired. Request a new code.")
            return self.form_invalid(form)


@method_decorator(flag_check("FLOW_START_AUTH", True), name="dispatch")
class AuthView(FormView[AuthForm]):
    form_class = AuthForm
    template_name = "pages/flow/start_auth.html"

    def form_valid(self, form: forms.Form) -> TemplateResponse | HttpResponseRedirect:
        try:
            url = reverse("ui:index")
            beneficiary = Beneficiary.objects.get(username=form.cleaned_data["username"])
            if beneficiary.check_password(form.cleaned_data["password"]):
                url = reverse(
                    "ui:flow:info", kwargs={"signed_data": sign_household(self.request, beneficiary.household)}
                )
            return HttpResponseRedirect(url)
        except Beneficiary.DoesNotExist:
            logger.warning("Beneficiary not found", extra={"username": form.cleaned_data["username"]})
            form.add_error("username", "Invalid username or password")
            return self.form_invalid(form)
        except FlowLockoutError as e:
            return TemplateResponse(self.request, "pages/flow/locked_out.html", {"message": e})


class NotAvailable(TemplateView):
    template_name = "pages/flow/not_available.html"
