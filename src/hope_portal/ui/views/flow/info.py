from typing import Any

from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.views.generic.edit import ProcessFormView

from hope_portal.ui.views.flow.crypt import unsign_household


class InfoView(TemplateResponseMixin, ContextMixin, ProcessFormView):
    template_name = "pages/flow/info.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        kwargs["household"] = unsign_household(self.request, self.kwargs["signed_data"])
        return super().get_context_data(**kwargs)
