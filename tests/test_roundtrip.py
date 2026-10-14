"""Seeded random checks: built values read back strictly, and no input crashes the reader."""

from __future__ import annotations

import random
import string

from altsvc import Alternative, AltSvcError, build, lint, parse

_PIECES = ['h3=":443"', "clear", ",", ";", "=", '"', "\\", " ", "\t", "ma", "persist", "1", "%"]
_ALPHABET = string.printable + "\u00e9\u00ff\u0100\x00\x7f"


def _random_alternative(rng: random.Random) -> Alternative:
    alpn = bytes(rng.randrange(256) for _ in range(rng.randint(1, 6)))
    host = rng.choice(["", "alt.example", "192.0.2.7", "2001:db8::5", "xn--bcher-kva.example"])
    params: dict[str, str] = {}
    for _ in range(rng.randint(0, 3)):
        name = "".join(rng.choice(string.ascii_lowercase + "-_") for _ in range(rng.randint(1, 5)))
        if name not in ("ma", "persist"):
            value = "".join(rng.choice(string.printable[:95]) for _ in range(rng.randint(0, 6)))
            params[name] = value
    made = Alternative.of(
        alpn,
        rng.randint(1, 65535),
        host,
        ma=rng.choice([None, 0, 60, 2**31]),
        persist=rng.random() < 0.5,
        params=params,
    )
    return made


def test_every_built_value_reads_back_strictly() -> None:
    rng = random.Random(7838)
    for _ in range(2000):
        alternatives = [_random_alternative(rng) for _ in range(rng.randint(1, 3))]
        header = build(alternatives)
        assert parse(header, strict=True) == alternatives, header
        assert [issue.severity for issue in lint(header)].count("error") == 0


def test_random_input_raises_nothing_but_alt_svc_error() -> None:
    rng = random.Random(9114)
    for _ in range(3000):
        if rng.random() < 0.5:
            text = "".join(rng.choice(_PIECES) for _ in range(rng.randint(0, 12)))
        else:
            text = "".join(rng.choice(_ALPHABET) for _ in range(rng.randint(0, 30)))
        tolerant = parse(text)
        lint(text)
        try:
            strict = parse(text, strict=True)
        except AltSvcError as error:
            assert error.code
            continue
        assert strict == tolerant, text
