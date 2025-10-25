import importlib
from collections.abc import Iterable
from typing import Any

from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


def get_hope_storage() -> Any:
    options = settings.STORAGES["hope"]["OPTIONS"]
    package_name, klass_name = settings.STORAGES["hope"]["BACKEND"].rsplit(".", 1)
    module = importlib.import_module(package_name)
    return getattr(module, klass_name)(**options)


class HopeModel(models.Model):
    class Meta:
        abstract = True
        managed = False
        app_label = "hope"

    class Tenant:
        tenant_filter_field = None

    def save(
        self,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        pass

    def delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        return 0, {}
