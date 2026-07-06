import uuid

import factory.fuzzy

from hope_portal.modules.hope.models import Household, Individual, Individualroleinhousehold

from ..base import AutoRegisterModelFactory
from .program import ProgramFactory

RELATIONSHIPS = (
    "Unknown",
    "Aunt / Uncle",
    "Brother / Sister",
    "Cousin",
    "Daughter-in-law / Son-in-law",
    "Granddaughter / Grandson",
    "Grandmother / Grandfather",
    "Mother / Father",
)

RELATIONSHIP_CHOICE = list(zip(RELATIONSHIPS, RELATIONSHIPS, strict=True))


class HouseholdRoleFactory(AutoRegisterModelFactory):
    class Meta:
        model = Individualroleinhousehold


class HouseholdFactory(AutoRegisterModelFactory):
    id = factory.Sequence(lambda n: uuid.uuid4().hex)
    unicef_id = factory.Sequence(lambda n: f"HH-{n}")
    size = factory.fuzzy.FuzzyInteger(3, 8)
    head_of_household = factory.SubFactory("testutils.factories.IndividualFactory")
    program_registration_id = factory.Sequence(lambda n: f"REG-{n}")
    program = factory.SubFactory(ProgramFactory)

    class Meta:
        model = Household

    @factory.post_generation
    def create_linked_item(self: Household, create, extracted, **kwargs):
        if not create or not self.head_of_household:
            return
        self.head_of_household.household = self
        self.head_of_household.save()


class IndividualFactory(AutoRegisterModelFactory):
    id = factory.Sequence(lambda n: uuid.uuid4().hex)
    full_name = factory.LazyAttribute(lambda o: f"{o.given_name} {o.middle_name} {o.family_name}")
    given_name = factory.Faker("first_name")
    middle_name = factory.Faker("first_name")
    family_name = factory.Faker("last_name")
    phone_no = factory.Sequence(lambda n: f"+48 609 456 {n % 1000:03d}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    relationship = factory.fuzzy.FuzzyChoice([value for value, label in RELATIONSHIP_CHOICE[1:] if value != "HEAD"])
    household = None

    class Meta:
        model = Individual
