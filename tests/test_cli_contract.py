"""Subprocess contracts for effective alternatives and bounded usage diagnostics."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def _run(args: list[str], stdin: str = "") -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"))
    return subprocess.run(
        [sys.executable, "-m", "altsvc", *args],
        input=stdin,
        text=True,
        capture_output=True,
        timeout=30,
        env=env,
        check=False,
    )


@pytest.mark.parametrize("field", ['h3=":443", clear', 'clear, h3=":443"'])
@pytest.mark.parametrize("piped", [False, True])
def test_clear_suppresses_effective_alternatives(field: str, piped: bool) -> None:
    result = _run([], f"HTTP/2 200\nAlt-Svc: {field}\n\n") if piped else _run([field])
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["clear"] is True and report["valid"] is False
    assert report["alternatives"] == []
    assert report["issues"][0]["code"] == "clear.mixed"


def test_421_suppresses_effective_alternatives() -> None:
    result = _run([], 'HTTP/1.1 421 Misdirected Request\nAlt-Svc: h3=":443"\n\n')
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["ignored"] is True
    assert "status.421" in [issue["code"] for issue in report["issues"]]
    assert report["alternatives"] == []


@pytest.mark.parametrize("kind", ["option", "positional", "help-value"])
@pytest.mark.parametrize("repeats", [1, 400])
def test_usage_errors_do_not_echo_arguments(kind: str, repeats: int) -> None:
    marker = "SENSITIVE_SENTINEL_7f8c"
    payload = marker * repeats
    args = {
        "option": ["--" + payload],
        "positional": ['h3=":443"', payload],
        "help-value": ["--help=" + payload],
    }[kind]
    result = _run(args)
    assert result.returncode == 2 and result.stdout == ""
    assert marker not in result.stderr
    assert 0 < len(result.stderr) < 300
