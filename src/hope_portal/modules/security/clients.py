import logging
from typing import Any

from requests import Session
from requests.exceptions import HTTPError, RequestException

logger = logging.getLogger(__name__)


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

    def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any] | None:
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
            return None
        except RequestException:
            logger.warning("Failed to reach HOPE API", exc_info=True)
            return None
        except Exception:  # noqa: BLE001
            logger.warning("Unexpected error creating beneficiary ticket", exc_info=True)
            return None
        try:
            body = response.json()
        except ValueError:
            logger.warning("HOPE API returned a non-JSON ticket response")
            return None
        if not isinstance(body, dict):
            return None
        return body

    def create_beneficiary_ticket(
        self,
        business_area_slug: str,
        description: str,
        program_id: str | None = None,
        household_unicef_id: str | None = None,
    ) -> dict[str, Any] | None:
        payload: dict[str, Any] = {"description": description}
        if program_id:
            payload["program"] = program_id
        if household_unicef_id:
            payload["household_unicef_id"] = household_unicef_id
        return self._post(f"{business_area_slug}/beneficiary-tickets/", payload)
