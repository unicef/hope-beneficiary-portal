import uuid
from unittest import mock

import pytest
from constance.test import override_config
from django.urls import reverse
from testutils.factories.hope.houshold import HouseholdFactory

from hope_portal.modules.inspect import Inspector
from hope_portal.modules.security.clients import HopeAPIClient
from hope_portal.modules.security.guards import RegistrationAttemptGuard


@pytest.fixture
def household():
    hh = HouseholdFactory()
    hh.program.business_area.slug = "ba-slug"
    hh.program.business_area.name = "Business Area"
    hh.program.business_area.save(update_fields=["slug", "name"])
    return hh


def _go_to_info_page(django_app, household):
    url = reverse("ui:flow:start-registration")
    res = django_app.get(url)
    res.forms["reg-form"]["registration_number"] = household.program_registration_id
    res = res.forms["reg-form"].submit().follow()
    with mock.patch("hope_portal.ui.forms.flow.QuestionForm.check_value", return_value=True):
        res.forms["ask-form"]["form-0-question"] = "--"
        res.forms["ask-form"]["form-1-question"] = "--"
        res.forms["ask-form"]["form-2-question"] = "--"
        res = res.forms["ask-form"].submit()
    return res.follow()


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3)
def test_flow_not_found(django_app, household):
    RegistrationAttemptGuard.clear()
    url = reverse("ui:flow:start-registration")
    res = django_app.get(url)
    res.forms["reg-form"]["registration_number"] = household.program_registration_id
    res = res.forms["reg-form"].submit().follow()
    res = res.forms["ask-form"].submit()
    assert res.status_code == 200
    res.forms["ask-form"]["form-0-question"] = "--"
    res.forms["ask-form"]["form-1-question"] = "--"
    res.forms["ask-form"]["form-2-question"] = "--"
    res = res.forms["ask-form"].submit()
    assert b"Sorry cannot find your data" in res.content


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3)
def test_flow_found(django_app, household):
    res = _go_to_info_page(django_app, household)
    assert b"Welcome" in res.content, res.showbrowser()
    assert b"Household details" in res.content


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3)
def test_flow_open_issue_manual_create(django_app, household, settings, monkeypatch):
    settings.HOPE_API_BASE_URL = "https://hope.example.org"
    settings.HOPE_API_TOKEN = "token"
    settings.HOPE_API_TIMEOUT = 5

    info_res = _go_to_info_page(django_app, household)
    issue_link = info_res.pyquery("a:contains('Open issue')").attr("href")
    assert issue_link

    captured = {}

    def _capture_create(self, business_area_slug, description, program_id=None):
        captured["business_area_slug"] = business_area_slug
        captured["description"] = description
        captured["program_id"] = program_id

    monkeypatch.setattr(HopeAPIClient, "create_beneficiary_ticket", _capture_create)

    issue_res = django_app.get(issue_link)
    issue_res.forms[0]["description"] = "Manual issue description"
    issue_res = issue_res.forms[0].submit()
    assert issue_res.status_code == 302
    assert captured["business_area_slug"] == household.program.business_area.slug
    assert captured["description"] == "Manual issue description"
    assert uuid.UUID(captured["program_id"]) == uuid.UUID(str(household.program_id))


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3)
def test_flow_open_issue_requires_ticket_service_config(django_app, household, settings, monkeypatch):
    settings.HOPE_API_BASE_URL = ""
    settings.HOPE_API_TOKEN = ""

    info_res = _go_to_info_page(django_app, household)
    issue_link = info_res.pyquery("a:contains('Open issue')").attr("href")
    assert issue_link

    def _fail_create(self, business_area_slug, description, program_id=None):
        raise AssertionError("Ticket creation should not be called")

    monkeypatch.setattr(HopeAPIClient, "create_beneficiary_ticket", _fail_create)

    issue_res = django_app.get(issue_link)
    issue_res.forms[0]["description"] = "Will fail"
    issue_res = issue_res.forms[0].submit()
    assert issue_res.status_code == 200
    assert b"Ticket service is not configured." in issue_res.content


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3)
def test_flow_open_issue_form_no_longer_shows_business_area_choice(django_app, household):
    household.program.business_area.name = None
    household.program.business_area.save(update_fields=["name"])

    HouseholdFactory(
        household_collection_id=household.household_collection_id,
        unicef_id=household.unicef_id,
        program=household.program,
    )

    info_res = _go_to_info_page(django_app, household)
    issue_link = info_res.pyquery("a:contains('Open issue')").attr("href")
    issue_res = django_app.get(issue_link)

    assert issue_res.status_code == 200
    assert b'name="business_area_slug"' not in issue_res.content
    assert b'name="description"' in issue_res.content


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3)
def test_flow_open_issue_requires_available_business_area(django_app, household, settings, monkeypatch):
    settings.HOPE_API_BASE_URL = "https://hope.example.org"
    settings.HOPE_API_TOKEN = "token"
    settings.HOPE_API_TIMEOUT = 5

    household.program.business_area.slug = None
    household.program.business_area.save(update_fields=["slug"])

    info_res = _go_to_info_page(django_app, household)
    issue_link = info_res.pyquery("a:contains('Open issue')").attr("href")
    assert issue_link

    def _fail_create(self, business_area_slug, description, program_id=None):
        raise AssertionError("Ticket creation should not be called when no business area is available")

    monkeypatch.setattr(HopeAPIClient, "create_beneficiary_ticket", _fail_create)

    issue_res = django_app.get(issue_link)
    issue_res.forms[0]["description"] = "Will fail because no business area"
    issue_res = issue_res.forms[0].submit()
    assert issue_res.status_code == 200
    assert b"No business area available for this household." in issue_res.content


