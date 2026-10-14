"""Edge cases found by changing the guarded logic one piece at a time."""

from __future__ import annotations

import pytest

from altsvc import Alternative, AltSvcError, build, lint, parse
from altsvc._codec import split_authority
from altsvc._head import field_lines


def test_the_top_octet_of_obs_text_is_kept_in_a_quoted_value() -> None:
    assert parse('h3=":443"; n="\xff"') == [Alternative("h3", ":443", {"n": "\xff"})]


def test_a_quoted_pair_may_escape_any_visible_character() -> None:
    assert parse(r'h3=":443"; n="\!\~"') == [Alternative("h3", ":443", {"n": "!~"})]


def test_a_quoted_pair_may_not_escape_a_control_character() -> None:
    assert [issue.code for issue in lint('h3=":443"; n="a\\\x00"')] == ["syntax.quoted-string"]


def test_build_refuses_delete() -> None:
    with pytest.raises(AltSvcError) as caught:
        build([Alternative("h3", ":443", {"n": "a\x7fb"})])
    assert caught.value.code == "parameter.value"


def test_ports_may_have_leading_zeros_but_not_more_than_five_digits() -> None:
    assert split_authority(":000443") == ("", 443)
    assert split_authority(":0000000065535") == ("", 65535)
    for port in ("443443", "100000", "9" * 6000, "000"):
        with pytest.raises(AltSvcError):
            split_authority(":" + port)


def test_a_non_ascii_host_is_reported_as_needing_a_labels() -> None:
    with pytest.raises(AltSvcError, match="A-labels"):
        split_authority("b\u00fccher.example:443")


def test_of_refuses_a_bool_port_as_a_type_error() -> None:
    with pytest.raises(TypeError, match="port"):
        Alternative.of("h3", True)


def test_clear_mixed_points_at_the_second_element() -> None:
    issues = lint('clear, h3=":443", h2=":443"')
    assert [(issue.code, issue.offset) for issue in issues] == [("clear.mixed", 7)]


def test_build_refuses_a_huge_ma_without_converting_it() -> None:
    with pytest.raises(AltSvcError) as caught:
        build([Alternative("h3", ":443", {"ma": "9" * 6000})])
    assert caught.value.code == "ma.invalid"


def test_a_field_in_the_body_after_the_head_is_not_read() -> None:
    text = 'HTTP/1.1 200 OK\r\nAlt-Svc: h3=":443"\r\n\r\nAlt-Svc: clear\r\n'
    assert field_lines(text) == ("200", ['h3=":443"'])


def test_an_ip_literal_of_hex_digits_must_still_be_an_ipv6_address() -> None:
    for host in ("[1:2]", "[12345::]", "[::1::2]", "[]"):
        with pytest.raises(AltSvcError):
            split_authority(host + ":443")


def test_tolerant_reading_drops_a_protocol_id_with_a_broken_escape() -> None:
    assert parse('h3%4=":443", h2=":443"') == [Alternative("h2", ":443")]


def test_a_body_line_like_a_four_digit_status_does_not_start_a_response() -> None:
    text = 'HTTP/1.1 200 OK\r\nAlt-Svc: h3=":443"\r\n\r\nHTTP/1.1 2000\r\nAlt-Svc: x\r\n'
    assert field_lines(text) == ("200", ['h3=":443"'])
