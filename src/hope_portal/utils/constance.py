import logging
from typing import TYPE_CHECKING, Any, Mapping, Sequence

from constance import config
from django.contrib.auth.models import Group
from django.forms import ChoiceField, TextInput, Textarea, Widget

if TYPE_CHECKING:
    from django.core.files.uploadedfile import UploadedFile
    from django.utils.datastructures import MultiValueDict

    _DataT = Mapping[str, Any]  # noqa: PYI047
    _FilesT = MultiValueDict[str, UploadedFile]  # noqa: PYI047


logger = logging.getLogger(__name__)


class GroupSelect(ChoiceField):
    def __init__(self, **kwargs: Any) -> None:
        ret: Sequence[tuple[str | int, str]] = [("", "None")] + [
            (c["pk"], c["name"]) for c in Group.objects.values("pk", "name")
        ]
        kwargs["choices"] = ret
        super().__init__(**kwargs)


class WriteOnlyWidget(Widget):
    def format_value(self, value: Any) -> str:
        return str(super().format_value("***"))

    def value_from_datadict(self, data: "_DataT", files: "_FilesT", name: str) -> Any:
        value = data.get(name)
        if value == "***":
            return getattr(config, name)
        return value


class WriteOnlyTextarea(WriteOnlyWidget, Textarea):
    pass


class WriteOnlyInput(WriteOnlyWidget, TextInput):
    pass
