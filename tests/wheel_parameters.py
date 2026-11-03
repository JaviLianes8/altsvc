"""Hand-written parameter contracts executed by the isolated installed consumer."""

from __future__ import annotations

from collections.abc import Callable

import altsvc
from altsvc import DEFAULT_MAX_AGE, Alternative, AltSvcError, expires_at, is_fresh

assert "site-packages" in altsvc.__file__, altsvc.__file__

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
