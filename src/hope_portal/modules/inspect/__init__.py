import logging
import random
from typing import Any

from constance import config
from django.core.cache import cache
from django.utils.translation import gettext as _

from hope_portal.modules.hope.models import Household, Individual
from hope_portal.modules.inspect.extractors import DateExtractor, LetterExtractor, PhoneNumberExtractor, QuestionData

logger = logging.getLogger(__name__)

HEAD = 100
PRIMARY_COLLECTOR = 200

DOB = 1
GIVEN_NAME = 2
LAST_NAME = 3
PHONE = 4

HEAD_DOB = HEAD + DOB
HEAD_GIVEN_NAME = HEAD + GIVEN_NAME
HEAD_LAST_NAME = HEAD + LAST_NAME
HEAD_PHONE = HEAD + PHONE

PRIMARY_COLLECTOR_DOB = PRIMARY_COLLECTOR + DOB
PRIMARY_COLLECTOR_GIVEN_NAME = PRIMARY_COLLECTOR + GIVEN_NAME
PRIMARY_COLLECTOR_LAST_NAME = PRIMARY_COLLECTOR + LAST_NAME
PRIMARY_COLLECTOR_PHONE = PRIMARY_COLLECTOR + PHONE


class Inspector:
    def __init__(self, hh: Household) -> None:
        self.household = hh
        self.infos = self.collect_information()

    def _collect_person_data(self, person: Individual, offset: int) -> dict[int, Any]:
        infos: dict[int, Any] = {}
        if person.birth_date and not person.estimated_birth_date:
            infos[offset + DOB] = person.birth_date
        if person.given_name:
            infos[offset + GIVEN_NAME] = person.given_name
        if person.family_name:
            infos[offset + LAST_NAME] = person.family_name
        if person.phone_no:
            infos[offset + PHONE] = person.phone_no[1:]
        return infos

    def collect_information(self) -> dict[int, Any]:
        infos: dict[int, Any]
        infos = cache.get(f"infos:{self.household.detail_id}")
        if not infos:
            infos = {}
            if head := self.household.head_of_household:
                infos.update(self._collect_person_data(head, HEAD))
            if pc := self.household.primary_collector:  # type: ignore[attr-defined]
                infos.update(self._collect_person_data(pc, PRIMARY_COLLECTOR))
            cache.set(f"infos:{self.household.detail_id}", infos, timeout=config.CACHE_QUESTIONS_TIMEOUT)
        return infos

    def get_questions(self) -> list[QuestionData]:
        ret = []
        for target_idx, label in [(HEAD, _("Head of Household")), (PRIMARY_COLLECTOR, _("Primary Collector"))]:
            if (target_idx + DOB) in self.infos:
                ret.append(DateExtractor(_(f"{label} Birth date"), self.infos[(target_idx + DOB)]).get_question())
            if (target_idx + GIVEN_NAME) in self.infos:
                ret.append(
                    LetterExtractor(_(f"{label} Given name"), self.infos[(target_idx + GIVEN_NAME)]).get_question()
                )
            if (target_idx + LAST_NAME) in self.infos:
                ret.append(
                    LetterExtractor(_(f"{label} Last name"), self.infos[(target_idx + LAST_NAME)]).get_question()
                )
            if (target_idx + PHONE) in self.infos:
                ret.append(
                    PhoneNumberExtractor(_(f"{label} Phone number"), self.infos[(target_idx + PHONE)]).get_question()
                )
        if len(ret) < config.MIN_QUESTIONS:
            logger.debug(
                f"Not available question ({len(ret)}) to proceed with identification. (min. {config.MIN_QUESTIONS})"
            )
            return []
        return random.sample(ret, min(config.MAX_QUESTIONS, len(ret)))
