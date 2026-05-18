import pytest
from django.core.cache import cache

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
    cache.set(f"infos:{household.detail_id}", {HEAD + MIDDLE_NAME: "   "}, timeout=60)

    inspector = Inspector(household)

    assert inspector._collect_per_person_questions(1) == []
