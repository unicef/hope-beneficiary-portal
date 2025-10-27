from typing import Any

from django.core import signing
from django.core.signing import SignatureExpired
from django.http import HttpRequest

from hope_portal.exception import FlowTimeoutError
from hope_portal.modules.hope.models import Household


def get_signer(request: HttpRequest, extra: str = "") -> signing.TimestampSigner:
    session_key = request.session.session_key
    session_salt = f"s:{session_key}:{extra}"
    return signing.TimestampSigner(salt=session_salt)


def sign(request: HttpRequest, value: Any) -> str:
    signer = get_signer(request)
    return signer.sign_object(value)


def unsign(request: HttpRequest, value: Any, max_age: int = 60) -> Any:
    signer = get_signer(request)
    try:
        return signer.unsign_object(value, max_age=max_age)
    except (signing.BadSignature, Household.DoesNotExist, SignatureExpired):
        raise FlowTimeoutError() from None


def sign_household(request: HttpRequest, hh: Household) -> str:
    return sign(request, {"id": str(hh.id)})


def unsign_household(request: HttpRequest, key: str) -> Household:
    try:
        value = unsign(request, key)
        return Household.objects.get(pk=value["id"])
    except (signing.BadSignature, Household.DoesNotExist):
        raise FlowTimeoutError() from None
