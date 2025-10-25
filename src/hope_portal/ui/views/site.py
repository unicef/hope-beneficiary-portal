from django.http import HttpRequest, HttpResponse
from django.views import View
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "pages/index.html"


class HealthCheckView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return HttpResponse("Ok")
