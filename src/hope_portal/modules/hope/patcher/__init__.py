import logging
from functools import partial, partialmethod
from typing import TYPE_CHECKING, Sequence

from django.apps import AppConfig, apps
from django.db import models

from hope_portal.modules.hope import models as hope_models

if TYPE_CHECKING:
    from django.db.models import Model

    from hope_portal.modules.hope.models import HopeModel


logger = logging.getLogger(__name__)


def label(attr: str, self: "type[Model]") -> str:
    return str(getattr(self, attr))


def add_m2m(
    master: "type[Model]", name: str, detail: "type[Model]", through: "type[Model]", related_name: "str|None" = None
) -> None:
    models.ManyToManyField(
        detail,
        through=through,
        related_name=related_name,
    ).contribute_to_class(master, name)


def patch() -> None:
    ordering: "dict[type[Model], Sequence[str]]" = {
        hope_models.BusinessArea: ["name"],
        hope_models.Household: ["unicef_id"],
    }

    appconf: AppConfig = apps.get_app_config("hope")
    model: HopeModel

    for model in appconf.get_models():
        for attr in ["name", "username", "unicef_id"]:
            if hasattr(model, attr):
                model.__str__ = partialmethod(partial(label, attr))
                break

        if model in ordering:
            model._meta.ordering = ordering[model]
        else:
            model._meta.ordering = ["pk"]

    from . import hh  # noqa
