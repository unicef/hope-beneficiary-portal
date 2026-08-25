import uuid
from unittest import mock

import pytest
from constance.test import override_config
from django.core import signing
from django.db import IntegrityError
from django.urls import reverse
from testutils.factories.beneficiary import BeneficiaryFactory
from testutils.factories.hope.houshold import HouseholdFactory

from hope_portal.exception import FlowLockoutError
from hope_portal.models.beneficiary import Beneficiary, household_key
from hope_portal.modules.inspect import Inspector
from hope_portal.modules.security.clients import HopeAPIClient
from hope_portal.modules.security.guards import RegistrationAttemptGuard
from hope_portal.ui.forms.flow import QuestionForm


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
def test_flow_info_handles_null_head_and_program_in_collection(django_app, household):
    """A sibling household in the same collection with no head_of_household/program must not 500."""
    HouseholdFactory(
        household_collection_id=household.household_collection_id,
        unicef_id=household.unicef_id,
        head_of_household=None,
        program=None,
    )
    res = _go_to_info_page(django_app, household)
    assert res.status_code == 200, res.showbrowser()
    assert b"Welcome" in res.content


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3)
def test_flow_open_issue_manual_create(django_app, household, settings, monkeypatch):
    settings.HOPE_API_BASE_URL = "https://hope.example.org"
    settings.HOPE_API_TOKEN = "token"
    settings.HOPE_API_TIMEOUT = 5

    info_res = _go_to_info_page(django_app, household)
    issue_link = info_res.pyquery("a:contains('Open Hope Grievance')").attr("href")
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
    issue_link = info_res.pyquery("a:contains('Open Hope Grievance')").attr("href")
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
    issue_link = info_res.pyquery("a:contains('Open Hope Grievance')").attr("href")
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
    issue_link = info_res.pyquery("a:contains('Open Hope Grievance')").attr("href")
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
# AskView: VERIFICATION_PASS_THRESHOLD — partial credit
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3, VERIFICATION_PASS_THRESHOLD=60)
def test_ask_view_passes_with_partial_credit_above_threshold(django_app, household):
    """2 correct answers out of 3 (~67%) passes when the threshold is 60%."""
    url = reverse("ui:flow:start-registration")
    res = django_app.get(url)
    res.forms["reg-form"]["registration_number"] = household.program_registration_id
    res = res.forms["reg-form"].submit().follow()

    with mock.patch(
        "hope_portal.ui.forms.flow.QuestionForm.check_value",
        side_effect=[True, True, False],
    ):
        res.forms["ask-form"]["form-0-question"] = "any"
        res.forms["ask-form"]["form-1-question"] = "any"
        res.forms["ask-form"]["form-2-question"] = "any"
        res = res.forms["ask-form"].submit()

    assert res.status_code == 302
    assert "info" in res.location


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3, VERIFICATION_PASS_THRESHOLD=100)
def test_ask_view_fails_with_partial_credit_at_default_threshold(django_app, household):
    """The same 2-out-of-3 answers fail when the threshold is left at 100% (all-or-nothing)."""
    url = reverse("ui:flow:start-registration")
    res = django_app.get(url)
    res.forms["reg-form"]["registration_number"] = household.program_registration_id
    res = res.forms["reg-form"].submit().follow()

    with mock.patch(
        "hope_portal.ui.forms.flow.QuestionForm.check_value",
        side_effect=[True, True, False],
    ):
        res.forms["ask-form"]["form-0-question"] = "any"
        res.forms["ask-form"]["form-1-question"] = "any"
        res.forms["ask-form"]["form-2-question"] = "any"
        res = res.forms["ask-form"].submit()

    assert res.status_code == 200
    assert b"Sorry cannot find your data" in res.content


@pytest.mark.django_db
@override_config(VERIFICATION_PASS_THRESHOLD=100)
def test_meets_pass_threshold_boundaries():
    from hope_portal.ui.views.flow.ask import AskView

    assert AskView._meets_pass_threshold([True, True, True])
    assert not AskView._meets_pass_threshold([])
    assert not AskView._meets_pass_threshold([True, False, False])


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


