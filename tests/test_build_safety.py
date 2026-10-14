"""The builder refuses everything that would not read back strictly to the same value."""

from __future__ import annotations

import pytest

from altsvc import CLEAR, Alternative, AltSvcError, build, parse


@pytest.mark.parametrize(
    ("alternative", "code"),
    [
        (Alternative("h3", ":443\r\nSet-Cookie: x=1"), "authority.port"),
        (Alternative("h3", "a\r\nb:443"), "authority.host"),
        (Alternative("h3", ":443", {"note": "a\r\nSet-Cookie: x"}), "parameter.value"),
        (Alternative("h3", ":443", {"note": "caf\u00e9"}), "parameter.value"),
        (Alternative("h3", ":443", {"note": "a\x00"}), "parameter.value"),
        (Alternative("h3", ":443", {"ma": "-1"}), "ma.invalid"),
        (Alternative("h3", ":443", {"ma": "2147483649"}), "ma.invalid"),
        (Alternative("h3", ":443", {"MA": "1" + "0" * 20}), "ma.invalid"),
        (Alternative("h3", ":443", {"ma": "\u0661"}), "parameter.value"),
        (Alternative("h3", ":443", {"persist": "0"}), "persist.invalid"),
        (Alternative("h3", ":443", {"ma": "1", "Ma": "2"}), "parameter.duplicate"),
        (Alternative("h3", ":443", {"": "1"}), "parameter.name"),
        (Alternative("h%33", ":443"), "protocol-id.canonical"),
        (Alternative("w=x", ":443"), "protocol-id.canonical"),
        (Alternative("h3", ":0"), "authority.port"),
        (Alternative("h3", "host"), "authority.port"),
    ],
)
def test_build_refuses(alternative: Alternative, code: str) -> None:
    with pytest.raises(AltSvcError) as caught:
        build([alternative])
    assert caught.value.code == code


def test_build_accepts_the_largest_ma_and_leading_zeros() -> None:
    header = build([Alternative("h3", ":443", {"ma": "2147483648"})])
    assert header == 'h3=":443"; ma=2147483648'
    assert build([Alternative("h3", ":443", {"ma": "007"})]) == 'h3=":443"; ma=007'


def test_build_quotes_values_that_are_not_tokens() -> None:
    header = build([Alternative("h3", ":443", {"a": 'x"y\\z', "b": "", "c": "1,2"})])
    assert header == 'h3=":443"; a="x\\"y\\\\z"; b=""; c="1,2"'
    assert parse(header, strict=True) == [
        Alternative("h3", ":443", {"a": 'x"y\\z', "b": "", "c": "1,2"})
    ]


class _Sneaky(str):
    def __str__(self) -> str:
        return 'h3=":1"\r\nSet-Cookie: x'

    def __format__(self, spec: str) -> str:
        return self.__str__()


def test_build_writes_the_characters_of_a_str_subclass_not_its_rendering() -> None:
    header = build([Alternative(_Sneaky("h3"), _Sneaky(":443"), {_Sneaky("a"): _Sneaky("b")})])
    assert header == 'h3=":443"; a=b'
    assert type(header) is str


def test_build_refuses_non_text_parts() -> None:
    for alternative in (
        Alternative(b"h3", ":443"),  # type: ignore[arg-type]
        Alternative("h3", 443),  # type: ignore[arg-type]
        Alternative("h3", ":443", {"ma": 60}),  # type: ignore[dict-item]
        Alternative("h3", ":443", {1: "x"}),  # type: ignore[dict-item]
    ):
        with pytest.raises(TypeError):
            build([alternative])


def test_build_refuses_a_string_or_a_non_alternative() -> None:
    with pytest.raises(TypeError):
        build('h3=":443"')  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        build([("h3", ":443")])  # type: ignore[list-item]
    with pytest.raises(TypeError):
        build(iter([Alternative("h3", ":443")]))  # type: ignore[arg-type]


def test_build_clear_and_ipv6() -> None:
    assert build(CLEAR) == "clear"
    assert build([Alternative.of("h3", 443, "2001:db8::1")]) == 'h3="[2001:db8::1]:443"'
