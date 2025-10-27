import factory

from hope_portal.modules.hope.models import GrievanceticketPrograms

from ..base import AutoRegisterModelFactory
from .program import ProgramFactory


class GrievanceticketProgramsFactory(AutoRegisterModelFactory):
    program = factory.SubFactory(ProgramFactory)

    class Meta:
        model = GrievanceticketPrograms
