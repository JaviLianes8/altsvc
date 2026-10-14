"""Strict reading raises on the first error; tolerant reading keeps what is sound."""

from __future__ import annotations

import pytest

from altsvc import CLEAR, Alternative, AltSvcError, parse


def test_strict_accepts_a_valid_value() -> None:
    value = 'h3=":443"; ma=3600, h2="alt.example.com:443"; persist=1'
    assert parse(value, strict=True) == parse(value)


@pytest.mark.parametrize(
    ("value", "code", "offset"),
    [
        ("", "empty", 0),
        ('h3=":443";', "syntax.empty-parameter", 9),
        ('h3=":443", clear', "clear.mixed", 11),
        ('h3=":443"; ma=x, h2=":0"', "ma.invalid", 11),
        ('h3=":443"; persist=0, h2 = ":1"', "syntax.space", 24),
    ],
)
def test_strict_raises_the_first_error_with_code_and_offset(
    value: str, code: str, offset: int
) -> None:
    with pytest.raises(AltSvcError) as caught:
        parse(value, strict=True)
    assert caught.value.code == code
    assert caught.value.offset == offset
    assert f"(at offset {offset})" in str(caught.value)


def test_warnings_do_not_make_strict_raise() -> None:
    value = 'h3=":443"; ma=1; ma=2; persist=yes; ma=99999999999'
    assert parse(value, strict=True) == [
        Alternative("h3", ":443", {"ma": "99999999999", "persist": "yes"})
    ]


def test_strict_reads_clear() -> None:
    assert parse(" clear ", strict=True) is CLEAR


def test_tolerant_reads_clear_next_to_alternatives_as_clear() -> None:
    assert parse('h3=":443", clear') is CLEAR
    assert parse(['h3=":443"', "clear"]) is CLEAR


def test_tolerant_drops_an_alternative_with_a_bad_authority_or_ma() -> None:
    value = 'h3=":0", h3="a b:1", h3=":443"; ma=x, h3=":443"; ma="7"'
    assert parse(value) == [Alternative("h3", ":443", {"ma": "7"})]


def test_tolerant_drops_an_alternative_whose_ma_is_broken() -> None:
    assert parse('h3=":443"; ma = 5, h2=":443"; ma') == []


def test_tolerant_ignores_a_broken_parameter_of_another_name() -> None:
    value = 'h3=":443"; foo = 1; ;persist=1; bar'
    assert parse(value) == [Alternative("h3", ":443", {"persist": "1"})]


def test_tolerant_drops_an_alternative_followed_by_junk() -> None:
    assert parse('h3=":443" junk, h2=":443"') == [Alternative("h2", ":443")]


def test_tolerant_drops_a_non_canonical_protocol_id() -> None:
    assert parse('%68%33=":443", h3=":443"') == [Alternative("h3", ":443")]


def test_clear_is_case_sensitive_in_both_modes() -> None:
    assert parse("Clear") == []
    with pytest.raises(AltSvcError) as caught:
        parse("CLEAR", strict=True)
    assert caught.value.code == "syntax.equals"


def test_several_field_lines_combine_in_order() -> None:
    assert parse(['h3=":443"', 'h2=":443"'], strict=True) == [
        Alternative("h3", ":443"),
        Alternative("h2", ":443"),
    ]


def test_an_unclosed_quote_swallows_the_rest_of_the_value() -> None:
    assert parse('h3=":443", h2="a:1, h3=":8443"') == [Alternative("h3", ":443")]


def test_obs_text_inside_a_quoted_value_is_kept() -> None:
    assert parse('h3=":443"; note="caf\u00e9"') == [
        Alternative("h3", ":443", {"note": "caf\u00e9"})
    ]


def test_a_control_character_in_an_unknown_value_drops_only_that_parameter() -> None:
    assert parse('h3=":443"; note="a\rb"; ma=5') == [Alternative("h3", ":443", {"ma": "5"})]
