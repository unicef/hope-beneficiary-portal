import uuid

import factory

from hope_portal.modules.hope.models import Program

from ..base import AutoRegisterModelFactory
from .businessarea import BusinessAreaFactory


class ProgramFactory(AutoRegisterModelFactory):
    id = factory.Sequence(lambda n: uuid.uuid4().hex)
    business_area = factory.SubFactory(BusinessAreaFactory)

    class Meta:
        model = Program
