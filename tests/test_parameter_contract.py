"""Hand-written contracts for ASCII parameter names and explicit empty lifetimes."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from altsvc import DEFAULT_MAX_AGE, Alternative, AltSvcError, expires_at, is_fresh


@pytest.mark.parametrize(
    "name", ["per\u017fist", "persi\u017ft", "per\u017fi\u017ft", "PER\u017fI\u017fT"]
)
def test_non_ascii_lookalikes_cannot_enable_persistence(name: str) -> None:
    assert Alternative("h3", ":443", {name: "1"}).persist is False
    assert Alternative("h3", ":443", {"persist": "0", name: "1"}).persist is False


@pytest.mark.parametrize("name", ["persist", "PERSIST", "Persist"])
def test_ascii_case_variants_enable_persistence(name: str) -> None:
    assert Alternative("h3", ":443", {name: "1"}).persist is True


@pytest.mark.parametrize("name", ["ma", "MA", "Ma"])
@pytest.mark.parametrize(
    "read",
    [
        pytest.param(lambda item: item.ma, id="ma"),
        pytest.param(lambda item: item.max_age, id="max_age"),
        pytest.param(lambda item: expires_at(item, 100), id="expires_at"),
        pytest.param(lambda item: is_fresh(item, 100, 100), id="is_fresh"),
    ],
)
def test_empty_lifetime_is_invalid(name: str, read: Callable[[Alternative], object]) -> None:
    item = Alternative("h3", ":443", {name: ""})
    with pytest.raises(AltSvcError) as caught:
        read(item)
    assert caught.value.code == "ma.invalid"


def test_missing_lifetime_keeps_the_default() -> None:
    item = Alternative("h3", ":443")
    assert item.ma is None
    assert item.max_age == DEFAULT_MAX_AGE == 86400
    assert expires_at(item, 100) == 86500
    assert is_fresh(item, 100, 86499)
    assert not is_fresh(item, 100, 86500)
