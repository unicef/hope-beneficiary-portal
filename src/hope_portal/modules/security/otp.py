import secrets
import string

from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from twilio.rest import Client


def generate_otp(length: int = 6) -> str:
    otp = "".join(secrets.choice(string.digits) for _ in range(length))
    return signing.dumps(otp, salt="otp", compress=True)


def validate_otp(token: str) -> str | None:
    try:
        return signing.loads(token, salt="otp", max_age=settings.OTP_VALIDITY_MINUTES / 60)
    except signing.BadSignature:
        return None


def send_otp_sms(to_phone_number: str, otp: str) -> bool:
    if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_FROM_NUMBER]):
        return False

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message_body = _("Your OTP is: {otp}. It is valid for {minutes} minutes.").format(
        otp=otp, minutes=settings.OTP_VALIDITY_MINUTES
    )
    client.messages.create(body=message_body, from_=settings.TWILIO_FROM_NUMBER, to=to_phone_number)
    return True


def store_otp(phone_number: str, otp: str) -> None:
    cache_key = f"otp_{phone_number}"
    cache.set(cache_key, otp, settings.OTP_VALIDITY_MINUTES * 60)


def verify_otp(phone_number: str, otp_attempt: str) -> bool:
    cache_key = f"otp_{phone_number}"
    stored_otp = cache.get(cache_key)
    if stored_otp and stored_otp == otp_attempt:
        cache.delete(cache_key)  # OTP is one-time use
        return True
    return False
