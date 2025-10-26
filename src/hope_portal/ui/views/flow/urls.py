from django.urls import path

from .ask import AskView
from .info import InfoView
from .start import NotAvailable, StartView

app_name = "flow"

urlpatterns = [
    path("start/", StartView.as_view(), name="start"),
    path("ask/<str:signed_data>/", AskView.as_view(), name="ask"),
    path("info/<str:signed_data>/", InfoView.as_view(), name="info"),
    path("not-available/", NotAvailable.as_view(), name="not-available"),
]
