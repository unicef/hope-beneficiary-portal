import pytest
from constance.test import override_config
from django.core.cache import cache
from django.utils import timezone

from hope_portal.modules.inspect import ADMIN1, ADMIN2, HEAD, HOUSEHOLD, MIDDLE_NAME, PHONE, Inspector, _digits_only
from hope_portal.utils.verification_fields import VerificationField
from testutils.factories.hope.houshold import HouseholdFactory

ALL_VERIFICATION_FIELDS = VerificationField.values
FIELDS_WITHOUT_NAMES = [
    key
    for key in ALL_VERIFICATION_FIELDS
    if key not in (VerificationField.GIVEN_NAME, VerificationField.MIDDLE_NAME, VerificationField.LAST_NAME)
]


def _household_with_only_given_name(given_name: str) -> object:
    """Create a household whose head has only a given name — no other question-eligible fields."""
    return HouseholdFactory(
        head_of_household__given_name=given_name,
        head_of_household__middle_name="",
        head_of_household__family_name="",
        head_of_household__phone_no="",
    )


@pytest.mark.django_db
def test_collect_information_skips_blank_middle_name():
    household = HouseholdFactory(head_of_household__middle_name="   ")

    inspector = Inspector(household)

    assert HEAD + MIDDLE_NAME not in inspector.infos


@pytest.mark.django_db
def test_collect_per_person_questions_skips_blank_cached_values():
    household = HouseholdFactory()
    cache_key = Inspector(household)._cache_key()
    cache.set(cache_key, {HEAD + MIDDLE_NAME: "   "}, timeout=60)
    inspector = Inspector(household)

    assert inspector._collect_per_person_questions(1) == []


@pytest.mark.django_db
def test_cache_key_changes_when_middle_name_changes():
    household = HouseholdFactory(head_of_household__middle_name="OldMiddle")

    inspector = Inspector(household)
    old_key = inspector._cache_key()
    cache.set(old_key, {HEAD + MIDDLE_NAME: "OldMiddle"}, timeout=60)

    household.head_of_household.middle_name = ""
    household.head_of_household.updated_at = timezone.now()
    household.head_of_household.save(update_fields=["middle_name", "updated_at"])

    refreshed = Inspector(household)

    assert refreshed._cache_key() != old_key
    assert HEAD + MIDDLE_NAME not in refreshed.infos


# phone number digit extraction — spaces/formatting must not shift digit positions


def test_digits_only_strips_plus_spaces_and_punctuation():
    assert _digits_only("+48 609 456 123") == "48609456123"
    assert _digits_only("+1 (555) 123-4567") == "15551234567"


@pytest.mark.django_db
def test_collect_person_data_stores_phone_as_digits_only():
    household = HouseholdFactory(head_of_household__phone_no="+48 609 456 001")
    inspector = Inspector(household)
    assert inspector.infos[HEAD + PHONE] == "48609456001"


# VERIFICATION_ENABLED_FIELDS — admins choose exactly which fields are askable;
# given/middle/last name are excluded from the default set (data-quality concerns).


@pytest.mark.django_db
@override_config(VERIFICATION_ENABLED_FIELDS=FIELDS_WITHOUT_NAMES)
def test_name_questions_excluded_when_not_in_enabled_fields():
    household = _household_with_only_given_name("Arsen")
    assert Inspector(household)._collect_all_questions() == []
    assert Inspector(household).build_answer_map() == {}


@pytest.mark.django_db
@override_config(VERIFICATION_ENABLED_FIELDS=["given_name"])
def test_name_questions_included_when_selected():
    household = _household_with_only_given_name("Arsen")
    questions = Inspector(household)._collect_all_questions()
    assert len(questions) == 5
    assert {q.answer for q in questions} == set("Arsen")


@pytest.mark.django_db
@override_config(VERIFICATION_ENABLED_FIELDS=["phone"])
def test_only_selected_fields_are_used_even_if_others_have_data():
    household = HouseholdFactory(head_of_household__given_name="Arsen", head_of_household__phone_no="+48123456789")
    answer_map = Inspector(household).build_answer_map()
    assert answer_map
    assert set(answer_map.values()) <= set("48123456789")


