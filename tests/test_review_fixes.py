"""Regression tests for the findings of the independent review."""

from __future__ import annotations

import pytest

from altsvc import Alternative, AltSvcError, build, lint, parse
from altsvc._codec import split_authority
from altsvc._head import field_lines


@pytest.mark.parametrize(
    "host",
    [
        "fe80::1%a\r\nSet-Cookie: x=1",
        "fe80::1%eth0",
        "fe80::1%25eth0",
        "::1%a]b",
        "::1%\u00e9",
        'fe80::1%"',
        "v1.x",
    ],
)
def test_an_ip_literal_carries_no_zone_id_or_other_text(host: str) -> None:
    with pytest.raises(AltSvcError) as caught:
        split_authority(f"[{host}]:443")
    assert caught.value.code == "authority.host"
    with pytest.raises(AltSvcError):
        build([Alternative("h3", f"[{host}]:443")])
    assert parse(f'h3="[{host}]:443"') == []


def test_of_cannot_smuggle_a_line_break_through_an_ipv6_host() -> None:
    with pytest.raises(AltSvcError):
        Alternative.of("h3", 443, "fe80::1%x\r\nX: y")


def test_an_ipv4_mapped_ipv6_literal_is_fine() -> None:
    assert split_authority("[::ffff:192.0.2.1]:443") == ("::ffff:192.0.2.1", 443)


def test_messages_carry_no_offset_of_their_own() -> None:
    (issue,) = lint(['h3=":443"', 'h2=":0"'])
    assert issue.offset == 14
    assert issue.message == "port must be 1 to 65535 in ':0'"
    with pytest.raises(AltSvcError) as caught:
        parse('h3=":0"', strict=True)
    assert str(caught.value) == "port must be 1 to 65535 in ':0' (at offset 3)"
    assert caught.value.message == "port must be 1 to 65535 in ':0'"


def test_build_wants_a_mapping_of_params() -> None:
    for params in ([("a", "b")], None):
        with pytest.raises(TypeError, match="mapping"):
            build([Alternative("h3", ":443", params)])  # type: ignore[arg-type]


class _Hollow(list[Alternative]):
    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(())


def test_build_checks_what_it_iterates_not_what_len_says() -> None:
    with pytest.raises(AltSvcError) as caught:
        build(_Hollow([Alternative("h3", ":443")]))
    assert caught.value.code == "empty"


def test_the_last_ma_decides_like_every_repeated_parameter() -> None:
    assert parse('h3=":443"; ma=x; ma=5') == [Alternative("h3", ":443", {"ma": "5"})]
    assert parse('h3=":443"; ma=5; ma=x') == []
    assert [issue.code for issue in lint('h3=":443"; ma=x; ma=5')] == [
        "ma.invalid",
        "parameter.duplicate",
    ]


@pytest.mark.parametrize("value", [{'h3=":443"': 1}, {'h3=":443"'}, iter(['h3=":443"'])])
def test_only_text_or_a_sequence_of_text_is_read(value: object) -> None:
    with pytest.raises(TypeError):
        parse(value)  # type: ignore[arg-type]


def test_a_body_line_that_starts_with_http_does_not_start_a_response() -> None:
    text = 'HTTP/1.1 200 OK\r\nAlt-Svc: h3=":443"\r\n\r\nHTTP/1.1 is fun\r\nAlt-Svc: x\r\n'
    assert field_lines(text) == ("200", ['h3=":443"'])


@pytest.mark.parametrize("prefix", ["\ufeff", "\xef\xbb\xbf", "  "])
def test_a_bom_or_indentation_before_the_head_is_skipped(prefix: str) -> None:
    assert field_lines(prefix + 'HTTP/2 200\nalt-svc: h3=":443"\n') == ("200", ['h3=":443"'])
    assert field_lines(prefix + "Alt-Svc: clear\n") == ("", ["clear"])


@pytest.mark.parametrize("value", ["clear,", ", clear", ["clear", ""]])
def test_clear_is_a_whole_value_not_a_list_member(value: str | list[str]) -> None:
    assert [(issue.code, issue.severity) for issue in lint(value)] == [("clear.list", "error")]
    with pytest.raises(AltSvcError):
        parse(value, strict=True)
    assert parse(" clear\t", strict=True) is parse(value)


def test_an_unregistered_draft_id_is_not_called_non_http() -> None:
    (issue,) = lint('h3-29=":443"')
    assert issue.message == "'h3-29' is not a registered HTTP ALPN id (IANA ALPN registry)"


def test_of_accepts_a_bracketed_ipv6_host() -> None:
    assert Alternative.of("h3", 443, "[::1]") == Alternative("h3", "[::1]:443")
