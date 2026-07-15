from django.db.models import TextChoices


class VerificationField(TextChoices):
    DOB = "dob", "Birth date"
    GIVEN_NAME = "given_name", "Given name"
    MIDDLE_NAME = "middle_name", "Middle name"
    LAST_NAME = "last_name", "Last name"
    PHONE = "phone", "Phone number"
    PHONE_ALT = "phone_alt", "Alternative phone number"
    FIRST_REGISTRATION_DATE = "first_registration_date", "First registration date"
    IBAN = "iban", "IBAN / account number"
    ADMIN_AREA1 = "admin_area1", "Administrative area (Admin Level 1)"
    ADMIN_AREA2 = "admin_area2", "Administrative area (Admin Level 2)"
    ADMIN_AREA3 = "admin_area3", "Administrative area (Admin Level 3)"
    ADMIN_AREA4 = "admin_area4", "Administrative area (Admin Level 4)"


_NAME_FIELDS = frozenset({VerificationField.GIVEN_NAME, VerificationField.MIDDLE_NAME, VerificationField.LAST_NAME})

DEFAULT_ENABLED_VERIFICATION_FIELDS: list[str] = [
    field.value for field in VerificationField if field not in _NAME_FIELDS
]