# All fields enabled below so these generic-mechanics tests keep using "given name" as their
# vehicle field, independent of VERIFICATION_ENABLED_FIELDS.


@pytest.mark.django_db
@override_config(VERIFICATION_ENABLED_FIELDS=ALL_VERIFICATION_FIELDS)
def test_collect_all_questions_returns_every_position_for_given_name():
    household = _household_with_only_given_name("Arsen")
    questions = Inspector(household)._collect_all_questions()
    assert len(questions) == 5
    assert {q.answer for q in questions} == set("Arsen")


@pytest.mark.django_db
@override_config(VERIFICATION_ENABLED_FIELDS=ALL_VERIFICATION_FIELDS)
def test_collect_all_questions_empty_household_returns_empty():
    household = _household_with_only_given_name("")
    assert Inspector(household)._collect_all_questions() == []


@pytest.mark.django_db
@override_config(VERIFICATION_ENABLED_FIELDS=ALL_VERIFICATION_FIELDS)
def test_build_answer_map_contains_entry_for_every_position():
    household = _household_with_only_given_name("Arsen")
    answer_map = Inspector(household).build_answer_map()
    assert len(answer_map) == 5
    assert set(answer_map.values()) == set("Arsen")


@pytest.mark.django_db
@override_config(VERIFICATION_ENABLED_FIELDS=ALL_VERIFICATION_FIELDS)
def test_build_answer_map_is_keyed_by_question_text():
    household = _household_with_only_given_name("AB")
    answer_map = Inspector(household).build_answer_map()
    for text, answer in answer_map.items():
        assert isinstance(text, str)
        assert answer in "AB"


@pytest.mark.django_db
@override_config(VERIFICATION_ENABLED_FIELDS=ALL_VERIFICATION_FIELDS)
def test_matches_answers_true_for_correct_answers():
    household = _household_with_only_given_name("Arsen")
    inspector = Inspector(household)
    answer_map = inspector.build_answer_map()
    question_text, correct_answer = next(iter(answer_map.items()))
    assert inspector.matches_answers([(question_text, correct_answer)])


@pytest.mark.django_db
@override_config(VERIFICATION_ENABLED_FIELDS=ALL_VERIFICATION_FIELDS)
def test_matches_answers_true_case_insensitive():
    household = _household_with_only_given_name("Arsen")
    inspector = Inspector(household)
    answer_map = inspector.build_answer_map()
    question_text, correct_answer = next(iter(answer_map.items()))
    assert inspector.matches_answers([(question_text, correct_answer.upper())])


@pytest.mark.django_db
@override_config(VERIFICATION_ENABLED_FIELDS=ALL_VERIFICATION_FIELDS)
def test_matches_answers_false_for_wrong_answer():
    household = _household_with_only_given_name("Arsen")
    inspector = Inspector(household)
    answer_map = inspector.build_answer_map()
    question_text, _ = next(iter(answer_map.items()))
    assert not inspector.matches_answers([(question_text, "WRONG")])


@pytest.mark.django_db
def test_matches_answers_false_for_unknown_question():
    household = _household_with_only_given_name("Arsen")
    inspector = Inspector(household)
    assert not inspector.matches_answers([("A question that does not exist?", "anything")])


@pytest.mark.django_db
def test_matches_answers_empty_list_returns_false():
    """An empty asked list must not be treated as 'all correct' — explicit guard against all([]) == True."""
    household = _household_with_only_given_name("Arsen")
    assert not Inspector(household).matches_answers([])


# Administrative area — all admin levels (1-4) are collected, not a single configured level,
# so each question explicitly names which level it refers to.


def test_admin_label_names_the_level_explicitly():
    assert Inspector._admin_label(1) == "Administrative area (Admin Level 1)"
    assert Inspector._admin_label(2) == "Administrative area (Admin Level 2)"
    assert Inspector._admin_label(4) == "Administrative area (Admin Level 4)"


