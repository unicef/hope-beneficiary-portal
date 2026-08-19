import uuid

from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from hope_portal.modules.hope.models import Household


def household_key(household: Household) -> str:
    """Return a stable hex household id whether Django gave us a UUID or a hex string."""
    return uuid.UUID(str(household.id)).hex


class Beneficiary(models.Model):
    username = models.CharField(_("username"), max_length=150, unique=True)
    household_id = models.CharField(_("household id"), max_length=150, unique=True)
    password = models.CharField(_("password"), max_length=128)
    last_login = models.DateTimeField(_("last login"), blank=True, null=True)
    suspended = models.BooleanField(_("suspended"), default=False)

    def __str__(self) -> str:
        return self.username

    @cached_property
    def household(self) -> Household:
        return Household.objects.get(id=self.household_id)

    def link_to(self, hh: Household) -> None:
        self.household_id = household_key(hh)
        self.save()
        if "household" in self.__dict__:
            delattr(self, "household")

    @classmethod
    def for_household(cls, household: Household) -> "Beneficiary | None":
        return cls.objects.filter(household_id=household_key(household)).first()

    @classmethod
    def set_credentials(cls, household: Household, username: str, raw_password: str) -> "Beneficiary":
        beneficiary = cls.for_household(household)
        if beneficiary is None:
            beneficiary = cls(household_id=household_key(household), username=username)
        else:
            beneficiary.username = username
        beneficiary.set_password(raw_password)
        beneficiary.save()
        return beneficiary

    def set_password(self, raw_password: str) -> None:
        self.password = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        def setter(raw_password: str) -> None:
            self.set_password(raw_password)
            self.save(update_fields=["password"])

        return check_password(raw_password, self.password, setter)
