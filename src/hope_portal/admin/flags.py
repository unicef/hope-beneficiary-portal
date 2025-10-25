from typing import Any

from django.contrib import admin
from flags.admin import FlagStateAdmin as BaseFlagStateAdmin
from flags.forms import FlagStateForm as BaseFlagStateForm
from flags.models import FlagState
from unfold.admin import ModelAdmin
from unfold.widgets import CHECKBOX_CLASSES, INPUT_CLASSES

admin.site.unregister([FlagState])


class FlagStateForm(BaseFlagStateForm):  # type: ignore[misc]
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs["class"] = " ".join(INPUT_CLASSES)
        self.fields["condition"].widget.attrs["class"] = " ".join(INPUT_CLASSES)
        self.fields["value"].widget.attrs["class"] = " ".join(INPUT_CLASSES)
        self.fields["name"].widget.attrs["class"] = " ".join(INPUT_CLASSES)
        self.fields["required"].widget.attrs["class"] = " ".join(CHECKBOX_CLASSES)


@admin.register(FlagState)
class FlagStateAdmin(BaseFlagStateAdmin[FlagState], ModelAdmin):  # type: ignore[misc]
    form = FlagStateForm
