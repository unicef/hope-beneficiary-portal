import uuid

import factory.fuzzy

from hope_portal.modules.hope.models import Payment

from ..base import AutoRegisterModelFactory
from .businessarea import BusinessAreaFactory
from .houshold import HouseholdFactory, IndividualFactory


class PaymentFactory(AutoRegisterModelFactory):
    id = factory.Sequence(lambda n: uuid.uuid4().hex)
    business_area = factory.SubFactory(BusinessAreaFactory)
    head_of_household = factory.SubFactory(IndividualFactory)
    household = factory.SubFactory(HouseholdFactory)
    parent = None
    financial_service_provider = None
    collector = factory.SubFactory(IndividualFactory)
    source_payment = None
    delivery_type = None

    class Meta:
        model = Payment
