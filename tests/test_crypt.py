from types import SimpleNamespace

import pytest

from hope_portal.exception import FlowTimeoutError
from hope_portal.ui.views.flow.crypt import sign_candidates, unsign_candidates
from testutils.factories.hope.houshold import HouseholdFactory


@pytest.fixture
def req(rf):
    """A lightweight fake request with a stable session key."""
    request = rf.get("/")
    request.session = SimpleNamespace(session_key="test-session-key-crypt")
    return request


@pytest.mark.django_db
def test_sign_unsign_candidates_round_trip_preserves_order(req):
    households = [HouseholdFactory(), HouseholdFactory(), HouseholdFactory()]
    signed = sign_candidates(req, households)
    result = unsign_candidates(req, signed)
    assert [str(h.pk) for h in result] == [str(h.pk) for h in households]


@pytest.mark.django_db
def test_sign_unsign_candidates_empty_list(req):
    signed = sign_candidates(req, [])
    assert unsign_candidates(req, signed) == []


@pytest.mark.django_db
def test_unsign_candidates_skips_deleted_households(req):
    surviving = HouseholdFactory()
    deleted = HouseholdFactory()
    # Sign with both IDs, then delete one from the DB.
    signed = sign_candidates(req, [surviving, deleted])
    deleted.delete()

    result = unsign_candidates(req, signed)

    assert len(result) == 1
    assert str(result[0].pk) == str(surviving.pk)


@pytest.mark.django_db
def test_unsign_candidates_raises_flow_timeout_on_bad_signature(req):
    with pytest.raises(FlowTimeoutError):
        unsign_candidates(req, "this.is.not.a.valid.signed.token")


@pytest.mark.django_db
def test_unsign_candidates_raises_flow_timeout_on_wrong_session_key(req, rf):
    households = [HouseholdFactory()]
    signed = sign_candidates(req, households)

    other_req = rf.get("/")
    other_req.session = SimpleNamespace(session_key="completely-different-key")
    with pytest.raises(FlowTimeoutError):
        unsign_candidates(other_req, signed)
