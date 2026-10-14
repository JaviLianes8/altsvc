import pytest

from altsvc import CLEAR, Alternative, AltSvcError, build, parse


def test_build_single_alternative() -> None:
    assert build([Alternative("h3", ":443")]) == 'h3=":443"'


def test_build_with_parameters() -> None:
    header = build([Alternative("h3", ":443", {"ma": "3600", "persist": "1"})])
    assert header == 'h3=":443"; ma=3600; persist=1'


def test_build_multiple_alternatives() -> None:
    header = build(
        [
            Alternative("h2", "alt.example.com:443"),
            Alternative("h3", ":443"),
        ]
    )
    assert header == 'h2="alt.example.com:443", h3=":443"'


def test_build_clear() -> None:
    assert build(CLEAR) == "clear"


def test_build_refuses_an_empty_sequence() -> None:
    with pytest.raises(AltSvcError) as caught:
        build([])
    assert caught.value.code == "empty"


def test_build_quotes_non_token_parameter_value() -> None:
    assert build([Alternative("h2", ":443", {"note": "a b"})]) == 'h2=":443"; note="a b"'


def test_build_refuses_a_quote_in_the_authority() -> None:
    with pytest.raises(AltSvcError) as caught:
        build([Alternative("h2", 'x"y:443')])
    assert caught.value.code == "authority.host"


def test_build_rejects_invalid_protocol() -> None:
    with pytest.raises(AltSvcError):
        build([Alternative("bad proto", ":443")])


def test_build_rejects_invalid_parameter_name() -> None:
    with pytest.raises(AltSvcError):
        build([Alternative("h3", ":443", {"bad name": "1"})])


def test_round_trip_alternatives() -> None:
    alternatives = [
        Alternative("h2", "alt.example.com:443", {"ma": "7200"}),
        Alternative("h3", ":443", {"ma": "3600", "persist": "1"}),
    ]
    assert parse(build(alternatives)) == alternatives


def test_round_trip_clear() -> None:
    assert parse(build(CLEAR)) is CLEAR
