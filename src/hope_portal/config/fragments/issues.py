from .. import env

ISSUES_API_TOKEN = env("ISSUES_API_TOKEN")
ISSUES_PROJECT = env("ISSUES_PROJECT")
ISSUES_CONFIGURED = bool(ISSUES_API_TOKEN and ISSUES_PROJECT)

ISSUES = {
    "BACKEND": "issues.backends.github.Backend",
    "RENDERER": "html2canvas-pro",
    "OPTIONS": {
        "API_TOKEN": ISSUES_API_TOKEN,
        "PROJECT": ISSUES_PROJECT,
    },
    "ANNOTATIONS": {
        "get_client_ip": "issues.utils.get_client_ip",
        "get_extra_info": "issues.utils.get_extra_info",
        "get_labels": "issues.utils.get_labels",
        "get_user": "issues.utils.get_user",
        "get_user_agent": "issues.utils.get_user_agent",
        "get_version": "issues.utils.get_version",
    },
}
