from typing import Any

from ..settings import DEBUG

FLAGS_STATE_LOGGING = DEBUG
FLAGS: dict[str, list[Any]] = {
    "DEVELOP_DEBUG_TOOLBAR": [],
    "DEVELOP_QUESTION_DEBUG": [],
    "DEVELOP_UNSAFE_INFO": [],
    "SHOW_ADMIN_LINK": [],
    "SHOW_OPEN_ISSUE": [],
    "FLOW_START_REGISTRATION": [],
    "FLOW_START_SMS": [],
    "FLOW_START_EMAIL": [],
    "FLOW_START_AUTH": [],
    "FLOW_ACCOUNT_CREATE": [],
    "FLOW_ASK": [],
    "FLOW_INFO": [],
}
