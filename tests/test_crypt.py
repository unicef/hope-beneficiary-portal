from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from hope_portal.exception import FlowTimeoutError
from hope_portal.modules.hope.models import Household
from hope_portal.ui.views.flow.crypt import sign_candidates, unsign_candidates


@pytest.fixture
def req(rf):
    """Lightweight fake request carrying a stable session key."""
    request = rf.get("/")
    request.session = SimpleNamespace(session_key="test-session-key-crypt")
    return request


def _mock_household(pk: str) -> MagicMock:
    hh = MagicMock()
    hh.id = pk
    hh.pk = pk
    return hh


def _mock_objects(filter_result: list) -> MagicMock:
    mgr = MagicMock()
    mgr.filter.return_value = filter_result
    return mgr


# ---------------------------------------------------------------------------
# Round-trip: signing order is preserved regardless of queryset return order
# ---------------------------------------------------------------------------


def test_sign_unsign_candidates_round_trip_preserves_order(req):
    h1 = _mock_household("id-1")
    h2 = _mock_household("id-2")
    h3 = _mock_household("id-3")

    signed = sign_candidates(req, [h1, h2, h3])

    # Queryset returns in a different order — unsign must restore the original one.
    with patch.object(Household, "objects", _mock_objects([h3, h1, h2])):
        result = unsign_candidates(req, signed)

    assert result == [h1, h2, h3]


# ---------------------------------------------------------------------------
# Empty candidate list
# ---------------------------------------------------------------------------


def test_sign_unsign_candidates_empty_list(req):
    # filter(pk__in=[]) is optimised to an empty queryset by Django — no DB hit.
    signed = sign_candidates(req, [])
    with patch.object(Household, "objects", _mock_objects([])):
        assert unsign_candidates(req, signed) == []


# ---------------------------------------------------------------------------
# Households that no longer exist in the DB are silently skipped
# ---------------------------------------------------------------------------


def test_unsign_candidates_skips_missing_households(req):
    surviving = _mock_household("id-surviving")
    signed = sign_candidates(req, [surviving, _mock_household("id-deleted")])

    # Only the surviving household is returned by the queryset.
    with patch.object(Household, "objects", _mock_objects([surviving])):
        result = unsign_candidates(req, signed)

    assert result == [surviving]


# ---------------------------------------------------------------------------
# Tampered token → FlowTimeoutError
# ---------------------------------------------------------------------------


def test_unsign_candidates_raises_flow_timeout_on_bad_signature(req):
    with pytest.raises(FlowTimeoutError):
        unsign_candidates(req, "this.is.not.a.valid.signed.token")


# ---------------------------------------------------------------------------
# Different session key makes the token unreadable
# ---------------------------------------------------------------------------


def test_unsign_candidates_raises_flow_timeout_on_wrong_session_key(req, rf):
    signed = sign_candidates(req, [_mock_household("some-id")])

    other_req = rf.get("/")
    other_req.session = SimpleNamespace(session_key="completely-different-key")
    with pytest.raises(FlowTimeoutError):
        unsign_candidates(other_req, signed)
