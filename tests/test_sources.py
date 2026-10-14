"""Check the library against the pinned RFCs, IANA registries and two shipping parsers.

The files are read from tests/upstream (URL, revision, size and sha256 in MANIFEST.json);
the tests that read them skip until `python scripts/fetch_upstream.py` has fetched them.
"""

from __future__ import annotations

import csv
import io
import re
import string
from collections.abc import Callable

import pytest

from altsvc import (
    DEFAULT_MAX_AGE,
    DELTA_SECONDS_MAX,
    Alternative,
    encode_protocol_id,
    expires_at,
    parse,
)
from altsvc._chars import OWS, REG_NAME, TCHAR
from altsvc._codec import HTTP_ALPN_IDS

Reader = Callable[[str], str]


def _flat(text: str) -> str:
    return " ".join(text.split())


def _section(text: str, start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]


def _group(pattern: str, text: str) -> str:
    match = re.search(pattern, text)
    assert match is not None, pattern
    return match.group(1)


def _alternatives(value: str) -> list[Alternative]:
    result = parse(value, strict=True)
    assert isinstance(result, list)
    return result


def test_every_rfc_7838_field_example_reads_strictly(upstream: Reader) -> None:
    text = _section(upstream("rfc7838.txt"), "\n3.  The Alt-Svc", "\n4.  The ALTSVC")
    values = re.findall(r"^ +Alt-Svc: (.+)$", text, flags=re.MULTILINE)
    assert [_alternatives(value) for value in values] == [
        [Alternative("h2", ":8000")],
        [Alternative("h2", "new.example.org:80")],
        [Alternative("h2", "alt.example.com:8000"), Alternative("h2", ":443")],
        [Alternative("h2", ":443", {"ma": "3600"})],
        [Alternative("h2", ":8000", {"ma": "60"})],
        [Alternative("h2", ":443", {"ma": "2592000", "persist": "1"})],
    ]


def test_the_rfc_7838_escaping_table_is_what_encode_writes(upstream: Reader) -> None:
    rows = re.findall(r"^ +\| (\S+) +\| (\S+) +\|", upstream("rfc7838.txt"), flags=re.MULTILINE)
    table = [(name, protocol_id) for name, protocol_id in rows if name in ("h2", "w=x:y#z", "x%y")]
    assert table == [("h2", "h2"), ("w=x:y#z", "w%3Dx%3Ay#z"), ("x%y", "x%25y")]
    for name, protocol_id in table:
        assert encode_protocol_id(name) == protocol_id


def test_the_rules_this_library_applies_are_in_rfc_7838(upstream: Reader) -> None:
    # Short citations of https://www.rfc-editor.org/rfc/rfc7838.txt sections 3, 3.1, 6 and 8.
    flat = _flat(upstream("rfc7838.txt"))
    for rule in (
        'clear = %s"clear"; "clear", case-sensitive',
        'alt-value = alternative *( OWS ";" OWS parameter )',
        'alt-authority = quoted-string ; containing [ uri-host ] ":" port',
        'parameter = token "=" ( token / quoted-string )',
        "uppercase hex digits MUST be used",
        "Unknown parameters MUST be ignored",
        "fresh for 24 hours",
        "ma = delta-seconds",
        'persist = "1"',
        "MUST be expressed using A-labels",
        "An Alt-Svc header field in a 421 (Misdirected Request) response MUST be ignored",
    ):
        assert rule in flat, rule
    assert DEFAULT_MAX_AGE == 24 * 3600


def test_the_age_example_of_section_3_1(upstream: Reader) -> None:
    example = _section(upstream("rfc7838.txt"), "For example, a response:", "indicates")
    age = int(_group(r"Age: (\d+)", example))
    (alternative,) = _alternatives(_group(r"Alt-Svc: (.+)", example))
    assert expires_at(alternative, 0.0, age=age) == 30.0


