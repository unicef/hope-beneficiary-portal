from typing import Any

from django import forms
from django.core import signing
from django.forms.renderers import DjangoTemplates

from hope_portal.exception import FlowLockoutError
from hope_portal.modules.hope.models import Household
from hope_portal.modules.security.guards import RegistrationAttemptGuard


class QuestionRenderer(DjangoTemplates):
    field_template_name = "forms/question/field.html"


class StartForm(forms.Form):
    registration_number = forms.CharField(widget=forms.TextInput(attrs={"class": "input w-full"}))

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["renderer"] = QuestionRenderer()
        self.key = kwargs.pop("key", None)
        super().__init__(*args, **kwargs)

    def clean_registration_number(self) -> Household:
        try:
            guard = RegistrationAttemptGuard(self.cleaned_data["registration_number"])
            if guard.is_locked_out():
                raise FlowLockoutError(guard.get_lockout_message())
            return Household.objects.get(detail_id=self.cleaned_data["registration_number"])
        except Household.DoesNotExist:
            raise forms.ValidationError("Registration number not found") from None


class QuestionForm(forms.Form):
    question = forms.CharField(
        label="Question", max_length=100, widget=forms.TextInput(attrs={"class": "input w-full"})
    )
    signed = forms.CharField(label="Signed", widget=forms.HiddenInput)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["renderer"] = QuestionRenderer()
        self.key = kwargs.pop("key", None)
        super().__init__(*args, **kwargs)

    def sign(self, k: str, v: str) -> str:
        return signing.TimestampSigner().sign_object([k, v])

    def unsign(self, key: str) -> tuple[str, str]:
        return signing.TimestampSigner().unsign_object(key)

    def check_value(self) -> bool:
        signer = signing.TimestampSigner()
        try:
            data = signer.unsign_object(self.cleaned_data["signed"])
            return str(data[1]).lower() == str(self.cleaned_data["question"]).lower()
        except signing.BadSignature:
            return False


class QuestionBaseFormSet(forms.BaseFormSet[QuestionForm]):
    pass


QuestionFormSet = forms.formset_factory(QuestionForm, formset=QuestionBaseFormSet, extra=0)
