"""Factory contracts preserve the underlying values of accepted subclasses."""

from __future__ import annotations

import pytest

from altsvc import Alternative, AltSvcError


class RenderedInt(int):
    def __format__(self, spec: str) -> str:
        return "80"

    def __str__(self) -> str:
        return "86400"

    def __int__(self) -> int:
        return 80

    def __le__(self, other: object) -> bool:
        return True

    def __ge__(self, other: object) -> bool:
        return True


class RenderedHost(str):
    def __format__(self, spec: str) -> str:
        return "evil.example"

    def __str__(self) -> str:
        return "evil.example"


def test_factory_preserves_integer_port_value() -> None:
    assert Alternative.of("h3", RenderedInt(443)).port == 443


@pytest.mark.parametrize("value", [0, 60, 2**31])
def test_factory_preserves_integer_lifetime_value(value: int) -> None:
    assert Alternative.of("h3", 443, ma=RenderedInt(value)).max_age == value


@pytest.mark.parametrize("host", ["good.example", "::1", "[::1]"])
def test_factory_preserves_host_characters(host: str) -> None:
    assert Alternative.of("h3", 443, RenderedHost(host)).host == host.strip("[]")


@pytest.mark.parametrize("value", [-1, 65536])
def test_factory_validates_underlying_port(value: int) -> None:
    with pytest.raises(AltSvcError) as caught:
        Alternative.of("h3", RenderedInt(value))
    assert caught.value.code == "authority.port"


@pytest.mark.parametrize("value", [-1, 2**31 + 1])
def test_factory_validates_underlying_lifetime(value: int) -> None:
    with pytest.raises(AltSvcError) as caught:
        Alternative.of("h3", 443, ma=RenderedInt(value))
    assert caught.value.code == "ma.invalid"
