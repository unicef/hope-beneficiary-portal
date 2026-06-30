from typing import Any
import logging
from django.conf import settings
from django.forms import BaseFormSet
from django.http import HttpRequest, HttpResponse, HttpResponseBase, HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.views.generic.edit import ProcessFormView
from flags.decorators import flag_check
from flags.state import flag_enabled

from hope_portal.modules.hope.models import Household
from hope_portal.modules.inspect import Inspector, QuestionData
from hope_portal.ui.forms.flow import QuestionForm, QuestionFormSet
from hope_portal.ui.views.flow.crypt import sign, sign_candidates, unsign_candidates

logger = logging.getLogger(__name__)


@method_decorator(flag_check("FLOW_ASK", True), name="dispatch")
class AskView(TemplateResponseMixin, ContextMixin, ProcessFormView):
    template_name = "pages/flow/ask.html"
    inspector: Inspector
    household: Household
    candidates: list[Household]
    questions: list[QuestionData]

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        self.candidates = unsign_candidates(request, self.kwargs["signed_data"])
        if not self.candidates:
            return HttpResponseRedirect(reverse("ui:flow:not-available"))
        self.household = self.candidates[0]
        self.inspector = Inspector(self.household)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        for index, candidate in enumerate(self.candidates):
            others = self.candidates[:index] + self.candidates[index + 1 :]
            inspector = Inspector(candidate)
            if questions := inspector.get_questions(other_candidates=others or None):
                if index > 0:
                    key = sign_candidates(request, self.candidates[index:])
                    return HttpResponseRedirect(reverse("ui:flow:ask", kwargs={"signed_data": key}))
                self.questions = questions
                return super().get(request, **kwargs)
        return HttpResponseRedirect(reverse("ui:flow:not-available"))

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        formset = QuestionFormSet(data=self.request.POST)
        if not formset.is_valid():
            return self.form_invalid(formset)

        if all(form.check_value() for form in formset.forms):
            return self.form_valid(formset)

        asked = self._extract_asked_answers(formset)
        for candidate in self.candidates[1:]:
            if Inspector(candidate).matches_answers(asked):
                self.household = candidate
                return self.form_valid(formset)

        return self.render_to_response(self.get_context_data(retry=True))

    def _extract_asked_answers(self, formset: Any) -> list[tuple[str, str]]:
        asked = []
        for form in formset.forms:
            try:
                label, _ = form.unsign(form.cleaned_data["signed"])
                asked.append((label, form.cleaned_data["question"]))
            except Exception:  # noqa: BLE001
                logger.error("Failed to extract asked answers", exc_info=True)
        return asked

    def get_formset(self) -> BaseFormSet[QuestionForm]:
        signed_data = self.kwargs["signed_data"]
        if self.request.method == "GET":
            formset = QuestionFormSet(
                initial=[{} for _ in self.questions],
                form_kwargs={"key": signed_data},
            )
            for question_data, form in zip(self.questions, formset, strict=True):
                form.fields["question"].label = question_data.question
                if settings.DEBUG and flag_enabled("DEVELOP_QUESTION_DEBUG", request=self.request):
                    form.fields["question"].help_text = f"{question_data.hint} ({question_data.answer})"
                else:
                    form.fields["question"].help_text = question_data.hint
                form.fields["signed"].initial = form.sign(question_data.question, question_data.answer)
        else:
            formset = QuestionFormSet(data=self.request.POST)
            for form in formset.forms:
                label, _ = form.unsign(form.data[f"{form.prefix}-signed"])
                form.fields["question"].label = label
        return formset

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
