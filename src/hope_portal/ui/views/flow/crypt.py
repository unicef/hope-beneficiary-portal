from django.core import signing
from django.http import HttpRequest

from hope_portal.exception import FlowTimeoutError
from hope_portal.modules.hope.models import Household


def get_signer(request: HttpRequest, extra: str = "") -> signing.TimestampSigner:
    session_key = request.session.session_key
    session_salt = f"s:{session_key}:{extra}"
    return signing.TimestampSigner(salt=session_salt)


def sign_household(request: HttpRequest, hh: Household) -> str:
    signer = get_signer(request)
    return signer.sign_object({"hh_id": str(hh.id)})


def unsign_household(request: HttpRequest, key: str, max_age: int = 60) -> Household:
    signer = get_signer(request)
    try:
        data = signer.unsign_object(key, max_age=max_age)
        return Household.objects.get(pk=data["hh_id"])
    except (signing.BadSignature, Household.DoesNotExist):
        raise FlowTimeoutError() from None
