ISSUES = {
    "BACKEND": "issues.backends.github.Backend",
    "RENDERER": "html2canvas-pro",
    "OPTIONS": {
        "API_TOKEN": "your_gitlab_private_access_token",
        "PROJECT": "your_project_id_or_path",
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
