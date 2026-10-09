import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from requests import Session
from requests.exceptions import HTTPError, RequestException

logger = logging.getLogger(__name__)


class TicketCreateOutcome(StrEnum):
    CREATED = "created"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class TicketCreateResult:
    """Result of asking HOPE to create a beneficiary grievance.

    FAILED means HOPE rejected the request. UNKNOWN means the request did not
    finish in a way we can trust, so the ticket may already exist.
    """

    outcome: TicketCreateOutcome
    ticket: dict[str, Any] | None = None


class HopeAPIClient:
    def __init__(self, base_url: str, token: str, timeout: int) -> None:
        self.base_url = base_url
        self.token = token
        self.timeout = timeout

        self._session = Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Token {self.token}",
            }
        )

    def _post(self, endpoint: str, payload: dict[str, Any]) -> TicketCreateResult:
        url = f"{self.base_url.rstrip('/')}/{endpoint}"
        try:
            response = self._session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except HTTPError as exc:
            logger.warning(
                "Failed to create beneficiary ticket",
                extra={"status": exc.response.status_code if exc.response else None},
                exc_info=True,
            )
            return TicketCreateResult(TicketCreateOutcome.FAILED)
        except RequestException:
            logger.warning("Could not confirm beneficiary ticket creation", exc_info=True)
            return TicketCreateResult(TicketCreateOutcome.UNKNOWN)
        except Exception:  # noqa: BLE001
            logger.warning("Unexpected error creating beneficiary ticket", exc_info=True)
            return TicketCreateResult(TicketCreateOutcome.UNKNOWN)
        try:
            body = response.json()
        except ValueError:
            logger.warning("HOPE API returned a non-JSON ticket response")
            return TicketCreateResult(TicketCreateOutcome.UNKNOWN)
        if not isinstance(body, dict) or not body.get("code"):
            return TicketCreateResult(TicketCreateOutcome.UNKNOWN)
        return TicketCreateResult(TicketCreateOutcome.CREATED, body)

    def create_beneficiary_ticket(
        self,
        business_area_slug: str,
        description: str,
        program_id: str | None = None,
        household_unicef_id: str | None = None,
    ) -> TicketCreateResult:
        payload: dict[str, Any] = {"description": description}
        if program_id:
            payload["program"] = program_id
        if household_unicef_id:
            payload["household_unicef_id"] = household_unicef_id
        return self._post(f"{business_area_slug}/beneficiary-tickets/", payload)
