import logging
from typing import Callable

from django.http import HttpRequest, HttpResponseBase, HttpResponseRedirect

from hope_portal.exception import FlowTimeoutError

logger = logging.getLogger(__name__)


class ExceptionHandlerMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponseBase]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponseBase:
        return self.get_response(request)

    def process_exception(self, request: HttpRequest, exception: Exception) -> HttpResponseRedirect | None:
        if isinstance(exception, FlowTimeoutError):
            logger.warning(f"Object not found for request: {request.path}")
            return HttpResponseRedirect("/")
        return None
