from typing import Any

from django.conf import settings
from django.forms import BaseFormSet
from django.http import HttpRequest, HttpResponse, HttpResponseBase, HttpResponseRedirect
from django.urls import reverse
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.views.generic.edit import ProcessFormView

from hope_portal.modules.hope.models import Household
from hope_portal.modules.inspect import Inspector
from hope_portal.ui.forms.ask import QuestionForm, QuestionFormSet
from hope_portal.ui.views.flow.crypt import unsign_household


class AskView(TemplateResponseMixin, ContextMixin, ProcessFormView):
    template_name = "pages/flow/ask.html"
    inspector: Inspector
    household: Household

    def get_formset(self) -> BaseFormSet[QuestionForm]:
        key = self.kwargs["signed_data"]

        if self.request.method == "GET":
            questions = self.inspector.get_questions()
            fs = QuestionFormSet(initial=[{} for __ in questions], form_kwargs={"key": key})
            for q, f in zip(questions, fs, strict=True):
                f.fields["question"].label = q.question
                f.fields["question"].help_text = q.answer
                f.fields["signed"].initial = f.sign(q.question, q.answer)
        else:
            fs = QuestionFormSet(data=self.request.POST)
            for frm in fs.forms:
                label, __ = frm.unsign(frm.data[f"{frm.prefix}-signed"])
                frm.fields["question"].label = label
        return fs

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        self.household = unsign_household(request, self.kwargs["signed_data"])
        self.inspector = Inspector(self.household)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        fs = QuestionFormSet(data=self.request.POST)
        if fs.is_valid():
            if all(f.check_value() for f in fs.forms):
                return self.form_valid(fs)
            return self.render_to_response(self.get_context_data(retry=True))
        return self.form_invalid(fs)

    def form_valid(self, formset: BaseFormSet[QuestionForm]) -> HttpResponse:
        return HttpResponseRedirect(reverse("ui:flow:info", kwargs={"signed_data": self.kwargs["signed_data"]}))

    def form_invalid(self, formset: BaseFormSet[QuestionForm]) -> HttpResponse:
        return self.render_to_response(self.get_context_data(formset=formset))

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        kwargs["formset"] = self.get_formset()
        kwargs["household"] = self.household
        if settings.DEBUG:
            kwargs["values"] = self.household
        return super().get_context_data(**kwargs)
