from altsvc import CLEAR, Alternative, parse


def test_single_alternative() -> None:
    assert parse('h3=":443"') == [Alternative("h3", ":443")]


def test_authority_with_host() -> None:
    assert parse('h2="alt.example.com:443"') == [Alternative("h2", "alt.example.com:443")]


def test_multiple_alternatives() -> None:
    result = parse('h2="alt.example.com:443", h3=":443"')
    assert result == [
        Alternative("h2", "alt.example.com:443"),
        Alternative("h3", ":443"),
    ]


def test_ma_and_persist_parameters() -> None:
    result = parse('h3=":443"; ma=3600; persist=1')
    assert result == [Alternative("h3", ":443", {"ma": "3600", "persist": "1"})]


def test_parameters_expose_typed_helpers() -> None:
    result = parse('h3=":443"; ma=3600; persist=1')
    assert isinstance(result, list)
    assert result[0].ma == 3600
    assert result[0].persist is True


def test_missing_parameters_default() -> None:
    result = parse('h3=":443"')
    assert isinstance(result, list)
    assert result[0].ma is None
    assert result[0].persist is False


def test_clear_token() -> None:
    assert parse("clear") is CLEAR


def test_clear_is_case_sensitive() -> None:
    assert parse("Clear") == []


def test_quoted_value_with_comma_is_not_a_separator() -> None:
    result = parse('h2="a,b:443"; ma=10')
    assert result == [Alternative("h2", "a,b:443", {"ma": "10"})]


def test_quoted_parameter_value() -> None:
    result = parse('h2=":443"; note="a;b"')
    assert result == [Alternative("h2", ":443", {"note": "a;b"})]


def test_escaped_quote_inside_authority() -> None:
    result = parse('h2="say \\"hi\\":443"')
    assert result == [Alternative("h2", 'say "hi":443')]


def test_surrounding_whitespace_is_ignored() -> None:
    assert parse('  h3=":443" ') == [Alternative("h3", ":443")]


def test_malformed_alternative_is_skipped() -> None:
    result = parse('garbage, h3=":443", noequalsign')
    assert result == [Alternative("h3", ":443")]


def test_unquoted_authority_is_skipped() -> None:
    assert parse("h3=:443") == []


def test_empty_header_is_empty_list() -> None:
    assert parse("") == []
