import logging
import random
from hashlib import sha256
from typing import Any

from constance import config
from django.core.cache import cache
from django.utils.translation import gettext as _

from hope_portal.modules.hope.models import Account, Household, Individual
from hope_portal.modules.inspect.extractors import (
    DateExtractor,
    Extractor,
    IbanExtractor,
    LetterExtractor,
    PhoneNumberExtractor,
    QuestionData,
)

logger = logging.getLogger(__name__)

HEAD = 100
PRIMARY_COLLECTOR = 200
HOUSEHOLD = 300

DOB = 1
GIVEN_NAME = 2
LAST_NAME = 3
PHONE = 4
IBAN = 5
MIDDLE_NAME = 6
PHONE_ALT = 7
FIRST_REG = 8

ADMIN2 = 10

HEAD_DOB = HEAD + DOB
HEAD_GIVEN_NAME = HEAD + GIVEN_NAME
HEAD_LAST_NAME = HEAD + LAST_NAME
HEAD_PHONE = HEAD + PHONE

PRIMARY_COLLECTOR_DOB = PRIMARY_COLLECTOR + DOB
PRIMARY_COLLECTOR_GIVEN_NAME = PRIMARY_COLLECTOR + GIVEN_NAME
PRIMARY_COLLECTOR_LAST_NAME = PRIMARY_COLLECTOR + LAST_NAME
PRIMARY_COLLECTOR_PHONE = PRIMARY_COLLECTOR + PHONE

IBAN_ACCOUNT_TYPE_KEYS = ("bank", "iban")


