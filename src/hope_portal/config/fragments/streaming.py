from .. import env

STREAMING = {
    "BROKER_URL": env("STREAMING_BROKER_URL"),
    "QUEUES": {
        "hope_portal": {
            "routing": ["hope.*.*"],
        },
    },
}
