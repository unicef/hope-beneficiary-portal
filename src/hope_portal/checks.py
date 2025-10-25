import logging
from pathlib import Path
from typing import Any

from django.core.checks import CheckMessage, Error, register

from .config import env

logger = logging.getLogger(__name__)


@register(deploy=True)
def check_dirs(*args: Any, **kwargs: Any) -> list[CheckMessage]:
    return [
        Error(
            f"{_dir} '{Path(env(_dir))}' does not exists",
            hint="check your configuration",
            obj=None,
            id="hope_portal.E005",
        )
        for _dir in ("MEDIA_ROOT", "STATIC_ROOT")
        if not Path(env(_dir)).exists()
    ]
