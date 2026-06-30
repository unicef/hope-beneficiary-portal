import re
from typing import TYPE_CHECKING, Any

import phonenumbers
from django import forms
from django.core import signing
from django.db.models import CharField, Func, Value
from django.db.models.functions import Replace
from django.forms.renderers import DjangoTemplates
from phonenumbers import NumberParseException

from hope_portal.exception import FlowLockoutError
from hope_portal.modules.hope.models import Household
from hope_portal.modules.security.guards import RegistrationAttemptGuard

if TYPE_CHECKING:
    from phonenumbers.phonenumber import PhoneNumber


class _RegexpReplace(Func):
    """PostgreSQL REGEXP_REPLACE(source, pattern, replacement)."""

    function = "REGEXP_REPLACE"
    output_field = CharField()


class QuestionRenderer(DjangoTemplates):
    field_template_name = "forms/question/field.html"


def validate_phonenumber(value: Any) -> None:
    try:
        parsed: PhoneNumber = phonenumbers.parse(value)
        if not phonenumbers.is_valid_number(parsed):
            raise forms.ValidationError("Invalid phone number")
    except NumberParseException:
        raise forms.ValidationError("Invalid phone number") from None


class BaseForm(forms.Form):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["renderer"] = QuestionRenderer()
        super().__init__(*args, **kwargs)


class SMSForm(BaseForm):
    number = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "input w-full",
                "autofocus": True,
                "autocomplete": "off",
                "placeholder": " ",
            }
        ),
        validators=[validate_phonenumber],
    )


class EmailForm(BaseForm):
    email = forms.EmailField(
        widget=forms.TextInput(
            attrs={
                "class": "input w-full",
                "autofocus": True,
                "autocomplete": "off",
                "placeholder": " ",
            }
        ),
    )


class OTPForm(BaseForm):
    otp = forms.CharField(
        min_length=6,
        max_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "input w-full",
                "autofocus": True,
                "autocomplete": "one-time-code",
                "inputmode": "numeric",
            }
        ),
    )


class AuthForm(BaseForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "input w-full",
                "autofocus": True,
                "autocomplete": "new-password",
                "placeholder": " ",
            }
        ),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "input w-full",
                "autocomplete": "new-password",
                "placeholder": " ",
            }
        ),
    )


class StartForm(BaseForm):
    registration_number = forms.CharField(
        widget=forms.TextInput(attrs={"class": "input w-full", "autofocus": True, "placeholder": " "})
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.key = kwargs.pop("key", None)
        super().__init__(*args, **kwargs)

    def clean_registration_number(self) -> list[Household]:
        registration_number = self.cleaned_data["registration_number"]
        guard = RegistrationAttemptGuard(registration_number)
        if guard.is_locked_out():
            raise FlowLockoutError(guard.get_lockout_message())

        registration_number_normalized = re.sub(r"#\d+$", "", re.sub(r"[-\s]", "", registration_number.strip()))

        program_registration_id_no_dashes = Replace(
            Replace("program_registration_id", Value("-"), Value("")),
            Value(" "),
            Value(""),
        )
        program_registration_id_normalized = _RegexpReplace(
            program_registration_id_no_dashes,
            Value(r"#[0-9]+$"),
            Value(""),
        )

        candidates = list(
            Household.objects.annotate(_normalized_program_registration_id=program_registration_id_normalized)
            .filter(_normalized_program_registration_id=registration_number_normalized)
            .order_by("-created_at")
        )
        if not candidates:
            raise forms.ValidationError("Registration number not found")
        return candidates


class QuestionForm(forms.Form):
    question = forms.CharField(
        label="Question",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "input w-full", "autocomplete": "off", "placeholder": " "}),
    )
    signed = forms.CharField(label="Signed", widget=forms.HiddenInput)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["renderer"] = QuestionRenderer()
        self.key = kwargs.pop("key", None)
        super().__init__(*args, **kwargs)

    def sign(self, question_text: str, answer: str) -> str:
        return signing.TimestampSigner().sign_object([question_text, answer])

    def unsign(self, signed_value: str) -> tuple[str, str]:
        return signing.TimestampSigner().unsign_object(signed_value)

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


class TicketCreateForm(BaseForm):
    description = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "input w-full",
                "rows": 4,
                "placeholder": "Describe your issue...",
                "autofocus": True,
            }
        ),
        max_length=2000,
    )
