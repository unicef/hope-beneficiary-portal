import uuid
from types import SimpleNamespace

import pytest
from django.contrib.auth.hashers import PBKDF2SHA1PasswordHasher, identify_hasher
from testutils.factories.beneficiary import BeneficiaryFactory
from testutils.factories.hope.houshold import HouseholdFactory

from hope_portal.models.beneficiary import Beneficiary, household_key
from hope_portal.ui.forms.flow import AccountCredentialsForm

ACCOUNT_PASSWORD = "PortalLogin-42!"


@pytest.fixture
def household():
    return HouseholdFactory()


def test_household_key_normalizes_uuid_and_hex_string():
    uid = uuid.uuid4()
    assert household_key(SimpleNamespace(id=uid)) == uid.hex
    assert household_key(SimpleNamespace(id=uid.hex)) == uid.hex
    assert household_key(SimpleNamespace(id=str(uid))) == uid.hex


@pytest.mark.django_db
def test_beneficiary_str_returns_username(household):
    beneficiary = BeneficiaryFactory(household=household, username="visible-name")
    assert str(beneficiary) == "visible-name"


@pytest.mark.django_db
def test_for_household_returns_none_when_missing(household):
    assert Beneficiary.for_household(household) is None


@pytest.mark.django_db
def test_set_credentials_creates_then_updates(household):
    created = Beneficiary.set_credentials(household, "first-user", ACCOUNT_PASSWORD)
    assert created.username == "first-user"
    assert created.check_password(ACCOUNT_PASSWORD)
    assert Beneficiary.for_household(household) == created

    updated = Beneficiary.set_credentials(household, "second-user", "OtherPass-99!")
    assert updated.pk == created.pk
    assert updated.username == "second-user"
    assert updated.check_password("OtherPass-99!")
    assert Beneficiary.objects.filter(household_id=household_key(household)).count() == 1


@pytest.mark.django_db
def test_link_to_updates_household_and_clears_cached_property(household):
    other = HouseholdFactory()
    beneficiary = BeneficiaryFactory(household=household, username="mover")
    assert household_key(beneficiary.household) == household_key(household)

    beneficiary.link_to(other)

    assert beneficiary.household_id == household_key(other)
    assert household_key(beneficiary.household) == household_key(other)


@pytest.mark.django_db
def test_link_to_without_cached_household(household):
    other = HouseholdFactory()
    beneficiary = BeneficiaryFactory(household=household, username="uncached")
    beneficiary.link_to(other)
    assert beneficiary.household_id == household_key(other)


@pytest.mark.django_db
def test_check_password_upgrades_unpreferred_hasher(household):
    beneficiary = BeneficiaryFactory(household=household, username="hasher-user")
    hasher = PBKDF2SHA1PasswordHasher()
    beneficiary.password = hasher.encode(ACCOUNT_PASSWORD, hasher.salt())
    beneficiary.save(update_fields=["password"])
    assert identify_hasher(beneficiary.password).algorithm == "pbkdf2_sha1"

    assert beneficiary.check_password(ACCOUNT_PASSWORD)
    beneficiary.refresh_from_db()
    assert identify_hasher(beneficiary.password).algorithm != "pbkdf2_sha1"


def _form_data(username="good-user", password=ACCOUNT_PASSWORD, password_confirm=None):
    return {
        "username": username,
        "password": password,
        "password_confirm": password if password_confirm is None else password_confirm,
    }


@pytest.mark.django_db
def test_account_credentials_form_valid_without_instance():
    form = AccountCredentialsForm(data=_form_data())
    assert form.is_valid()
    assert form.fields["password"].label != "New password"


@pytest.mark.django_db
def test_account_credentials_form_relabels_password_when_updating(household):
    beneficiary = BeneficiaryFactory(household=household, username="existing-user")
    form = AccountCredentialsForm(instance=beneficiary)
    assert form.fields["password"].label == "New password"
    assert form.fields["password_confirm"].label == "Confirm new password"


@pytest.mark.django_db
def test_account_credentials_form_allows_keeping_own_username(household):
    beneficiary = BeneficiaryFactory(household=household, username="keep-me")
    form = AccountCredentialsForm(data=_form_data(username="keep-me"), instance=beneficiary)
    assert form.is_valid()


@pytest.mark.django_db
def test_account_credentials_form_rejects_duplicate_when_instance_has_no_pk(household):
    BeneficiaryFactory(household=household, username="taken-name")
    form = AccountCredentialsForm(
        data=_form_data(username="taken-name"),
        instance=Beneficiary(username="unsaved"),
    )
    assert not form.is_valid()
    assert "already taken" in form.errors["username"][0]


@pytest.mark.django_db
def test_account_credentials_form_rejects_duplicate_when_updating_to_another_user(household):
    BeneficiaryFactory(household=household, username="taken-name")
    other = HouseholdFactory()
    mine = BeneficiaryFactory(household=other, username="mine")
    form = AccountCredentialsForm(data=_form_data(username="taken-name"), instance=mine)
    assert not form.is_valid()
    assert "already taken" in form.errors["username"][0]


@pytest.mark.django_db
def test_account_credentials_form_rejects_weak_password():
    form = AccountCredentialsForm(data=_form_data(password="password", password_confirm="password"))
    assert not form.is_valid()
    assert "password" in form.errors


@pytest.mark.django_db
def test_account_credentials_form_rejects_invalid_username():
    form = AccountCredentialsForm(data=_form_data(username="bad user!"))
    assert not form.is_valid()
    assert "username" in form.errors


@pytest.mark.django_db
def test_account_credentials_form_clean_skips_password_checks_when_missing():
    form = AccountCredentialsForm(data={"username": "good-user"})
    assert not form.is_valid()
    assert "password" in form.errors
    assert "password_confirm" in form.errors
