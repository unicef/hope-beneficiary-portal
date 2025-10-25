from unittest import mock

import pytest
from django.urls import reverse
from testutils.factories.hope.houshold import HouseholdFactory


@pytest.fixture
def household():
    return HouseholdFactory()


@pytest.mark.django_db
def test_flow_not_found(django_app, household):
    url = reverse("ui:flow:start")
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
def test_flow_found(django_app, household):
    url = reverse("ui:flow:start")
    res = django_app.get(url)
    res.forms["reg-form"]["registration_number"] = household.detail_id
    res = res.forms["reg-form"].submit().follow()
    res = res.forms["ask-form"].submit()
    assert res.status_code == 200
    with mock.patch("hope_portal.ui.forms.ask.QuestionForm.check_value", return_value=True):
        res.forms["ask-form"]["form-0-question"] = "--"
        res.forms["ask-form"]["form-1-question"] = "--"
        res.forms["ask-form"]["form-2-question"] = "--"
        res = res.forms["ask-form"].submit()
    assert res.status_code == 302
    res = res.follow()
    assert b"Welcome" in res.content
