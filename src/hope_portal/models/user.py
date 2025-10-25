from unicef_security.models import AbstractUser, SecurityMixin


class User(SecurityMixin, AbstractUser):  # type: ignore[misc]
    class Meta:
        abstract = False
