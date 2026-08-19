import re
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import phonenumbers
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core import signing
from django.core.exceptions import ValidationError
from django.db.models import CharField, Func, Value
from django.db.models.functions import Replace
from django.forms.renderers import DjangoTemplates
from phonenumbers import NumberParseException

from hope_portal.exception import FlowLockoutError
from hope_portal.models.beneficiary import Beneficiary
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
                "autocomplete": "username",
                "placeholder": " ",
            }
        ),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "input w-full",
                "autocomplete": "current-password",
                "placeholder": " ",
            }
        ),
    )


class AccountCredentialsForm(BaseForm):
    username = forms.CharField(
        min_length=3,
        max_length=150,
        validators=[UnicodeUsernameValidator()],
        widget=forms.TextInput(
            attrs={
                "class": "input w-full",
                "autofocus": True,
                "autocomplete": "username",
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
    password_confirm = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(
            attrs={
                "class": "input w-full",
                "autocomplete": "new-password",
                "placeholder": " ",
            }
        ),
    )

    def __init__(self, *args: Any, instance: Beneficiary | None = None, **kwargs: Any) -> None:
        self.instance = instance
        super().__init__(*args, **kwargs)
        if instance is not None:
            self.fields["password"].label = "New password"
            self.fields["password_confirm"].label = "Confirm new password"

    def clean_username(self) -> str:
        username = self.cleaned_data["username"]
        qs = Beneficiary.objects.filter(username=username)
        if self.instance is not None and self.instance.pk is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        username = cleaned_data.get("username")
        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Passwords do not match.")
        if password:
            try:
                validate_password(password, user=SimpleNamespace(username=username or ""))
            except ValidationError as exc:
                self.add_error("password", exc)
        return cleaned_data


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

    def sign(self, question_text: str) -> str:
        """Sign the question text for tamper-detection. The expected answer is kept server-side."""
        return signing.TimestampSigner().sign_object(question_text)

    def unsign(self, signed_value: str) -> str:
        """Return the signed question text, raising BadSignature if tampered."""
        return signing.TimestampSigner().unsign_object(signed_value)

    def check_value(self, expected_answer: str) -> bool:
        """Verify the signed question is untampered, then compare the answer."""
        try:
            signing.TimestampSigner().unsign_object(self.cleaned_data["signed"])
        except signing.BadSignature:
            return False
        return str(expected_answer).lower() == str(self.cleaned_data["question"]).lower()


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
