import factory
from factory import PostGenerationMethodCall

from hope_portal.models.beneficiary import Beneficiary, household_key

from .base import AutoRegisterModelFactory
from .hope.houshold import HouseholdFactory


class BeneficiaryFactory(AutoRegisterModelFactory):
    username = factory.Sequence(lambda n: f"beneficiary-{n}")
    household = factory.SubFactory(HouseholdFactory)
    household_id = factory.LazyAttribute(lambda o: household_key(o.household))
    password = PostGenerationMethodCall("set_password", "PortalLogin-42!")

    class Meta:
        model = Beneficiary
        exclude = ("household",)