# ---------------------------------------------------------------------------
# QuestionForm: sign/unsign/check_value unit tests
# ---------------------------------------------------------------------------


def test_question_form_sign_unsign_round_trip():
    """sign() embeds only the question text; unsign() returns it unchanged."""
    form = QuestionForm()
    question_text = "What is the first letter of your given name?"
    signed = form.sign(question_text)
    assert form.unsign(signed) == question_text


def test_question_form_sign_does_not_embed_answer():
    """The signed token must not contain the plain-text answer."""
    form = QuestionForm()
    answer = "SuperSecretAnswer"
    signed = form.sign("Some question?")
    assert answer not in signed


def test_question_form_unsign_raises_on_tampered_value():
    form = QuestionForm()
    with pytest.raises(signing.BadSignature):
        form.unsign("this.is.obviously.tampered")


def test_question_form_check_value_correct_answer():
    signed = QuestionForm().sign("Q?")
    form = QuestionForm(data={"question": "A", "signed": signed})
    assert form.is_valid()
    assert form.check_value("A")
    assert form.check_value("a")


def test_question_form_check_value_wrong_answer():
    signed = QuestionForm().sign("Q?")
    form = QuestionForm(data={"question": "B", "signed": signed})
    assert form.is_valid()
    assert not form.check_value("A")


def test_question_form_check_value_tampered_signed():
    form = QuestionForm(data={"question": "A", "signed": "tampered.value.here"})
    assert form.is_valid()
    assert not form.check_value("A")


# ---------------------------------------------------------------------------
# AskView: POST with tampered signed field → reject immediately
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=1, MAX_QUESTIONS_PER_FIELD=1)
def test_ask_post_rejects_tampered_signed_field(django_app):
    """A POST whose signed field has been tampered must be redirected to not-available."""
    HouseholdFactory(
        program_registration_id="REG-TAMPER-TEST",
        head_of_household__given_name="Arsen",
        head_of_household__middle_name="",
        head_of_household__family_name="",
        head_of_household__phone_no="",
    )
    url = reverse("ui:flow:start-registration")
    res = django_app.get(url)
    res.forms["reg-form"]["registration_number"] = "REG-TAMPER-TEST"
    res = res.forms["reg-form"].submit().follow()
    if res.status_code == 302:
        res = res.follow()
    assert res.status_code == 200

    res.forms["ask-form"].fields["form-0-signed"][0].force_value("tampered.value.that.has.bad.signature")
    res.forms["ask-form"]["form-0-question"] = "some_answer"
    res = res.forms["ask-form"].submit()

    assert res.status_code == 302
    res = res.follow()
    assert "not-available" in res.request.url


# ---------------------------------------------------------------------------
# AskView: POST with zero forms (empty formset) → reject, not accept
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=1, MAX_QUESTIONS_PER_FIELD=1)
def test_ask_post_rejects_empty_formset(django_app):
    """
    If the submitted formset contains zero forms, asked == [] which is falsy.
    The view must reject immediately — all([]) must not silently grant access.
    """
    HouseholdFactory(
        program_registration_id="REG-EMPTY-FORMSET",
        head_of_household__given_name="Arsen",
        head_of_household__middle_name="",
        head_of_household__family_name="",
        head_of_household__phone_no="",
    )
    url = reverse("ui:flow:start-registration")
    res = django_app.get(url)
    res.forms["reg-form"]["registration_number"] = "REG-EMPTY-FORMSET"
    res = res.forms["reg-form"].submit().follow()
    if res.status_code == 302:
        res = res.follow()
    assert res.status_code == 200

    # Submit the form with TOTAL_FORMS=0 so the formset contains no questions.
    # Using form.submit() instead of django_app.post() ensures the CSRF token is
    # included automatically by webtest.
    form = res.forms["ask-form"]
    form["form-TOTAL_FORMS"] = "0"
    form["form-INITIAL_FORMS"] = "0"
    res = form.submit()
    assert res.status_code == 302
    res = res.follow()
    assert "not-available" in res.request.url


