import pytest
from django.core.cache import cache
from django.utils import timezone

from hope_portal.modules.inspect import HEAD, MIDDLE_NAME, Inspector
from testutils.factories.hope.houshold import HouseholdFactory


@pytest.mark.django_db
def test_collect_information_skips_blank_middle_name():
    household = HouseholdFactory(head_of_household__middle_name="   ")

    inspector = Inspector(household)

    assert HEAD + MIDDLE_NAME not in inspector.infos


@pytest.mark.django_db
def test_collect_per_person_questions_skips_blank_cached_values():
    household = HouseholdFactory()
    inspector = Inspector(household)
    cache.set(inspector._cache_key(), {HEAD + MIDDLE_NAME: "   "}, timeout=60)

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
