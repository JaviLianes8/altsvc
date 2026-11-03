"""Hand-written contracts for parameter mappings, names and exact stored values."""

from __future__ import annotations

from collections import UserDict
from collections.abc import Callable, ItemsView, Mapping
from types import MappingProxyType
from typing import cast

import pytest

from altsvc import DEFAULT_MAX_AGE, Alternative, AltSvcError, expires_at, is_fresh


class ItemsOnly:
    def items(self) -> ItemsView[str, str]:
        return {"ma": "1", "persist": "1"}.items()


@pytest.mark.parametrize("accessor", ["ma", "max_age", "persist"])
def test_parameter_accessors_reject_items_only_non_mappings(accessor: str) -> None:
    params = ItemsOnly()
    assert not isinstance(params, Mapping)
    item = Alternative("h3", ":443", cast(dict[str, str], params))
    with pytest.raises(TypeError):
        getattr(item, accessor)


@pytest.mark.parametrize("padding", [" {}", "{} ", " {} ", "\t{}", "{}\t", "\t{} \t"])
@pytest.mark.parametrize(
    ("name", "accessor", "missing", "existing"),
    [
        ("ma", "ma", None, 7),
        ("ma", "max_age", DEFAULT_MAX_AGE, 7),
        ("persist", "persist", False, False),
    ],
)
def test_whitespace_padded_parameter_names_remain_unmatched(
    padding: str, name: str, accessor: str, missing: object, existing: object
) -> None:
    padded = padding.format(name)
    item = Alternative("h3", ":443", {padded: "1"})
    assert getattr(item, accessor) == missing
    item = Alternative("h3", ":443", {"ma": "7", "persist": "0", padded: "1"})
    assert getattr(item, accessor) == existing


@pytest.mark.parametrize("mapping", [UserDict, MappingProxyType])
@pytest.mark.parametrize(
    ("read", "expected"),
    [
        pytest.param(lambda item: item.ma, 1, id="ma"),
        pytest.param(lambda item: item.max_age, 1, id="max_age"),
        pytest.param(lambda item: item.persist, True, id="persist"),
    ],
)
def test_parameter_accessors_accept_non_dict_mappings(
    mapping: Callable[[dict[str, str]], Mapping[str, str]],
    read: Callable[[Alternative], object],
    expected: object,
) -> None:
    params = mapping({"ma": "1", "persist": "1"})
    # The unvalidated constructor's runtime mapping contract is broader than its annotation.
    item = Alternative("h3", ":443", cast(dict[str, str], params))
    assert read(item) == expected


@pytest.mark.parametrize("value", [" 1", "1 ", " 1 ", "\t1", "1\t", "\t1 \t"])
def test_whitespace_padded_persistence_is_false(value: str) -> None:
    assert Alternative("h3", ":443", {"persist": value}).persist is False


@pytest.mark.parametrize("value", [" 1", "1 ", " 1 ", "\t1", "1\t", "\t1 \t"])
@pytest.mark.parametrize(
    "read",
    [
        pytest.param(lambda item: item.ma, id="ma"),
        pytest.param(lambda item: item.max_age, id="max_age"),
        pytest.param(lambda item: expires_at(item, 100), id="expires_at"),
        pytest.param(lambda item: is_fresh(item, 100, 100), id="is_fresh"),
    ],
)
def test_whitespace_padded_lifetime_is_invalid(
    value: str, read: Callable[[Alternative], object]
) -> None:
    item = Alternative("h3", ":443", {"ma": value})
    with pytest.raises(AltSvcError) as caught:
        read(item)
    assert caught.value.code == "ma.invalid"


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
