from sentry_sdk import capture_exception as _capture_exception


def capture_exception(error: Exception | None = None) -> str | None:
    return _capture_exception(error)
