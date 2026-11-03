"""Seeded independent codec properties and large input contracts."""

from __future__ import annotations

import random
import string
import time
from urllib.parse import quote_from_bytes, unquote_to_bytes

import pytest

from altsvc import Alternative, build, decode_protocol_id, encode_protocol_id, lint, parse
from altsvc._head import field_lines


@pytest.mark.parametrize("seed", [7838, 9110, 20261102])
def test_codec_matches_standard_library_oracle(seed: int) -> None:
    # RFC 7838 section 3 plus the RFC 9110 token alphabet, independently expressed.
    safe = string.ascii_letters + string.digits + "!#$&'*+-.^_`|~"
    rng = random.Random(seed)
    vectors = [bytes([byte]) for byte in range(256)]
    vectors += [rng.randbytes(rng.randrange(1, 200)) for _ in range(2000)]
    for value in vectors:
        encoded = encode_protocol_id(value)
        assert encoded == quote_from_bytes(value, safe=safe)
        assert decode_protocol_id(encoded) == unquote_to_bytes(encoded) == value


@pytest.mark.parametrize("seed", [12, 7838])
def test_last_parameter_agrees_with_independent_wire_order(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(2000):
        pairs = [(rng.choice(["ma", "MA", "Ma"]), rng.randrange(100)) for _ in range(8)]
        header = 'h3=":443"; ' + "; ".join(f"{name}={value}" for name, value in pairs)
        result = parse(header, strict=True)
        assert isinstance(result, list)
        assert result[0].ma == pairs[-1][1]


@pytest.mark.parametrize("shape", ["blank", "fold", "quoted", "parameters", "zeros", "escapes"])
def test_adversarial_shapes_scale_without_quadratic_blowup(shape: str) -> None:
    def run(size: int) -> None:
        if shape == "blank":
            assert field_lines("\n" * size + "Alt-Svc: clear") == ("", ["clear"])
        elif shape == "fold":
            value = field_lines('Alt-Svc: h3=":443"\n' + " ;x=a\n" * size)
            assert value is not None and len(value[1]) == 1
        elif shape == "quoted":
            assert parse('h3=":443";x="' + "a" * size + '"', strict=True)
        elif shape == "parameters":
            assert len(lint('h3=":443"' + ";x=1" * size)) == size - 1
        elif shape == "zeros":
            assert Alternative("h3", ":" + "0" * size + "443").port == 443
        else:
            assert decode_protocol_id("%FF" * size) == b"\xff" * size

    run(100)
    timings = []
    for size in (10000, 40000, 160000):
        start = time.perf_counter()
        run(size)
        timings.append(time.perf_counter() - start)
    # A generous ratio and fixed noise margin tolerate busy machines.
    assert timings[-1] < timings[0] * 35 + 0.25, timings


def test_large_built_value_roundtrips() -> None:
    item = Alternative.of("h3", 65535, ma=2**31, params={"x": 'a"\\' * 100000})
    assert parse(build([item]), strict=True) == [item]
