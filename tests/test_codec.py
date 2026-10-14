"""Protocol-id percent-encoding and the parts of an alt-authority."""

from __future__ import annotations

import pytest

from altsvc import AltSvcError, decode_protocol_id, encode_protocol_id
from altsvc._codec import is_canonical_protocol_id, join_authority, split_authority


@pytest.mark.parametrize(
    ("name", "protocol_id"),
    [
        ("h2", "h2"),
        ("w=x:y#z", "w%3Dx%3Ay#z"),
        ("x%y", "x%25y"),
        ("http/1.1", "http%2F1.1"),
        (b"\x00\xff", "%00%FF"),
        ("caf\u00e9", "caf%C3%A9"),
    ],
)
def test_encode_and_decode_are_inverse(name: str | bytes, protocol_id: str) -> None:
    assert encode_protocol_id(name) == protocol_id
    octets = name.encode("utf-8") if isinstance(name, str) else name
    assert decode_protocol_id(protocol_id) == octets
    assert is_canonical_protocol_id(protocol_id)


def test_every_octet_round_trips() -> None:
    every = bytes(range(256))
    assert decode_protocol_id(encode_protocol_id(every)) == every


def test_decode_accepts_lower_case_hex_but_it_is_not_canonical() -> None:
    assert decode_protocol_id("w%3dx") == b"w=x"
    assert not is_canonical_protocol_id("w%3dx")
    assert not is_canonical_protocol_id("%68")


@pytest.mark.parametrize(("bad", "code"), [("", "protocol-id.token"), ("a b", "protocol-id.token")])
def test_decode_refuses_a_non_token(bad: str, code: str) -> None:
    with pytest.raises(AltSvcError) as caught:
        decode_protocol_id(bad)
    assert caught.value.code == code
    assert not is_canonical_protocol_id(bad)


@pytest.mark.parametrize(("bad", "offset"), [("%", 0), ("a%4", 1), ("a%zz", 1), ("%4%41", 0)])
def test_decode_refuses_a_broken_escape(bad: str, offset: int) -> None:
    with pytest.raises(AltSvcError) as caught:
        decode_protocol_id(bad)
    assert caught.value.code == "protocol-id.percent"
    assert caught.value.offset == offset


def test_encode_refuses_an_empty_name_and_other_types() -> None:
    with pytest.raises(AltSvcError):
        encode_protocol_id(b"")
    with pytest.raises(TypeError):
        encode_protocol_id(3)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        decode_protocol_id(b"h3")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("authority", "host", "port"),
    [
        (":443", "", 443),
        ("alt.example.com:8000", "alt.example.com", 8000),
        ("192.0.2.1:1", "192.0.2.1", 1),
        ("[2001:db8::1]:65535", "2001:db8::1", 65535),
        ("xn--bcher-kva.example:443", "xn--bcher-kva.example", 443),
        ("a%20b:443", "a%20b", 443),
        (":00443", "", 443),
    ],
)
def test_split_authority(authority: str, host: str, port: int) -> None:
    assert split_authority(authority) == (host, port)


@pytest.mark.parametrize(
    ("authority", "code"),
    [
        ("", "authority.port"),
        ("example.org", "authority.port"),
        ("example.org:", "authority.port"),
        (":0", "authority.port"),
        (":65536", "authority.port"),
        (":443443", "authority.port"),
        (":\u0664\u0664\u0663", "authority.port"),
        (":+443", "authority.port"),
        ("::1:443", "authority.host"),
        ("[::1:443", "authority.host"),
        ("[nothex]:443", "authority.host"),
        ("b\u00fccher.example:443", "authority.host"),
        ("a/b:443", "authority.host"),
        ("a%2:443", "authority.host"),
        ("a%zz:443", "authority.host"),
        ('a"b:443', "authority.host"),
        ("a\r\nb:443", "authority.host"),
    ],
)
def test_split_authority_refuses(authority: str, code: str) -> None:
    with pytest.raises(AltSvcError) as caught:
        split_authority(authority)
    assert caught.value.code == code


def test_join_authority_brackets_ipv6_only() -> None:
    assert join_authority("", 443) == ":443"
    assert join_authority("alt.example", 1) == "alt.example:1"
    assert join_authority("::1", 8443) == "[::1]:8443"
