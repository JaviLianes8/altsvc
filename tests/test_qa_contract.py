"""Hand-written contracts for argument types, stored values and persistence."""

from __future__ import annotations

from typing import cast

import pytest

from altsvc import Alternative, AltSvcError, Issue, encode_protocol_id, expires_at, lint, parse


@pytest.mark.parametrize("strict", [None, 0, 1, "False", [], {}])
def test_strict_requires_a_boolean(strict: object) -> None:
    with pytest.raises(TypeError):
        parse('h3=":443"', strict=cast(bool, strict))


@pytest.mark.parametrize("value", [None, True, 3, 1.5, [], {}, object()])
@pytest.mark.parametrize("accessor", ["host", "port"])
def test_authority_accessors_reject_wrong_types(value: object, accessor: str) -> None:
    item = Alternative("h3", cast(str, value))
    with pytest.raises(TypeError):
        getattr(item, accessor)


@pytest.mark.parametrize("params", [None, [], True, 3, {3: "1"}, {"ma": None}, {"persist": 1}])
@pytest.mark.parametrize("accessor", ["ma", "max_age", "persist"])
def test_parameter_accessors_reject_malformed_storage(params: object, accessor: str) -> None:
    item = Alternative("h3", ":443", cast(dict[str, str], params))
    with pytest.raises(TypeError):
        getattr(item, accessor)


def test_freshness_rejects_present_none_lifetime() -> None:
    item = Alternative("h3", ":443", cast(dict[str, str], {"ma": None}))
    with pytest.raises(TypeError):
        expires_at(item, 0)


def test_accessors_validate_only_the_relevant_fields() -> None:
    item = Alternative(cast(str, None), ":443", cast(dict[str, str], None))
    assert (item.host, item.port) == ("", 443)
    item = Alternative(cast(str, None), cast(str, None), {"ma": "0"})
    assert item.max_age == 0


@pytest.mark.parametrize("strict", [False, True])
@pytest.mark.parametrize("name", ["persist", "PERSIST", "Persist"])
@pytest.mark.parametrize("value", ["0", "2", "yes", '""', "01", '" 1"', '"0"'])
def test_ignored_persistence_cannot_cancel_one(strict: bool, name: str, value: str) -> None:
    field = f'h3=":443"; persist="1"; {name}={value}; persist=0'
    result = parse(field, strict=strict)
    assert isinstance(result, list)
    assert result[0].persist is True
    assert result[0].params == {"persist": "1"}
    assert "persist.ignored" in [issue.code for issue in lint(field)]


def test_issue_has_no_writable_instance_dictionary() -> None:
    issue = Issue("x", "original", "error")
    with pytest.raises(TypeError):
        vars(issue)
    assert issue.message == "original"


@pytest.mark.parametrize("value", [b"", ""])
def test_empty_alpn_has_specific_error_code(value: str | bytes) -> None:
    with pytest.raises(AltSvcError) as caught:
        encode_protocol_id(value)
    assert caught.value.code == "protocol-id.empty"
