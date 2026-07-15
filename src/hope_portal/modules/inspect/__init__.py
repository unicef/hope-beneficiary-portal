import logging
import random
import re
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
from hope_portal.utils.verification_fields import VerificationField

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

ADMIN1 = 10
ADMIN2 = 11
ADMIN3 = 12
ADMIN4 = 13

ADMIN_LEVEL_KEYS: dict[int, int] = {1: ADMIN1, 2: ADMIN2, 3: ADMIN3, 4: ADMIN4}

HEAD_DOB = HEAD + DOB
HEAD_GIVEN_NAME = HEAD + GIVEN_NAME
HEAD_LAST_NAME = HEAD + LAST_NAME
HEAD_PHONE = HEAD + PHONE

PRIMARY_COLLECTOR_DOB = PRIMARY_COLLECTOR + DOB
PRIMARY_COLLECTOR_GIVEN_NAME = PRIMARY_COLLECTOR + GIVEN_NAME
PRIMARY_COLLECTOR_LAST_NAME = PRIMARY_COLLECTOR + LAST_NAME
PRIMARY_COLLECTOR_PHONE = PRIMARY_COLLECTOR + PHONE

IBAN_ACCOUNT_TYPE_KEYS = ("bank", "iban")

# Maps each selectable VERIFICATION_ENABLED_FIELDS key (see hope_portal.utils.verification_fields)
# to the internal per-person field key it gates. Admin levels aren't per-person fields — they're
# handled separately via ADMIN_AREA_SELECT_KEYS, one selectable key per level.
_PERSON_FIELD_SELECT_KEYS: dict[int, str] = {
    DOB: VerificationField.DOB.value,
    GIVEN_NAME: VerificationField.GIVEN_NAME.value,
    MIDDLE_NAME: VerificationField.MIDDLE_NAME.value,
    LAST_NAME: VerificationField.LAST_NAME.value,
    PHONE: VerificationField.PHONE.value,
    PHONE_ALT: VerificationField.PHONE_ALT.value,
    FIRST_REG: VerificationField.FIRST_REGISTRATION_DATE.value,
    IBAN: VerificationField.IBAN.value,
}
ADMIN_AREA_SELECT_KEYS: dict[int, str] = {
    1: VerificationField.ADMIN_AREA1.value,
    2: VerificationField.ADMIN_AREA2.value,
    3: VerificationField.ADMIN_AREA3.value,
    4: VerificationField.ADMIN_AREA4.value,
}

_expected_select_keys = set(_PERSON_FIELD_SELECT_KEYS.values()) | set(ADMIN_AREA_SELECT_KEYS.values())
_actual_select_keys = set(VerificationField.values)
if _actual_select_keys != _expected_select_keys:
    raise ValueError(
        "VerificationField is out of sync with Inspector's field mapping: "
        f"expected {_expected_select_keys!r}, got {_actual_select_keys!r}"
    )