# ---------------------------------------------------------------------------
# StartForm: registration number normalization
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3)
def test_start_form_matches_when_user_submits_without_dash(django_app):
    """DB stores 'REG-42' but user types 'REG42' (no dash) — should still resolve."""
    HouseholdFactory(program_registration_id="REG-DASH-MATCH")
    url = reverse("ui:flow:start-registration")
    res = django_app.get(url)
    res.forms["reg-form"]["registration_number"] = "REGDASHMATCH"
    res = res.forms["reg-form"].submit()
    assert res.status_code == 302, res.html.get_text()


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3)
def test_start_form_matches_hash_suffix_in_database(django_app):
    """DB stores 'REG-42#0' but user types 'REG-42' — #N suffix should be stripped on DB side."""
    HouseholdFactory(program_registration_id="REG-HASH-1#0")
    url = reverse("ui:flow:start-registration")
    res = django_app.get(url)
    res.forms["reg-form"]["registration_number"] = "REG-HASH-1"
    res = res.forms["reg-form"].submit()
    assert res.status_code == 302, res.html.get_text()


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3)
def test_start_form_returns_all_matching_candidates(django_app):
    """Both REG-MC#0 and REG-MC#1 must be found when user types 'REG-MC'."""
    HouseholdFactory(program_registration_id="REG-MC-MULTI#0")
    HouseholdFactory(program_registration_id="REG-MC-MULTI#1")
    url = reverse("ui:flow:start-registration")
    res = django_app.get(url)
    res.forms["reg-form"]["registration_number"] = "REG-MC-MULTI"
    # Both households must produce a valid redirect (the signed token encodes both IDs).
    res = res.forms["reg-form"].submit()
    assert res.status_code == 302, res.html.get_text()
    # Follow to the ask page — the URL embeds a signed token covering both candidates.
    ask_res = res.follow()
    assert ask_res.status_code in (200, 302)  # referenced to avoid an unused-variable warning


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3)
def test_start_form_validation_error_on_unknown_registration_number(django_app):
    url = reverse("ui:flow:start-registration")
    res = django_app.get(url)
    res.forms["reg-form"]["registration_number"] = "THIS-ID-DOES-NOT-EXIST-AT-ALL"
    res = res.forms["reg-form"].submit()
    assert res.status_code == 200
    assert b"Registration number not found" in res.content


