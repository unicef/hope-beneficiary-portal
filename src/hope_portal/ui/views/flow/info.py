from typing import Any

from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.views.generic.edit import ProcessFormView

from hope_portal.modules.hope.models import Household
from hope_portal.ui.views.flow.crypt import unsign


class InfoView(TemplateResponseMixin, ContextMixin, ProcessFormView):
    template_name = "pages/flow/info.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        data = unsign(self.request, self.kwargs["signed_data"])
        kwargs["household"] = Household.objects.get(pk=data["id"])
        return super().get_context_data(**kwargs)
