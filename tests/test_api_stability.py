"""Names, signatures, defaults and metadata promised by the stable API."""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

import altsvc


@pytest.mark.parametrize(
    ("name", "parameters"),
    [
        ("parse", [("value", False, None), ("strict", True, False)]),
        ("lint", [("value", False, None)]),
        ("build", [("alternatives", False, None)]),
        ("encode_protocol_id", [("name", False, None)]),
        ("decode_protocol_id", [("protocol_id", False, None)]),
        (
            "expires_at",
            [("alternative", False, None), ("received_at", False, None), ("age", True, 0)],
        ),
        (
            "is_fresh",
            [
                ("alternative", False, None),
                ("received_at", False, None),
                ("now", False, None),
                ("age", True, 0),
            ],
        ),
    ],
)
def test_function_signatures_remain_stable(
    name: str, parameters: list[tuple[str, bool, object]]
) -> None:
    signature = inspect.signature(getattr(altsvc, name))
    expected = []
    for param_name, keyword_only, default in parameters:
        kind = (
            inspect.Parameter.KEYWORD_ONLY
            if keyword_only
            else inspect.Parameter.POSITIONAL_OR_KEYWORD
        )
        expected.append((param_name, kind, inspect.Parameter.empty if default is None else default))
    assert [(p.name, p.kind, p.default) for p in signature.parameters.values()] == expected
    assert signature.return_annotation is not inspect.Parameter.empty


def test_factory_signature_defaults_remain_stable() -> None:
    signature = inspect.signature(altsvc.Alternative.of)
    assert list(signature.parameters) == ["alpn", "port", "host", "ma", "persist", "params"]
    assert [p.default for p in list(signature.parameters.values())[2:]] == ["", None, False, None]
    assert all(p.kind == p.KEYWORD_ONLY for p in list(signature.parameters.values())[3:])


def test_error_fields_and_clear_identity() -> None:
    error = altsvc.AltSvcError("invalid value", code="example", offset=4)
    assert isinstance(error, ValueError)
    assert (error.message, error.code, error.offset) == ("invalid value", "example", 4)
    assert str(error) == "invalid value (at offset 4)"
    plain = altsvc.AltSvcError("invalid value")
    assert (plain.code, plain.offset, str(plain)) == ("invalid", None, "invalid value")
    assert altsvc.Clear("clear") is altsvc.CLEAR
    assert altsvc.build(altsvc.Clear.CLEAR) == "clear"
    with pytest.raises(ValueError):
        altsvc.Clear("CLEAR")


def test_project_metadata_matches_stable_contract() -> None:
    root = Path(__file__).resolve().parents[1]
    metadata = root.joinpath("pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "1.0.0"' in metadata
    assert 'requires-python = ">=3.10"' in metadata
    assert "Development Status :: 5 - Production/Stable" in metadata
    assert 'license = "MIT"' in metadata and "dependencies = []" in metadata
    for name in ("Homepage", "Source", "Issues", "Changelog"):
        assert re.search(rf'^{name} = "https://', metadata, re.MULTILINE)
    readme = root.joinpath("README.md").read_text(encoding="utf-8")
    links = re.findall(r"\]\(([^)]+)\)", readme)
    assert links and all(link.startswith("https://") for link in links)
    assert "https://lianes8studio.com/certified/lianes8-certified-badge.svg" in readme
