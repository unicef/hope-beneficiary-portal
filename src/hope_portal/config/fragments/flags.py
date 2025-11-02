from typing import Any

from ..settings import DEBUG

FLAGS_STATE_LOGGING = DEBUG
FLAGS: dict[str, list[Any]] = {
    "DEVELOP_DEBUG_TOOLBAR": [],
    "DEVELOP_QUESTION_DEBUG": [],
    "DEVELOP_UNSAFE_INFO": [],
    "SHOW_ADMIN_LINK": [],
    "SHOW_OPEN_ISSUE": [],
}