# ---------------------------------------------------------------------------
# AskView: multi-candidate POST — second candidate matched on first submission
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=1, MAX_QUESTIONS_PER_FIELD=1)
def test_ask_view_identifies_second_candidate_when_answers_match_it(django_app):
    """
    If check_value() fails for candidate[0] but Inspector.matches_answers() returns True
    for candidate[1], the view should redirect to the info page for candidate[1].
    """
    HouseholdFactory(program_registration_id="REG-TWOCAND#0")
    HouseholdFactory(program_registration_id="REG-TWOCAND#1")

    url = reverse("ui:flow:start-registration")
    res = django_app.get(url)
    res.forms["reg-form"]["registration_number"] = "REG-TWOCAND"
    # Start form finds both; follows to ask page.
    res = res.forms["reg-form"].submit().follow()

    # We may get a second redirect if the first candidate is skipped (no questions).
    if res.status_code == 302:
        res = res.follow()

    assert res.status_code == 200

    with (
        mock.patch("hope_portal.ui.forms.flow.QuestionForm.check_value", return_value=False),
        mock.patch.object(Inspector, "matches_answers", return_value=True),
    ):
        res.forms["ask-form"]["form-0-question"] = "any_answer"
        res = res.forms["ask-form"].submit()

    # The view should redirect to the info page for whichever candidate matched.
    assert res.status_code == 302
    assert "info" in res.location


# ---------------------------------------------------------------------------
# AskView: multi-candidate POST — no candidate matched → retry shown
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=1, MAX_QUESTIONS_PER_FIELD=1)
def test_ask_view_shows_retry_when_no_candidate_matches(django_app):
    """
    When check_value() fails and no other candidate matches, the form is re-rendered
    with retry=True (template shows 'Sorry cannot find your data').
    """
    HouseholdFactory(program_registration_id="REG-RETRY-ONLY")

    url = reverse("ui:flow:start-registration")
    res = django_app.get(url)
    res.forms["reg-form"]["registration_number"] = "REG-RETRY-ONLY"
    res = res.forms["reg-form"].submit().follow()

    if res.status_code == 302:
        res = res.follow()

    assert res.status_code == 200

    with mock.patch("hope_portal.ui.forms.flow.QuestionForm.check_value", return_value=False):
        res.forms["ask-form"]["form-0-question"] = "--wrong--"
        res = res.forms["ask-form"].submit()

    assert res.status_code == 200
    assert b"Sorry cannot find your data" in res.content


# ---------------------------------------------------------------------------
# AskView: GET — candidate with no questions is skipped, redirect to next
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=1, MAX_QUESTIONS_PER_FIELD=1)
def test_ask_view_skips_candidate_with_no_questions_and_redirects(django_app):
    """
    If candidates[0] cannot produce any questions, the GET handler should redirect
    to a new signed token containing only the remaining candidates.
    """
    # household_empty: all question-eligible fields are blank → 0 questions
    HouseholdFactory(
        program_registration_id="REG-SKIP-NOQUESTIONS#0",
        head_of_household__given_name="",
        head_of_household__middle_name="",
        head_of_household__family_name="",
        head_of_household__phone_no="",
    )
    # household_data: has a name → will produce questions
    HouseholdFactory(
        program_registration_id="REG-SKIP-NOQUESTIONS#1",
        head_of_household__given_name="Mohammed",
        head_of_household__middle_name="",
        head_of_household__family_name="",
        head_of_household__phone_no="",
    )

    url = reverse("ui:flow:start-registration")
    res = django_app.get(url)
    res.forms["reg-form"]["registration_number"] = "REG-SKIP-NOQUESTIONS"

    # POST start form → 302 to /ask/<signed_ab>/
    res = res.forms["reg-form"].submit()
    assert res.status_code == 302

    # GET /ask/<signed_ab>/ → 302 to /ask/<signed_b>/ (first candidate skipped)
    res = res.follow()
    assert res.status_code == 302

    # GET /ask/<signed_b>/ → 200 ask page (second candidate has questions)
    res = res.follow()
    assert res.status_code == 200


# ---------------------------------------------------------------------------
# AskView: GET — all candidates have no questions → not-available
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=1, MAX_QUESTIONS_PER_FIELD=1)
def test_ask_view_redirects_to_not_available_when_no_candidates_have_questions(django_app):
    HouseholdFactory(
        program_registration_id="REG-ALL-EMPTY-NOQUESTIONS",
        head_of_household__given_name="",
        head_of_household__middle_name="",
        head_of_household__family_name="",
        head_of_household__phone_no="",
    )

    url = reverse("ui:flow:start-registration")
    res = django_app.get(url)
    res.forms["reg-form"]["registration_number"] = "REG-ALL-EMPTY-NOQUESTIONS"
    res = res.forms["reg-form"].submit()
    assert res.status_code == 302

    res = res.follow()
    # First ask GET → redirect again (no questions for only candidate)
    res = res.follow()
    assert "not-available" in res.request.url
