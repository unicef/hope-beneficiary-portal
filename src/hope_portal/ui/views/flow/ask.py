from typing import Any

from django.conf import settings
from django.forms import BaseFormSet
from django.http import HttpRequest, HttpResponse, HttpResponseBase, HttpResponseRedirect
from django.urls import reverse
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.views.generic.edit import ProcessFormView
from flags.state import flag_enabled

from hope_portal.modules.hope.models import Household
from hope_portal.modules.inspect import Inspector, QuestionData
from hope_portal.ui.forms.flow import QuestionForm, QuestionFormSet
from hope_portal.ui.views.flow.crypt import sign, unsign_household


class AskView(TemplateResponseMixin, ContextMixin, ProcessFormView):
    template_name = "pages/flow/ask.html"
    inspector: Inspector
    household: Household
    questions: list[QuestionData]

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        self.household = unsign_household(request, self.kwargs["signed_data"])
        self.inspector = Inspector(self.household)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not (questions := self.inspector.get_questions()):
            return HttpResponseRedirect(reverse("ui:flow:not-available"))
        self.questions = questions
        return super().get(request, **kwargs)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        fs = QuestionFormSet(data=self.request.POST)
        if fs.is_valid():
            if all(f.check_value() for f in fs.forms):
                return self.form_valid(fs)
            return self.render_to_response(self.get_context_data(retry=True))
        return self.form_invalid(fs)

    def get_formset(self) -> BaseFormSet[QuestionForm]:
        key = self.kwargs["signed_data"]
        frm: QuestionForm
        if self.request.method == "GET":
            fs = QuestionFormSet(initial=[{} for __ in self.questions], form_kwargs={"key": key})
            for q, frm in zip(self.questions, fs, strict=True):
                frm.fields["question"].label = q.question
                if settings.DEBUG and flag_enabled("DEVELOP_QUESTION_DEBUG", request=self.request):
                    frm.fields["question"].help_text = f"{q.hint} ({q.answer})"
                else:
                    frm.fields["question"].help_text = q.hint
                frm.fields["signed"].initial = frm.sign(q.question, q.answer)
        else:
            fs = QuestionFormSet(data=self.request.POST)
            for frm in fs.forms:
                label, __ = frm.unsign(frm.data[f"{frm.prefix}-signed"])
                frm.fields["question"].label = label
        return fs

    def form_valid(self, formset: BaseFormSet[QuestionForm]) -> HttpResponse:
        key = sign(self.request, {"source": self.kwargs["signed_data"], "id": str(self.household.pk)})
        return HttpResponseRedirect(reverse("ui:flow:info", kwargs={"signed_data": key}))

    def form_invalid(self, formset: BaseFormSet[QuestionForm]) -> HttpResponse:
        return self.render_to_response(self.get_context_data(formset=formset))

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        kwargs["formset"] = self.get_formset()
        kwargs["household"] = self.household
        if settings.DEBUG:
            kwargs["values"] = self.household
        return super().get_context_data(**kwargs)
