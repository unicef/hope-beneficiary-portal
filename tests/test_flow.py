from unittest import mock

import pytest
from constance.test import override_config
from django.urls import reverse
from testutils.factories.hope.houshold import HouseholdFactory

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
    res.forms["reg-form"]["registration_number"] = household.detail_id
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
    res.forms["reg-form"]["registration_number"] = household.detail_id
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
    assert captured["program_id"] == str(household.program_id)


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
