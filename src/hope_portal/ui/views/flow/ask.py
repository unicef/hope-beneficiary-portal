import logging
from typing import Any

from constance import config
from django.conf import settings
from django.core import signing
from django.core.cache import cache
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

        expected_answers: dict[str, str] = cache.get(self._answers_cache_key(), {})
        if not expected_answers:
            return HttpResponseRedirect(reverse("ui:flow:not-available"))

        asked = self._extract_asked_answers(formset)
        if not asked:
            return HttpResponseRedirect(reverse("ui:flow:not-available"))

        results = [
            form.check_value(expected_answers.get(question_text, ""))
            for form, (question_text, _) in zip(formset.forms, asked, strict=True)
        ]
        if self._meets_pass_threshold(results):
            cache.delete(self._answers_cache_key())
            return self.form_valid(formset)

        for candidate in self.candidates[1:]:
            if Inspector(candidate).matches_answers(asked):
                self.household = candidate
                cache.delete(self._answers_cache_key())
                return self.form_valid(formset)

        return self.render_to_response(self.get_context_data(retry=True))

    @staticmethod
    def _meets_pass_threshold(results: list[bool]) -> bool:
        if not results:
            return False
        try:
            threshold = int(config.VERIFICATION_PASS_THRESHOLD)
        except (TypeError, ValueError):
            threshold = 100
        threshold = max(1, min(100, threshold))
        return (sum(results) / len(results)) * 100 >= threshold

    def _answers_cache_key(self) -> str:
        return f"portal:ask:{self.kwargs['signed_data']}"

    def _extract_asked_answers(self, formset: Any) -> list[tuple[str, str]] | None:
        """Return (question_text, user_answer) pairs, or None if any signed token is invalid."""
        asked = []
        for form in formset.forms:
            try:
                question_text = form.unsign(form.cleaned_data["signed"])
                asked.append((question_text, form.cleaned_data["question"]))
            except signing.BadSignature:
                logger.warning("Tampered signed question field — rejecting submission")
                return None
        return asked

    def get_formset(self) -> BaseFormSet[QuestionForm]:
        signed_data = self.kwargs["signed_data"]
        if self.request.method == "GET":
            cache.set(
                self._answers_cache_key(),
                {question_data.question: question_data.answer for question_data in self.questions},
                timeout=3600,
            )
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
                form.fields["signed"].initial = form.sign(question_data.question)
        else:
            formset = QuestionFormSet(data=self.request.POST)
            for form in formset.forms:
                try:
                    label = form.unsign(form.data[f"{form.prefix}-signed"])
                except signing.BadSignature:
                    label = ""
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
