from typing import Any, Callable, Iterable


class Dummy:
    pass


def is_simple(obj: Any) -> bool:
    return not hasattr(obj, "__dict__")


def flatten(x: list[Any]) -> list[Any]:
    result = []
    for el in x:
        # if isinstance(el, (list, tuple)):
        if hasattr(el, "__iter__") and not isinstance(el, str):
            result.extend(flatten(el))
        else:
            result.append(el)
    return list(result)


def get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    if "." not in attr:
        return getattr(obj, attr, default)
    parts = attr.split(".")
    return get_attr(getattr(obj, parts[0], default), ".".join(parts[1:]), default)


class classproperty:  # noqa: N801
    def __init__(self, getter: Callable[[Any], Any]) -> None:
        self.getter = getter

    def __get__(self, instance: Any, owner: Any) -> Any:
        return self.getter(owner)


def repr_list(iterable: Iterable[Any]) -> str:
    return ", ".join("'%s'" % str(i) for i in iterable)
