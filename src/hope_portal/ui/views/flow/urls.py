from django.urls import path
from django.views.generic import TemplateView

from .account import AccountCreate
from .ask import AskView
from .info import InfoView, InspectView
from .issues import IssueView
from .start import AuthView, EmailView, NotAvailable, SMSView, StartView

app_name = "flow"

urlpatterns = [
    path("start/registration/", StartView.as_view(), name="start-registration"),
    path("start/sms/", SMSView.as_view(), name="start-sms"),
    path("start/email/", EmailView.as_view(), name="start-email"),
    path("start/auth/", AuthView.as_view(), name="start-auth"),
    path("account/create/<str:signed_data>/", AccountCreate.as_view(), name="account-create"),
    path("ask/<str:signed_data>/", AskView.as_view(), name="ask"),
    path("info/<str:signed_data>/", InfoView.as_view(), name="info"),
    path("open-issue/<str:signed_data>/", IssueView.as_view(), name="open-issue"),
    path("inspect/<str:uniced_id>/", InspectView.as_view(), name="inspect"),
    path("not-available/", NotAvailable.as_view(), name="not-available"),
    path("sent/sms/", TemplateView.as_view(template_name="pages/flow/sent.html"), name="sms-sent"),
    path("sent/email/", TemplateView.as_view(template_name="pages/flow/sent.html"), name="email-sent"),
]
