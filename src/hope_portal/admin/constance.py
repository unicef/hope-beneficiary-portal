from constance.admin import Config, ConstanceAdmin
from django.contrib import admin

admin.site.unregister([Config])


@admin.register(Config)
class ConstanceConfigAdmin(ConstanceAdmin[Config]):  # type: ignore[misc]
    pass
