"""The command line reads a value or a response head and prints JSON."""

from __future__ import annotations

import io
import json
import sys
from typing import Any

import pytest

from altsvc._cli import main
from altsvc._head import field_lines


class _Stdin:
    def __init__(self, data: bytes, tty: bool = False) -> None:
        self.buffer = io.BytesIO(data)
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


def _run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    stdin: bytes = b"",
    tty: bool = False,
) -> tuple[int, dict[str, Any], str]:
    monkeypatch.setattr(sys, "stdin", _Stdin(stdin, tty))
    code = main(argv)
    captured = capsys.readouterr()
    report = json.loads(captured.out) if captured.out else {}
    return code, report, captured.err


def test_a_valid_value_prints_its_alternatives(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, report, _ = _run(monkeypatch, capsys, ['w%3Dx="[::1]:8443"; ma=60; persist=1'])
    assert code == 0
    assert report["valid"] is True and report["clear"] is False
    assert report["alternatives"] == [
        {
            "protocol": "w%3Dx",
            "alpn": "w=x",
            "host": "::1",
            "port": 8443,
            "max_age": 60,
            "persist": True,
            "params": {"ma": "60", "persist": "1"},
        }
    ]
    assert [issue["code"] for issue in report["issues"]] == ["protocol.not-http"]


def test_errors_exit_one_and_list_findings(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, report, _ = _run(monkeypatch, capsys, ['h3=":443", clear'])
    assert code == 1
    assert report["valid"] is False and report["clear"] is True
    assert report["issues"] == [
        {
            "code": "clear.mixed",
            "severity": "error",
            "offset": 11,
            "message": "'clear' must be the whole value; it still invalidates every alternative",
        }
    ]


def test_an_empty_argument_is_a_value_to_check(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, report, _ = _run(monkeypatch, capsys, [""])
    assert code == 1 and report["issues"][0]["code"] == "empty"


def test_a_head_on_stdin_combines_every_field_line_of_the_last_response(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    head = (
        b"HTTP/1.1 301 Moved\r\nAlt-Svc: clear\r\n\r\n"
        b'HTTP/2 200\r\nalt-svc: h3=":443";\r\n  ma=60\r\nALT-SVC: h2=":443"\r\n\r\nbody'
    )
    code, report, _ = _run(monkeypatch, capsys, [], head)
    assert code == 0
    assert report["field"] == 'h3=":443"; ma=60, h2=":443"'
    assert [a["max_age"] for a in report["alternatives"]] == [60, 86400]


def test_a_421_response_is_ignored(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    head = b'HTTP/1.1 421 Misdirected Request\nAlt-Svc: clear, h3=":443"\n\n'
    code, report, _ = _run(monkeypatch, capsys, [], head)
    assert code == 1
    assert report["ignored"] is True and report["clear"] is False
    assert report["alternatives"] == []
    assert [issue["code"] for issue in report["issues"]] == ["clear.mixed", "status.421"]
    head = b'HTTP/1.1 421 Misdirected Request\nAlt-Svc: h3=":443"\n\n'
    code, report, _ = _run(monkeypatch, capsys, [], head)
    assert code == 1 and report["valid"] is True and report["ignored"] is True
    head = b'HTTP/2 200\nAlt-Svc: h3=":443"\n\n'
    code, report, _ = _run(monkeypatch, capsys, [], head)
    assert code == 0 and report["ignored"] is False


def test_pasted_fields_without_a_status_line_and_a_bare_value_on_stdin(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, report, _ = _run(monkeypatch, capsys, [], b'\n\nAlt-Svc: h3=":443"\n')
    assert code == 0 and report["field"] == 'h3=":443"'
    code, report, _ = _run(monkeypatch, capsys, [], b'  h2=":443"\r\n')
    assert code == 0 and report["field"] == 'h2=":443"'


@pytest.mark.parametrize("stdin", [b"", b"HTTP/1.1 200 OK\r\nServer: x\r\n\r\n", b"\r\n \n"])
def test_input_without_the_field_is_a_usage_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], stdin: bytes
) -> None:
    code, report, err = _run(monkeypatch, capsys, [], stdin)
    assert code == 2 and report == {}
    assert "no Alt-Svc field" in err


def test_a_terminal_with_nothing_piped_is_a_usage_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as caught:
        _run(monkeypatch, capsys, [], tty=True)
    assert caught.value.code == 2


def test_field_lines_unfolds_and_ignores_continuations_of_other_fields() -> None:
    text = 'HTTP/1.1 200 OK\nX-Note: a\n Alt-Svc: h2=":1"\nAlt-Svc: h3=":443"\n'
    assert field_lines(text) == ("200", ['h3=":443"'])
    assert field_lines('h3=":443"') is None
    assert field_lines("Alt-Svc: clear") == ("", ["clear"])
    assert field_lines("") is None