def _normalize_str(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
    return value


def _has_question_value(value: Any) -> bool:
    return bool(_normalize_str(value))


class Inspector:
    def __init__(self, hh: Household) -> None:
        self.household = hh
        self.infos = self.collect_information()

    def _get_individual_iban(self, person: Individual) -> str | None:
        account = (
            Account.objects.filter(
                individual=person,
                active=True,
                account_type__key__in=IBAN_ACCOUNT_TYPE_KEYS,
            )
            .exclude(number__isnull=True)
            .exclude(number__exact="")
            .order_by("-updated_at")
            .first()
        )
        return account.number if account else None

    def _collect_person_data(self, person: Individual, offset: int) -> dict[int, Any]:
        infos: dict[int, Any] = {}
        if person.birth_date and not person.estimated_birth_date:
            infos[offset + DOB] = person.birth_date
        if _has_question_value(person.given_name):
            infos[offset + GIVEN_NAME] = _normalize_str(person.given_name)
        if _has_question_value(person.middle_name):
            infos[offset + MIDDLE_NAME] = _normalize_str(person.middle_name)
        if _has_question_value(person.family_name):
            infos[offset + LAST_NAME] = _normalize_str(person.family_name)
        if _has_question_value(person.phone_no):
            phone_no = _normalize_str(person.phone_no)
            infos[offset + PHONE] = phone_no.removeprefix("+")
        if _has_question_value(person.phone_no_alternative):
            phone_no_alternative = _normalize_str(person.phone_no_alternative)
            infos[offset + PHONE_ALT] = phone_no_alternative.removeprefix("+")
        if person.first_registration_date:
            infos[offset + FIRST_REG] = person.first_registration_date
        if iban := self._get_individual_iban(person):
            iban = _normalize_str(iban)
            if iban:
                infos[offset + IBAN] = iban
        return infos

    def _collect_household_data(self) -> dict[int, Any]:
        infos: dict[int, Any] = {}
        admin2 = getattr(self.household, "admin2", None)
        admin2_name = _normalize_str(getattr(admin2, "name", None))
        if admin2 and admin2_name:
            infos[HOUSEHOLD + ADMIN2] = admin2_name
        return infos

    def _person_cache_parts(self, person: Individual | None) -> tuple[str, ...]:
        if not person:
            return ("",)
        iban = _normalize_str(self._get_individual_iban(person)) or ""
        return (
            str(person.birth_date or ""),
            str(bool(person.estimated_birth_date)),
            str(_normalize_str(person.given_name) or ""),
            str(_normalize_str(person.middle_name) or ""),
            str(_normalize_str(person.family_name) or ""),
            str(_normalize_str(person.phone_no) or ""),
            str(_normalize_str(person.phone_no_alternative) or ""),
            str(person.first_registration_date or ""),
            str(iban),
        )

    def _cache_key(self) -> str:
        head = self.household.head_of_household
        primary_collector = self.household.primary_collector  # type: ignore[attr-defined]
        admin2_name = _normalize_str(getattr(getattr(self.household, "admin2", None), "name", None)) or ""
        cache_fingerprint = "\x1f".join(
            (
                str(self.household.detail_id),
                *self._person_cache_parts(head),
                *self._person_cache_parts(primary_collector),
                str(admin2_name),
            )
        )
        digest = sha256(cache_fingerprint.encode("utf-8")).hexdigest()
        return f"infos:{self.household.detail_id}:{digest}"

    def collect_information(self) -> dict[int, Any]:
        infos: dict[int, Any]
        cache_key = self._cache_key()
        infos = cache.get(cache_key)
        if not infos:
            infos = {}
            if head := self.household.head_of_household:
                infos.update(self._collect_person_data(head, HEAD))
            if pc := self.household.primary_collector:  # type: ignore[attr-defined]
                infos.update(self._collect_person_data(pc, PRIMARY_COLLECTOR))
            infos.update(self._collect_household_data())
            cache.set(cache_key, infos, timeout=config.CACHE_QUESTIONS_TIMEOUT)
        return infos

    _PERSON_FIELDS: tuple[tuple[int, str, type[Extractor]], ...] = (
        (DOB, "{label} Birth date", DateExtractor),
        (GIVEN_NAME, "{label} Given name", LetterExtractor),
        (MIDDLE_NAME, "{label} Middle name", LetterExtractor),
        (LAST_NAME, "{label} Last name", LetterExtractor),
        (PHONE, "{label} Phone number", PhoneNumberExtractor),
        (PHONE_ALT, "{label} Alternative phone number", PhoneNumberExtractor),
        (FIRST_REG, "{label} First registration date", DateExtractor),
        (IBAN, "{label} IBAN / account number", IbanExtractor),
    )

    _PERSON_ROLES: tuple[tuple[int, str], ...] = (
        (HEAD, "Head of Household"),
        (PRIMARY_COLLECTOR, "Primary Collector"),
    )

    def _collect_per_person_questions(self, per_field: int) -> list[QuestionData]:
        ret: list[QuestionData] = []
        for offset, role_label in self._PERSON_ROLES:
            role_label_tr = _(role_label)
            for field_key, label_tpl, extractor_cls in self._PERSON_FIELDS:
                value = _normalize_str(self.infos.get(offset + field_key))
                if not value:
                    continue
                label = _(label_tpl).format(label=role_label_tr)
                ret.extend(extractor_cls(label, value).get_questions(per_field))
        return ret

    def _collect_household_questions(self, per_field: int) -> list[QuestionData]:
        ret: list[QuestionData] = []
        value = _normalize_str(self.infos.get(HOUSEHOLD + ADMIN2))
        if value:
            ret.extend(LetterExtractor(_("Administrative area"), value).get_questions(per_field))
        return ret

    def get_questions(self) -> list[QuestionData]:
        per_field = max(1, int(config.MAX_QUESTIONS_PER_FIELD))
        ret = self._collect_per_person_questions(per_field) + self._collect_household_questions(per_field)
        if len(ret) < config.MIN_QUESTIONS:
            logger.debug(
                f"Not available question ({len(ret)}) to proceed with identification. (min. {config.MIN_QUESTIONS})"
            )
            return []
        return random.sample(ret, min(config.MAX_QUESTIONS, len(ret)))