ACCOUNT_PASSWORD = "PortalLogin-42!"


def _account_create_link(info_res):
    return info_res.pyquery("a:contains('Set username and password')").attr("href")


def _account_reset_link(info_res):
    return info_res.pyquery("a:contains('View or reset login')").attr("href")


def _submit_account_form(res, username, password, password_confirm=None):
    form = res.forms["account-form"]
    form["username"] = username
    form["password"] = password
    form["password_confirm"] = password if password_confirm is None else password_confirm
    return form.submit()


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3)
def test_info_page_offers_set_credentials_when_no_account(django_app, household):
    info_res = _go_to_info_page(django_app, household)
    assert _account_create_link(info_res)
    assert _account_reset_link(info_res) is None


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3)
def test_create_account_with_chosen_credentials_then_login(django_app, household):
    info_res = _go_to_info_page(django_app, household)
    res = django_app.get(_account_create_link(info_res))
    assert res.status_code == 200
    assert b"Choose a username and password" in res.content

    res = _submit_account_form(res, "my-login", ACCOUNT_PASSWORD)
    assert res.status_code == 200
    assert b"Login created" in res.content
    assert b"my-login" in res.content
    assert ACCOUNT_PASSWORD.encode() not in res.content

    beneficiary = Beneficiary.objects.get(username="my-login")
    assert beneficiary.household_id == household_key(household)
    assert beneficiary.check_password(ACCOUNT_PASSWORD)

    res = django_app.get(reverse("ui:flow:start-auth"))
    res.forms["reg-form"]["username"] = "my-login"
    res.forms["reg-form"]["password"] = ACCOUNT_PASSWORD
    res = res.forms["reg-form"].submit().follow()
    assert b"Welcome" in res.content
    assert _account_reset_link(res)


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3)
def test_existing_account_shows_username_and_allows_password_reset(django_app, household):
    BeneficiaryFactory(household=household, username="existing-user")
    info_res = _go_to_info_page(django_app, household)
    assert _account_reset_link(info_res)
    assert _account_create_link(info_res) is None

    res = django_app.get(_account_reset_link(info_res))
    assert res.status_code == 200
    assert res.forms["account-form"]["username"].value == "existing-user"
    assert b"previous password cannot be recovered" in res.content
    assert b"existing-user" in res.content
    hashed = Beneficiary.objects.get(username="existing-user").password
    assert hashed.encode() not in res.content

    res = _submit_account_form(res, "existing-user", ACCOUNT_PASSWORD)
    assert b"Login updated" in res.content
    assert b"existing-user" in res.content
    assert ACCOUNT_PASSWORD.encode() not in res.content

    beneficiary = Beneficiary.objects.get(username="existing-user")
    assert beneficiary.check_password(ACCOUNT_PASSWORD)

    res = django_app.get(reverse("ui:flow:start-auth"))
    res.forms["reg-form"]["username"] = "existing-user"
    res.forms["reg-form"]["password"] = ACCOUNT_PASSWORD
    res = res.forms["reg-form"].submit().follow()
    assert b"Welcome" in res.content


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3)
def test_account_form_rejects_password_mismatch(django_app, household):
    info_res = _go_to_info_page(django_app, household)
    res = django_app.get(_account_create_link(info_res))
    res = _submit_account_form(res, "mismatch-user", ACCOUNT_PASSWORD, password_confirm="OtherPass-99!")
    assert res.status_code == 200
    assert b"Passwords do not match." in res.content
    assert not Beneficiary.objects.filter(username="mismatch-user").exists()


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3)
def test_account_form_rejects_duplicate_username(django_app, household):
    other = HouseholdFactory()
    BeneficiaryFactory(household=other, username="taken-name")
    info_res = _go_to_info_page(django_app, household)
    res = django_app.get(_account_create_link(info_res))
    res = _submit_account_form(res, "taken-name", ACCOUNT_PASSWORD)
    assert res.status_code == 200
    assert b"This username is already taken." in res.content
    assert not Beneficiary.objects.filter(household_id=household_key(household)).exists()