def _normalize_str(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
    return value


def _has_question_value(value: Any) -> bool:
    return bool(_normalize_str(value))


_NON_DIGIT_RE = re.compile(r"\D")


def _digits_only(value: str) -> str:
    return _NON_DIGIT_RE.sub("", value)


class Inspector:
    def __init__(self, household: Household) -> None:
        self.household = household
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
            infos[offset + PHONE] = _digits_only(_normalize_str(person.phone_no))
        if _has_question_value(person.phone_no_alternative):
            infos[offset + PHONE_ALT] = _digits_only(_normalize_str(person.phone_no_alternative))
        if person.first_registration_date:
            infos[offset + FIRST_REG] = person.first_registration_date
        if iban := self._get_individual_iban(person):
            iban = _normalize_str(iban)
            if iban:
                infos[offset + IBAN] = iban
        return infos

    @staticmethod
    def _admin_label(level: int) -> str:
        return _("Administrative area (Admin Level {level})").format(level=level)

    @staticmethod
    def _enabled_fields() -> frozenset[str]:
        try:
            return frozenset(config.VERIFICATION_ENABLED_FIELDS)
        except TypeError:
            return frozenset()

    def _collect_household_data(self) -> dict[int, Any]:
        infos: dict[int, Any] = {}
        for level, key in ADMIN_LEVEL_KEYS.items():
            admin = getattr(self.household, f"admin{level}", None)
            admin_name = _normalize_str(getattr(admin, "name", None))
            if admin and admin_name:
                infos[HOUSEHOLD + key] = admin_name
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

    def _admin_cache_parts(self) -> tuple[str, ...]:
        return tuple(
            str(_normalize_str(getattr(getattr(self.household, f"admin{level}", None), "name", None)) or "")
            for level in ADMIN_LEVEL_KEYS
        )

    def _cache_key(self) -> str:
        head = self.household.head_of_household
        primary_collector = self.household.primary_collector  # type: ignore[attr-defined]
        cache_fingerprint = "\x1f".join(
            (
                str(self.household.program_registration_id),
                *self._person_cache_parts(head),
                *self._person_cache_parts(primary_collector),
                *self._admin_cache_parts(),
            )
        )
        digest = sha256(cache_fingerprint.encode("utf-8")).hexdigest()
        return f"infos:{self.household.program_registration_id}:{digest}"

    def collect_information(self) -> dict[int, Any]:
        infos: dict[int, Any]
        cache_key = self._cache_key()
        infos = cache.get(cache_key)
        if not infos:
            infos = {}
            if head := self.household.head_of_household:
                infos.update(self._collect_person_data(head, HEAD))
            if primary_collector := self.household.primary_collector:  # type: ignore[attr-defined]
                infos.update(self._collect_person_data(primary_collector, PRIMARY_COLLECTOR))
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
        questions: list[QuestionData] = []
        enabled_fields = self._enabled_fields()
        for offset, role_label in self._PERSON_ROLES:
            for field_key, label_tpl, extractor_cls in self._PERSON_FIELDS:
                if _PERSON_FIELD_SELECT_KEYS[field_key] not in enabled_fields:
                    continue
                value = _normalize_str(self.infos.get(offset + field_key))
                if not value:
                    continue
                label = _(label_tpl).format(label=_(role_label))
                questions.extend(extractor_cls(label, value).get_questions(per_field))
        return questions

    def _collect_household_questions(self, per_field: int) -> list[QuestionData]:
        questions: list[QuestionData] = []
        enabled_fields = self._enabled_fields()
        for level, key in ADMIN_LEVEL_KEYS.items():
            if ADMIN_AREA_SELECT_KEYS[level] not in enabled_fields:
                continue
            value = _normalize_str(self.infos.get(HOUSEHOLD + key))
            if value:
                questions.extend(LetterExtractor(self._admin_label(level), value).get_questions(per_field))
        return questions

    def _collect_all_questions(self) -> list[QuestionData]:
        questions: list[QuestionData] = []
        enabled_fields = self._enabled_fields()
        for offset, role_label in self._PERSON_ROLES:
            for field_key, label_tpl, extractor_cls in self._PERSON_FIELDS:
                if _PERSON_FIELD_SELECT_KEYS[field_key] not in enabled_fields:
                    continue
                value = _normalize_str(self.infos.get(offset + field_key))
                if not value:
                    continue
                label = _(label_tpl).format(label=_(role_label))
                questions.extend(extractor_cls(label, value).iter_all_questions())
        for level, key in ADMIN_LEVEL_KEYS.items():
            if ADMIN_AREA_SELECT_KEYS[level] not in enabled_fields:
                continue
            value = _normalize_str(self.infos.get(HOUSEHOLD + key))
            if value:
                questions.extend(LetterExtractor(self._admin_label(level), value).iter_all_questions())
        return questions

    def get_questions(self, other_candidates: list["Household"] | None = None) -> list[QuestionData]:
        per_field = max(1, int(config.MAX_QUESTIONS_PER_FIELD))
        sampled = self._collect_per_person_questions(per_field) + self._collect_household_questions(per_field)
        if len(sampled) < config.MIN_QUESTIONS:
            logger.debug(
                f"Not enough questions ({len(sampled)}) to proceed with identification. (min. {config.MIN_QUESTIONS})"
            )
            return []

        max_questions = min(config.MAX_QUESTIONS, len(sampled))

        if not other_candidates:
            return random.sample(sampled, max_questions)

        return self._get_discriminating_question_set(sampled, other_candidates, max_questions)

    def _get_discriminating_question_set(
        self,
        sampled: list[QuestionData],
        other_candidates: list["Household"],
        max_questions: int,
    ) -> list[QuestionData]:
        other_answer_maps = [Inspector(candidate).build_answer_map() for candidate in other_candidates]

        unique_questions: dict[str, QuestionData] = {
            question.question: question for question in self._collect_all_questions()
        }
        question_coverage: dict[str, frozenset[int]] = {
            text: frozenset(
                index
                for index, other_map in enumerate(other_answer_maps)
                if other_map.get(text, "").lower() != question.answer.lower()
            )
            for text, question in unique_questions.items()
        }

        uncovered: set[int] = set(range(len(other_candidates)))
        guaranteed: list[QuestionData] = []
        used_texts: set[str] = set()

        while uncovered and len(guaranteed) < max_questions:
            best = max(
                (question for question in unique_questions.values() if question.question not in used_texts),
                key=lambda question: len(question_coverage[question.question] & uncovered),
                default=None,
            )
            if best is None:
                break
            newly_covered = question_coverage[best.question] & uncovered
            if not newly_covered:
                break
            guaranteed.append(best)
            used_texts.add(best.question)
            uncovered -= newly_covered

        if uncovered:
            logger.debug(
                f"{len(uncovered)} candidate(s) indistinguishable by available questions; "
                "falling back to post-submission matching."
            )

        remaining_pool = [question for question in sampled if question.question not in used_texts]
        remaining = random.sample(remaining_pool, min(max_questions - len(guaranteed), len(remaining_pool)))

        result = guaranteed + remaining
        random.shuffle(result)
        return result

    def build_answer_map(self) -> dict[str, str]:
        answer_map: dict[str, str] = {}
        enabled_fields = self._enabled_fields()
        for offset, role_label in self._PERSON_ROLES:
            for field_key, label_tpl, extractor_cls in self._PERSON_FIELDS:
                if _PERSON_FIELD_SELECT_KEYS[field_key] not in enabled_fields:
                    continue
                value = _normalize_str(self.infos.get(offset + field_key))
                if not value:
                    continue
                label = _(label_tpl).format(label=_(role_label))
                extractor = extractor_cls(label, value)
                for question_data in extractor.iter_all_questions():
                    answer_map[question_data.question] = question_data.answer

        for level, key in ADMIN_LEVEL_KEYS.items():
            if ADMIN_AREA_SELECT_KEYS[level] not in enabled_fields:
                continue
            value = _normalize_str(self.infos.get(HOUSEHOLD + key))
            if value:
                for question_data in LetterExtractor(self._admin_label(level), value).iter_all_questions():
                    answer_map[question_data.question] = question_data.answer

        return answer_map

    def matches_answers(self, asked: list[tuple[str, str]]) -> bool:
        if not asked:
            return False
        answer_map = self.build_answer_map()
        return all(
            answer_map.get(question_text, "").lower() == user_answer.lower() for question_text, user_answer in asked
        )
