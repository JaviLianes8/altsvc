"""Every finding has a code, a severity and the offset where it starts."""

from __future__ import annotations

import pytest

from altsvc import Issue, lint


def _found(value: str | list[str]) -> list[tuple[str, str, int | None]]:
    return [(issue.code, issue.severity, issue.offset) for issue in lint(value)]


def test_a_valid_value_has_no_findings() -> None:
    assert lint('h3=":443"; ma=86400, h2="alt.example.com:443"; persist=1') == []


def test_findings_are_issue_objects() -> None:
    (issue,) = lint("")
    assert isinstance(issue, Issue)
    assert issue == Issue("empty", "the value holds no alternative", "error", 0)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("", [("empty", "error", 0)]),
        (" , ,\t", [("empty", "error", 0)]),
        ('h3 = ":443"', [("syntax.space", "error", 2)]),
        ('h3=":443"; ma = 5', [("syntax.space", "error", 13)]),
        ("h3", [("syntax.equals", "error", 2)]),
        ('h3=":443"; persist', [("syntax.equals", "error", 18)]),
        ("h3=:443", [("syntax.authority", "error", 3)]),
        ('h3=":443"; ma=', [("syntax.value", "error", 14)]),
        ('h3=":443', [("syntax.quoted-string", "error", 3)]),
        ('h3=":4\x0043"', [("syntax.quoted-string", "error", 6)]),
        ('h3=":443" x', [("syntax.comma", "error", 10)]),
        ('h3=":443";', [("syntax.empty-parameter", "error", 9)]),
        ('h3=":443"; ; ma=1', [("syntax.empty-parameter", "error", 9)]),
        ('=":443"', [("syntax.token", "error", 0)]),
        ('h3=":443"; ="1"', [("syntax.token", "error", 11)]),
        ('h3=":443", clear', [("clear.mixed", "error", 11)]),
        ('clear, h3=":443"', [("clear.mixed", "error", 7)]),
        ("clear, clear", [("clear.mixed", "error", 7)]),
        ('h3%3a=":443"', [("protocol-id.canonical", "error", 0)]),
        ('%68%33=":443"', [("protocol-id.canonical", "error", 0)]),
        ('h3%4=":443"', [("protocol-id.percent", "error", 2)]),
        ('spdy%2F3=":443"', [("protocol.not-http", "warning", 0)]),
        ('h3="example.org"', [("authority.port", "error", 3)]),
        ('h3=":0"', [("authority.port", "error", 3)]),
        ('h3=":65536"', [("authority.port", "error", 3)]),
        ('h3="a b:443"', [("authority.host", "error", 3)]),
        ('h3="b\u00fccher.example:443"', [("authority.host", "error", 3)]),
        ('h3="[::g]:443"', [("authority.host", "error", 3)]),
        ('h3=":443"; ma=x', [("ma.invalid", "error", 11)]),
        ('h3=":443"; ma="-1"', [("ma.invalid", "error", 11)]),
        ('h3=":443"; ma=2147483649', [("ma.capped", "warning", 11)]),
        ('h3=":443"; persist=0', [("persist.ignored", "warning", 11)]),
        ('h3=":443"; ma=1; MA=2', [("parameter.duplicate", "warning", 17)]),
    ],
)
def test_each_finding_has_its_code_and_offset(
    value: str, expected: list[tuple[str, str, int]]
) -> None:
    assert _found(value) == expected


def test_findings_come_in_the_order_they_occur() -> None:
    value = 'h3=":0"; persist=2, x y, h2=":443"; ma=1; ma=2'
    assert [code for code, _, _ in _found(value)] == [
        "authority.port",
        "persist.ignored",
        "syntax.equals",
        "parameter.duplicate",
    ]


def test_several_field_lines_are_one_list_and_offsets_count_the_joint() -> None:
    assert _found(['h3=":443"', "h2=:1"]) == [("syntax.authority", "error", 14)]


def test_the_maximum_ma_itself_is_not_reported_as_capped() -> None:
    assert lint('h3=":443"; ma=2147483648') == []
    assert lint('h3=":443"; ma=0002147483648') == []


def test_a_comma_inside_a_broken_quoted_string_does_not_start_an_alternative() -> None:
    assert _found('h3=":443" "x, y", h2=":1"') == [("syntax.comma", "error", 10)]


def test_unknown_parameters_are_not_findings() -> None:
    assert lint('h3=":443"; foo=bar; v="1,2"') == []


def test_ma_zero_and_leading_zeros_are_valid() -> None:
    assert lint('h3=":443"; ma=0, h2=":443"; ma=007') == []


def test_bytes_input_gets_a_clear_type_error() -> None:
    with pytest.raises(TypeError, match="decode"):
        lint(b'h3=":443"')  # type: ignore[arg-type]


def test_a_list_with_non_text_gets_a_type_error() -> None:
    with pytest.raises(TypeError, match="sequence of str"):
        lint(['h3=":443"', 5])  # type: ignore[list-item]