@pytest.mark.django_db
def test_collect_household_data_has_no_admin_entries_when_areas_unset():
    """HouseholdFactory doesn't set admin1-admin4, so no bogus admin-area questions appear."""
    household = _household_with_only_given_name("Arsen")
    assert Inspector(household)._collect_household_data() == {}


@pytest.mark.django_db
@override_config(VERIFICATION_ENABLED_FIELDS=["admin_area1"])
def test_only_selected_admin_level_produces_questions():
    """Each admin level (admin_area1..4) is independently toggleable in VERIFICATION_ENABLED_FIELDS."""
    household = _household_with_only_given_name("Arsen")
    cache.set(
        Inspector(household)._cache_key(),
        {HOUSEHOLD + ADMIN1: "Kyiv", HOUSEHOLD + ADMIN2: "Oblast"},
        timeout=60,
    )
    answer_map = Inspector(household).build_answer_map()
    assert answer_map
    assert set(answer_map.values()) <= set("Kyiv")


@pytest.mark.django_db
@override_config(
    MIN_QUESTIONS=1, MAX_QUESTIONS=3, MAX_QUESTIONS_PER_FIELD=3, VERIFICATION_ENABLED_FIELDS=ALL_VERIFICATION_FIELDS
)
def test_get_questions_single_candidate_returns_random_sample():
    household = _household_with_only_given_name("Arsen")
    questions = Inspector(household).get_questions()
    assert 1 <= len(questions) <= 3


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=10, MAX_QUESTIONS=20, MAX_QUESTIONS_PER_FIELD=1)
def test_get_questions_below_min_returns_empty():
    household = _household_with_only_given_name("Arsen")
    assert Inspector(household).get_questions() == []


@pytest.mark.django_db
@override_config(
    MIN_QUESTIONS=1, MAX_QUESTIONS=5, MAX_QUESTIONS_PER_FIELD=5, VERIFICATION_ENABLED_FIELDS=ALL_VERIFICATION_FIELDS
)
def test_get_questions_includes_discriminating_question_for_two_candidates():
    household_a = _household_with_only_given_name("Arsen")
    household_b = _household_with_only_given_name("Artem")

    questions = Inspector(household_a).get_questions(other_candidates=[household_b])

    answer_map_b = Inspector(household_b).build_answer_map()
    assert any(answer_map_b.get(question.question, "").lower() != question.answer.lower() for question in questions)


@pytest.mark.django_db
@override_config(
    MIN_QUESTIONS=1, MAX_QUESTIONS=5, MAX_QUESTIONS_PER_FIELD=5, VERIFICATION_ENABLED_FIELDS=ALL_VERIFICATION_FIELDS
)
def test_get_discriminating_question_set_covers_all_pairs():
    # Arsen vs Artem vs Artom vs Arson — two discriminating positions needed.
    household_arsen = _household_with_only_given_name("Arsen")
    household_artem = _household_with_only_given_name("Artem")
    household_artom = _household_with_only_given_name("Artom")
    household_arson = _household_with_only_given_name("Arson")

    others = [household_artem, household_artom, household_arson]
    questions = Inspector(household_arsen).get_questions(other_candidates=others)

    for other in others:
        answer_map = Inspector(other).build_answer_map()
        assert any(
            answer_map.get(question.question, "").lower() != question.answer.lower() for question in questions
        ), f"{other.head_of_household.given_name!r} is not discriminated by the question set"


@pytest.mark.django_db
@override_config(
    MIN_QUESTIONS=1, MAX_QUESTIONS=5, MAX_QUESTIONS_PER_FIELD=5, VERIFICATION_ENABLED_FIELDS=ALL_VERIFICATION_FIELDS
)
def test_get_questions_indistinguishable_candidates_logs_debug(caplog):
    import logging

    household_a = _household_with_only_given_name("Same")
    household_b = _household_with_only_given_name("Same")

    with caplog.at_level(logging.DEBUG, logger="hope_portal.modules.inspect"):
        Inspector(household_a).get_questions(other_candidates=[household_b])

    assert any("indistinguishable" in record.message for record in caplog.records)
