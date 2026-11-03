"""Contracts for the stable surface and corrected boundary behavior."""

from __future__ import annotations

import doctest
import importlib
import inspect
import re
from collections.abc import Callable
from pathlib import Path

import pytest

import altsvc
from altsvc import Alternative, AltSvcError, build, encode_protocol_id, expires_at, is_fresh


def test_public_docstrings_are_executable() -> None:
    for name in altsvc.__all__:
        value = getattr(altsvc, name)
        if inspect.isclass(value) or inspect.isfunction(value):
            assert ">>>" in (value.__doc__ or ""), name
    for name in ("of", "alpn", "host", "port", "ma", "max_age", "persist"):
        assert ">>>" in (getattr(Alternative, name).__doc__ or "")
    for path in Path(altsvc.__file__).parent.glob("*.py"):
        if path.stem == "__main__":
            continue
        module = importlib.import_module(
            "altsvc" if path.stem == "__init__" else f"altsvc.{path.stem}"
        )
        assert doctest.testmod(module).failed == 0


def test_guide_examples_execute() -> None:
    text = Path(__file__).resolve().parents[1].joinpath("GUIDE.md").read_text(encoding="utf-8")
    for block in re.findall(r"```python\n(.*?)```", text, re.DOTALL):
        exec(compile(block, "GUIDE.md", "exec"), {})


def test_exact_spelling_reinserted_after_other_case_variants() -> None:
    for name in ("ma", "x"):
        result = altsvc.parse(f'h3=":443"; {name}=1; {name.upper()}=2; {name}=3')
        assert isinstance(result, list)
        assert list(result[0].params.items()) == [(name.upper(), "2"), (name, "3")]
        assert result[0].ma == (3 if name == "ma" else None)
        assert result[0].persist is False


@pytest.mark.parametrize("host", ["", "[::1]", "example.org"])
def test_long_zero_prefixed_port_is_safe(host: str) -> None:
    result = altsvc.parse(f'h3="{host}:' + "0" * 10000 + '443"', strict=True)
    assert isinstance(result, list)
    assert result[0].port == 443


@pytest.mark.parametrize("field", ["port", "ma"])
def test_huge_factory_integers_have_typed_errors(field: str) -> None:
    with pytest.raises(AltSvcError) as caught:
        if field == "port":
            Alternative.of("h3", 10**10000)
        else:
            Alternative.of("h3", 443, ma=10**10000)
    assert caught.value.code == ("authority.port" if field == "port" else "ma.invalid")


def test_factory_refuses_even_empty_non_mapping_params() -> None:
    with pytest.raises(TypeError, match="mapping"):
        Alternative.of("h3", 443, params=[])  # type: ignore[arg-type]


def test_surrogate_encoding_has_a_typed_error() -> None:
    with pytest.raises(AltSvcError) as caught:
        encode_protocol_id("\ud800")
    assert caught.value.code == "protocol-id.unicode"


@pytest.mark.parametrize(
    "time",
    [float("nan"), float("inf"), -float("inf"), 10**10000],
    ids=["nan", "inf", "-inf", "huge"],
)
def test_nonfinite_times_are_refused(time: float) -> None:
    alt = Alternative.of("h3", 443)
    for call in (lambda: expires_at(alt, time), lambda: is_fresh(alt, 0, time)):
        with pytest.raises(AltSvcError) as caught:
            call()
        assert caught.value.code == "time.invalid"


@pytest.mark.parametrize("value", [True, None, "1", object()])
def test_now_requires_a_number(value: object) -> None:
    with pytest.raises(TypeError):
        is_fresh(Alternative.of("h3", 443), 0, value)  # type: ignore[arg-type]


def test_expiry_validates_alternative_and_returns_float() -> None:
    with pytest.raises(TypeError):
        expires_at(None, 0)  # type: ignore[arg-type]
    assert type(expires_at(Alternative.of("h3", 443), 0)) is float


def test_generated_diagnostics_do_not_echo_inputs() -> None:
    secret = "private-key-" + "x" * 100000
    calls: list[Callable[[], object]] = [
        lambda: build([Alternative(secret + " ", ":443")]),
        lambda: build([Alternative("h3", secret + ":0")]),
        lambda: build([Alternative("h3", ":443", {secret: "\r"})]),
        lambda: build([Alternative("h3", ":443", {"ma": secret})]),
        lambda: altsvc.decode_protocol_id(secret + "%"),
        lambda: altsvc.decode_protocol_id(secret + " "),
        lambda: Alternative("h3", ":443", {"ma": secret}).ma,
    ]
    for call in calls:
        with pytest.raises(AltSvcError) as caught:
            call()
        assert "private-key" not in str(caught.value)
        assert len(str(caught.value)) < 200
    for value in (f'{secret}=":443"', f'h3=":443"; ma={secret}', f'h3="{secret}:0"'):
        for issue in altsvc.lint(value):
            assert "private-key" not in issue.message
            assert len(issue.message) < 200


def test_model_defaults_and_findings_are_independent() -> None:
    first = Alternative("h3", ":443")
    second = Alternative("h3", ":443")
    first.params["ma"] = "1"
    assert second.params == {}
    params = {"x": "a"}
    made = Alternative.of("h3", 443, params=params)
    params["x"] = "b"
    assert made.params == {"x": "a"}
    with pytest.raises(AttributeError):
        altsvc.Issue("x", "message", "error").message = "changed"  # type: ignore[misc]
