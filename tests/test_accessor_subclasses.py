"""Hand-written contracts keep accessor values consistent with serialized characters."""

from __future__ import annotations

import pytest

from altsvc import Alternative, build, expires_at, is_fresh, parse


class Authority(str):
    def rpartition(self, sep: str) -> tuple[str, str, str]:
        return "evil.example", ":", "80"

    def __str__(self) -> str:
        return "evil.example:80"


class Lifetime(str):
    def lstrip(self, chars: str | None = None) -> str:
        return "86400"

    def __str__(self) -> str:
        return "86400"


class Key(str):
    def translate(self, table: object) -> str:
        return "ma"

    def __str__(self) -> str:
        return "ma"


class Persistence(str):
    def __eq__(self, other: object) -> bool:
        return False

    def __str__(self) -> str:
        return "0"


def _roundtrip(alternative: Alternative) -> Alternative:
    decoded = parse(build([alternative]), strict=True)
    assert isinstance(decoded, list) and len(decoded) == 1
    return decoded[0]


@pytest.mark.parametrize("authority", ["good.example:443", "[::1]:8443", ":443"])
def test_authority_accessors_preserve_serialized_characters(authority: str) -> None:
    alternative = Alternative("h3", Authority(authority))
    decoded = _roundtrip(alternative)
    assert (alternative.host, alternative.port) == (decoded.host, decoded.port)
    assert type(alternative.authority) is Authority


@pytest.mark.parametrize("lifetime", ["0", "60", "2147483648"])
def test_lifetime_accessors_preserve_serialized_characters(lifetime: str) -> None:
    alternative = Alternative("h3", ":443", {"ma": Lifetime(lifetime)})
    decoded = _roundtrip(alternative)
    assert alternative.ma == decoded.ma == int(lifetime)
    assert alternative.max_age == decoded.max_age
    assert expires_at(alternative, 100) == expires_at(decoded, 100)
    assert is_fresh(alternative, 100, 100) == is_fresh(decoded, 100, 100)
    assert type(alternative.params["ma"]) is Lifetime


@pytest.mark.parametrize("key", ["extension", "MA", "persist"])
def test_parameter_keys_preserve_serialized_characters(key: str) -> None:
    alternative = Alternative("h3", ":443", {Key(key): "1"})
    decoded = _roundtrip(alternative)
    assert alternative.ma == decoded.ma
    assert alternative.max_age == decoded.max_age
    assert alternative.persist == decoded.persist


def test_persistence_accessor_preserves_serialized_characters() -> None:
    alternative = Alternative("h3", ":443", {"persist": Persistence("1")})
    decoded = _roundtrip(alternative)
    assert alternative.persist is decoded.persist is True
