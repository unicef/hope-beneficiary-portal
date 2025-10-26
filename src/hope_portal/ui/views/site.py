from typing import Any

from django.http import HttpRequest, HttpResponse
from django.views import View
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "pages/index.html"


class HealthCheckView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return HttpResponse("Ok")


class LockedOutView(TemplateView):
    template_name = "pages/lockout.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["message"] = self.request.session.pop("lockout_message", "")
        return context
