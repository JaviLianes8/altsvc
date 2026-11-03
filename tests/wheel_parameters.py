"""Hand-written parameter contracts executed by the isolated installed consumer."""

from __future__ import annotations

from collections import UserDict
from collections.abc import Callable, ItemsView, Mapping
from types import MappingProxyType
from typing import cast

import altsvc
from altsvc import DEFAULT_MAX_AGE, Alternative, AltSvcError, expires_at, is_fresh

assert "site-packages" in altsvc.__file__, altsvc.__file__


class ItemsOnly:
    def items(self) -> ItemsView[str, str]:
        return {"ma": "1", "persist": "1"}.items()


items_only = ItemsOnly()
assert not isinstance(items_only, Mapping)
for accessor in ("ma", "max_age", "persist"):
    item = Alternative("h3", ":443", cast(dict[str, str], items_only))
    try:
        getattr(item, accessor)
    except TypeError:
        pass
    else:
        raise AssertionError(f"{accessor} must reject items-only non-mappings")

for padding in (" {}", "{} ", " {} ", "\t{}", "{}\t", "\t{} \t"):
    padded_ma = padding.format("ma")
    padded_persist = padding.format("persist")
    item = Alternative("h3", ":443", {padded_ma: "1", padded_persist: "1"})
    assert item.ma is None
    assert item.max_age == DEFAULT_MAX_AGE
    assert item.persist is False
    item = Alternative(
        "h3", ":443", {"ma": "7", "persist": "0", padded_ma: "1", padded_persist: "1"}
    )
    assert item.ma == 7
    assert item.max_age == 7
    assert item.persist is False

mapping_factories: tuple[Callable[[dict[str, str]], Mapping[str, str]], ...] = (
    UserDict,
    MappingProxyType,
)
for mapping in mapping_factories:
    params = mapping({"ma": "1", "persist": "1"})
    # Exercise the runtime mapping contract without changing the constructor annotation.
    item = Alternative("h3", ":443", cast(dict[str, str], params))
    assert item.ma == 1
    assert item.max_age == 1
    assert item.persist is True

for value in (" 1", "1 ", " 1 ", "\t1", "1\t", "\t1 \t"):
    assert Alternative("h3", ":443", {"persist": value}).persist is False

for name in ("per\u017fist", "persi\u017ft", "per\u017fi\u017ft", "PER\u017fI\u017fT"):
    assert Alternative("h3", ":443", {name: "1"}).persist is False
    assert Alternative("h3", ":443", {"persist": "0", name: "1"}).persist is False

for name in ("persist", "PERSIST", "Persist"):
    assert Alternative("h3", ":443", {name: "1"}).persist is True

readers: tuple[Callable[[Alternative], object], ...] = (
    lambda item: item.ma,
    lambda item: item.max_age,
    lambda item: expires_at(item, 100),
    lambda item: is_fresh(item, 100, 100),
)
for value in (" 1", "1 ", " 1 ", "\t1", "1\t", "\t1 \t"):
    item = Alternative("h3", ":443", {"ma": value})
    for read in readers:
        try:
            read(item)
        except AltSvcError as error:
            assert error.code == "ma.invalid"
        else:
            raise AssertionError("whitespace-padded ma must raise ma.invalid")

for name in ("ma", "MA", "Ma"):
    item = Alternative("h3", ":443", {name: ""})
    for read in readers:
        try:
            read(item)
        except AltSvcError as error:
            assert error.code == "ma.invalid"
        else:
            raise AssertionError("empty ma must raise ma.invalid")

item = Alternative("h3", ":443")
assert item.ma is None
assert item.max_age == DEFAULT_MAX_AGE == 86400
assert expires_at(item, 100) == 86500
assert is_fresh(item, 100, 86499)
assert not is_fresh(item, 100, 86500)
