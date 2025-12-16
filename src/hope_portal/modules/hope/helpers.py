from django.contrib.auth.models import User
from hope_portal.modules.hope.models import HopeUser


def retrieve_hope_user(user: User | None = None) -> HopeUser | None:
    if not user:
        return None

    hope_user = None
    if user.email:
        hope_user = HopeUser.objects.using("hope_ro").filter(email=user.email).first()

    if user.username:
        hope_user = HopeUser.objects.using("hope_ro").filter(username=user.username).first()

    return hope_user
