from django.utils.translation import gettext as _

from hope_portal.modules.hope.models import Household
from hope_portal.modules.inspect.extractors import DateExtractor, LetterExtractor, PhoneNumberExtractor, QuestionData


class Inspector:
    def __init__(self, hh: Household) -> None:
        self.household = hh

    def get_questions(self) -> list[QuestionData]:
        ret = []
        head = self.household.head_of_household
        if head:
            if head.birth_date and not head.estimated_birth_date:
                ret.append(DateExtractor(_("Birth date"), head.birth_date).get_question())
            if head.given_name:
                ret.append(LetterExtractor(_("Given Name"), head.given_name).get_question())
            if head.family_name:
                ret.append(LetterExtractor(_("Family Name"), head.family_name).get_question())
            if head.phone_no:
                ret.append(PhoneNumberExtractor(_("Phone number"), head.phone_no[1:]).get_question())
        return ret
