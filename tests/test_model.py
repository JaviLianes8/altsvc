"""The Alternative accessors, its factory, and the cache helpers."""

from __future__ import annotations

import pytest

from altsvc import (
    DEFAULT_MAX_AGE,
    DELTA_SECONDS_MAX,
    Alternative,
    AltSvcError,
    expires_at,
    is_fresh,
    parse,
)


def _one(value: str) -> Alternative:
    result = parse(value, strict=True)
    assert isinstance(result, list)
    return result[0]


def test_accessors_read_every_part() -> None:
    alternative = _one('w%3Dx%3Ay#z="[2001:db8::1]:8443"; ma=60; persist=1')
    assert alternative.alpn == b"w=x:y#z"
    assert alternative.host == "2001:db8::1"
    assert alternative.port == 8443
    assert alternative.ma == 60
    assert alternative.max_age == 60
    assert alternative.persist is True


def test_ma_defaults_to_one_day() -> None:
    alternative = _one('h3=":443"')
    assert alternative.ma is None
    assert alternative.max_age == DEFAULT_MAX_AGE == 86400
    assert alternative.host == ""


def test_ma_is_capped_without_converting_long_digit_strings() -> None:
    assert _one('h3=":443"; ma=' + "9" * 6000).ma == DELTA_SECONDS_MAX == 2**31
    assert _one('h3=":443"; ma=2147483649').ma == DELTA_SECONDS_MAX
    assert _one('h3=":443"; ma=2147483647').ma == 2147483647
    assert _one('h3=":443"; ma=00000000000000000000000000012').ma == 12


def test_parameter_names_are_matched_without_case_and_the_last_wins() -> None:
    alternative = _one('h3=":443"; MA=1; Persist=1; ma=2')
    assert alternative.ma == 2
    assert alternative.persist is True
    assert _one('h3=":443"; persist=1; persist=0').persist is False


def test_persist_means_only_the_value_one() -> None:
    assert _one('h3=":443"; persist="1"').persist is True
    assert _one('h3=":443"; persist=01').persist is False


def test_accessors_raise_on_a_hand_made_bad_alternative() -> None:
    bad = Alternative("%zz", "nope", {"ma": "\u0661"})
    for read in (lambda: bad.alpn, lambda: bad.host, lambda: bad.port, lambda: bad.ma):
        with pytest.raises(AltSvcError):
            read()


def test_of_encodes_brackets_and_adds_parameters() -> None:
    made = Alternative.of("w=x:y#z", 8443, "::1", ma=60, persist=True, params={"foo": "a b"})
    assert made == Alternative(
        "w%3Dx%3Ay#z", "[::1]:8443", {"foo": "a b", "ma": "60", "persist": "1"}
    )
    assert Alternative.of(b"h3", 443) == Alternative("h3", ":443")


@pytest.mark.parametrize(
    "call",
    [
        lambda: Alternative.of("h3", 0),
        lambda: Alternative.of("h3", 443, "a b"),
        lambda: Alternative.of("h3", 443, ma=-1),
        lambda: Alternative.of("h3", 443, ma=2**31 + 1),
        lambda: Alternative.of("", 443),
        lambda: Alternative.of("h3", 443, params={"x": "a\r\nb"}),
    ],
)
def test_of_refuses_what_build_refuses(call: object) -> None:
    with pytest.raises(AltSvcError):
        call()  # type: ignore[operator]


def test_rfc_age_example_fresh_for_the_rest_of_ma() -> None:
    # RFC 7838 section 3.1: ma=60 with Age: 30 leaves 30 seconds from receipt.
    alternative = _one('h2=":8000"; ma=60')
    assert expires_at(alternative, 1000.0, age=30) == 1030.0
    assert is_fresh(alternative, 1000.0, 1029.9, age=30)
    assert not is_fresh(alternative, 1000.0, 1030.0, age=30)


def test_expiry_defaults_and_never_goes_back_in_time() -> None:
    assert expires_at(_one('h3=":443"'), 5.0) == 5.0 + 86400
    assert expires_at(_one('h3=":443"; ma=10'), 5.0, age=99) == 5.0
    assert not is_fresh(_one('h3=":443"; ma=0'), 5.0, 5.0)


def test_expiry_refuses_a_negative_age() -> None:
    with pytest.raises(AltSvcError) as caught:
        expires_at(_one('h3=":443"'), 0.0, age=-1)
    assert caught.value.code == "age.negative"


@pytest.mark.parametrize(
    ("age", "received_at"), [(True, 0.0), (1.5, 0.0), (0, "0"), (0, False), (0, None)]
)
def test_expiry_refuses_wrong_types(age: object, received_at: object) -> None:
    with pytest.raises(TypeError):
        expires_at(_one('h3=":443"'), received_at, age=age)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "call",
    [
        lambda: Alternative.of("h3", True),
        lambda: Alternative.of("h3", "443"),  # type: ignore[arg-type]
        lambda: Alternative.of("h3", 443, ma=True),
        lambda: Alternative.of("h3", 443, ma="60"),  # type: ignore[arg-type]
        lambda: Alternative.of("h3", 443, persist=1),  # type: ignore[arg-type]
        lambda: Alternative.of("h3", 443, host=None),  # type: ignore[arg-type]
    ],
)
def test_of_refuses_wrong_types(call: object) -> None:
    with pytest.raises(TypeError):
        call()  # type: ignore[operator]
