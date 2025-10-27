import uuid

import factory

from hope_portal.modules.hope.models import BusinessArea

from ..base import AutoRegisterModelFactory


class BusinessAreaFactory(AutoRegisterModelFactory):
    id = factory.Sequence(lambda n: uuid.uuid4().hex)

    class Meta:
        model = BusinessArea