def test_the_errata_do_not_touch_the_grammar(upstream: Reader) -> None:
    page = _flat(re.sub(r"<[^>]+>", " ", upstream("rfc7838-errata.html")))
    assert sorted(re.findall(r"Errata-ID: (\d+)", page)) == ["6480", "6481"]
    assert page.count("Type: Editorial") == 2
    assert "Type: Technical" not in page


def test_the_rfc_9114_h3_example(upstream: Reader) -> None:
    (alternative,) = _alternatives(_group(r"Alt-Svc: (h3=.+)", upstream("rfc9114.txt")))
    assert (alternative.alpn, alternative.host, alternative.port) == (b"h3", "", 50781)


def test_the_rfc_9460_interaction_example(upstream: Reader) -> None:
    text = upstream("rfc9460.txt")
    value = _group(r"Alt-Svc: (h2=.+)", _section(text, "9.3.  Interaction", "\n10."))
    assert [(a.alpn, a.host, a.port) for a in _alternatives(value)] == [
        (b"h2", "alt.example", 443),
        (b"h2", "alt2.example", 443),
        (b"h3", "", 8443),
    ]
    assert 'no SvcParamKey corresponding to the Alt-Svc "ma"' in _flat(text)


def test_the_delta_seconds_ceiling_comes_from_rfc_9111(upstream: Reader) -> None:
    text = upstream("rfc9111.txt")
    rule = _flat(_section(text, "Delta Seconds\n\n", "\n1.3."))
    assert "delta-seconds = 1*DIGIT" in rule
    assert f"to be {DELTA_SECONDS_MAX} (2^31)" in rule


def test_tchar_ows_and_the_list_rule_match_rfc_9110(upstream: Reader) -> None:
    text = upstream("rfc9110.txt")
    symbols = set(re.findall(r'"(.)"', _section(text, "     tchar          =", "; any VCHAR")))
    assert symbols | set(string.ascii_letters + string.digits) == TCHAR
    assert "OWS            = *( SP / HTAB )" in text
    assert OWS == " \t"
    assert '#element => [ element ] *( OWS "," OWS [ element ] )' in text


def test_reg_name_characters_match_rfc_3986(upstream: Reader) -> None:
    text = upstream("rfc3986.txt")
    sub = set(re.findall(r'"(.)"', _section(text, "      sub-delims  =", "\n\n")))
    unreserved = set(string.ascii_letters + string.digits + "-._~")
    assert "reg-name    = *( unreserved / pct-encoded / sub-delims )" in text
    assert 'unreserved  = ALPHA / DIGIT / "-" / "." / "_" / "~"' in text
    assert sub | unreserved | {"%"} == REG_NAME


def test_http_alpn_ids_are_the_http_entries_of_the_iana_registry(upstream: Reader) -> None:
    ids = set()
    for row in csv.DictReader(io.StringIO(upstream("alpn-protocol-ids.csv"))):
        if row["Protocol"].startswith("HTTP/"):
            octets = _group(r"^((?:0x[0-9a-fA-F]{2} ?)+)", row["Identification Sequence"])
            ids.add(bytes(int(part, 16) for part in octets.split()))
    assert ids == HTTP_ALPN_IDS


def test_the_iana_parameter_registry_holds_ma_and_persist(upstream: Reader) -> None:
    values = re.findall(r"<value>([^<]+)</value>", upstream("http-alt-svc-parameters.xml"))
    assert values == ["ma", "persist"]


@pytest.mark.parametrize(
    ("name", "default", "fold"),
    [
        ("quiche-spdy_alt_svc_wire_format.cc", "max_age_seconds = 86400;", "tolower(*c)"),
        ("curl-altsvc.c", "maxage = 24 * 3600;", 'curlx_str_casecompare(&name, "ma")'),
    ],
)
def test_shipping_parsers_default_ma_to_a_day_and_fold_names(
    upstream: Reader, name: str, default: str, fold: str
) -> None:
    source = upstream(name)
    assert default in source
    assert fold in source
    (alternative,) = _alternatives('h3=":443"; MA=5')
    assert (alternative.ma, _alternatives('h3=":443"')[0].max_age) == (5, 86400)
