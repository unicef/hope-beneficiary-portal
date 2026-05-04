from unittest.mock import Mock
from requests.exceptions import HTTPError, RequestException

from hope_portal.modules.security.clients import HopeAPIClient


def test_create_beneficiary_ticket_builds_endpoint_and_payload(monkeypatch):
    client = HopeAPIClient(base_url="https://hope.example.org/", token="token", timeout=3)
    captured = {}

    def _capture_post(endpoint, payload):
        captured["endpoint"] = endpoint
        captured["payload"] = payload

    monkeypatch.setattr(client, "_post", _capture_post)

    client.create_beneficiary_ticket("ba-slug", "desc")

    assert captured["endpoint"] == "ba-slug/beneficiary-tickets/"
    assert captured["payload"] == {"description": "desc"}


def test_post_success_calls_requests_session_with_timeout():
    client = HopeAPIClient(base_url="https://hope.example.org/", token="token", timeout=7)
    response = Mock()
    response.raise_for_status = Mock()
    client._session.post = Mock(return_value=response)

    client._post("ba-slug/beneficiary-tickets/", {"description": "desc"})

    client._session.post.assert_called_once_with(
        "https://hope.example.org/ba-slug/beneficiary-tickets/",
        json={"description": "desc"},
        timeout=7,
    )
    response.raise_for_status.assert_called_once()


def test_post_handles_http_error(monkeypatch):
    client = HopeAPIClient(base_url="https://hope.example.org", token="token", timeout=3)
    response = Mock(status_code=500)
    http_error = HTTPError(response=response)
    client._session.post = Mock(side_effect=http_error)
    warning = Mock()
    monkeypatch.setattr("hope_portal.modules.security.clients.logger.warning", warning)

    client._post("ba-slug/beneficiary-tickets/", {"description": "desc"})

    warning.assert_called_once()


def test_post_handles_request_exception(monkeypatch):
    client = HopeAPIClient(base_url="https://hope.example.org", token="token", timeout=3)
    client._session.post = Mock(side_effect=RequestException("network"))
    warning = Mock()
    monkeypatch.setattr("hope_portal.modules.security.clients.logger.warning", warning)

    client._post("ba-slug/beneficiary-tickets/", {"description": "desc"})

    warning.assert_called_once()


def test_post_handles_unexpected_exception(monkeypatch):
    client = HopeAPIClient(base_url="https://hope.example.org", token="token", timeout=3)
    client._session.post = Mock(side_effect=RuntimeError("boom"))
    warning = Mock()
    monkeypatch.setattr("hope_portal.modules.security.clients.logger.warning", warning)

    client._post("ba-slug/beneficiary-tickets/", {"description": "desc"})

    warning.assert_called_once()
