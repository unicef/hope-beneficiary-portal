import pytest

from hope_portal.utils.language import flatten, get_attr, is_simple


def test_get_attr():
    assert get_attr(pytest, "Cache")

    class C:
        pass

    a = C()
    a.b = C()
    a.b.c = 4
    assert get_attr(a, "b.c") == 4
    assert get_attr(a, "b.c.y", None) is None
    assert get_attr(a, "b.c.y", 1) == 1


def test_is_simple():
    return is_simple(pytest)


@pytest.mark.parametrize(
    ["value", "expected"],
    [
        ([1, 2], [1, 2]),
        ([11, 22, [33, 44, 55]], [11, 22, 33, 44, 55]),
        ([11, 22, (33, 44, 55), [66, [77, 88]]], [11, 22, 33, 44, 55, 66, 77, 88]),
        ([[[1, 2, 3], (42, None)], [4, 5], [6], 7, (8, 9, 10)], [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]),
    ],
)
def test_flatten(value, expected):
    assert flatten(value) == expected