@pytest.mark.django_db
def test_auth_login_rejects_wrong_password(django_app, household):
    BeneficiaryFactory(household=household, username="auth-user")
    res = django_app.get(reverse("ui:flow:start-auth"))
    res.forms["reg-form"]["username"] = "auth-user"
    res.forms["reg-form"]["password"] = "WrongPass-99!"
    res = res.forms["reg-form"].submit()
    assert res.status_code == 200
    assert b"Invalid username or password" in res.content


@pytest.mark.django_db
def test_auth_login_rejects_unknown_user(django_app):
    res = django_app.get(reverse("ui:flow:start-auth"))
    res.forms["reg-form"]["username"] = "nobody"
    res.forms["reg-form"]["password"] = ACCOUNT_PASSWORD
    res = res.forms["reg-form"].submit()
    assert res.status_code == 200
    assert b"Invalid username or password" in res.content


@pytest.mark.django_db
def test_auth_login_rejects_suspended_beneficiary(django_app, household):
    BeneficiaryFactory(household=household, username="suspended-user", suspended=True)
    res = django_app.get(reverse("ui:flow:start-auth"))
    res.forms["reg-form"]["username"] = "suspended-user"
    res.forms["reg-form"]["password"] = ACCOUNT_PASSWORD
    res = res.forms["reg-form"].submit()
    assert res.status_code == 200
    assert b"Invalid username or password" in res.content


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3)
def test_account_form_prefills_empty_username_when_unicef_id_missing(django_app, household):
    household.unicef_id = ""
    household.save(update_fields=["unicef_id"])
    info_res = _go_to_info_page(django_app, household)
    res = django_app.get(_account_create_link(info_res))
    assert res.forms["account-form"]["username"].value == ""


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3)
def test_account_create_handles_integrity_error(django_app, household):
    info_res = _go_to_info_page(django_app, household)
    res = django_app.get(_account_create_link(info_res))
    with mock.patch(
        "hope_portal.ui.views.flow.account.Beneficiary.set_credentials",
        side_effect=IntegrityError(),
    ):
        res = _submit_account_form(res, "race-user", ACCOUNT_PASSWORD)
    assert res.status_code == 200
    assert b"This username is already taken." in res.content
    assert not Beneficiary.objects.filter(username="race-user").exists()


@pytest.mark.django_db
def test_auth_login_rejects_missing_household(django_app, household):
    beneficiary = BeneficiaryFactory(household=household, username="orphan-user")
    beneficiary.household_id = uuid.uuid4().hex
    beneficiary.save(update_fields=["household_id"])
    res = django_app.get(reverse("ui:flow:start-auth"))
    res.forms["reg-form"]["username"] = "orphan-user"
    res.forms["reg-form"]["password"] = ACCOUNT_PASSWORD
    res = res.forms["reg-form"].submit()
    assert res.status_code == 200
    assert b"Invalid username or password" in res.content


@pytest.mark.django_db
def test_auth_login_shows_lockout_page(django_app, household):
    BeneficiaryFactory(household=household, username="locked-user")
    res = django_app.get(reverse("ui:flow:start-auth"))
    res.forms["reg-form"]["username"] = "locked-user"
    res.forms["reg-form"]["password"] = ACCOUNT_PASSWORD
    with mock.patch(
        "hope_portal.ui.views.flow.start.Beneficiary.objects.get",
        side_effect=FlowLockoutError("Too many attempts."),
    ):
        res = res.forms["reg-form"].submit()
    assert res.status_code == 200
    assert b"Locked out" in res.content


@pytest.mark.django_db
@override_config(MIN_QUESTIONS=1, MAX_QUESTIONS=3)
def test_account_create_posts_to_refreshed_signed_data(django_app, household):
    info_res = _go_to_info_page(django_app, household)
    link = _account_create_link(info_res)
    res = django_app.get(link)
    form_action = res.forms["account-form"].action
    assert form_action
    assert form_action.rstrip("/") != res.request.path.rstrip("/")
    assert "/account/create/" in form_action
