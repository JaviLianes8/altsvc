"""Build the wheel, install it in a throwaway venv and drive the installed package.

Slow and needs the build backend, so it runs only with ALTSVC_E2E=1.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tarfile
import venv
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    os.environ.get("ALTSVC_E2E") != "1", reason="set ALTSVC_E2E=1 to build and install"
)

PROGRAM = r"""
import importlib.metadata, importlib.resources
import altsvc
from altsvc import (
    CLEAR, DEFAULT_MAX_AGE, DELTA_SECONDS_MAX, Alternative, AltSvcError, Issue, build,
    decode_protocol_id, encode_protocol_id, expires_at, is_fresh, lint, parse,
)

assert "site-packages" in altsvc.__file__, altsvc.__file__
assert importlib.metadata.version("altsvc") == altsvc.__version__
assert importlib.resources.files("altsvc").joinpath("py.typed").is_file()

(alt,) = parse('w%3Dx%3Ay#z="[::1]:8443"; MA=60; persist=1', strict=True)
assert (alt.alpn, alt.host, alt.port, alt.ma, alt.persist) == (b"w=x:y#z", "::1", 8443, 60, True)
assert parse('h3=":443"')[0].max_age == DEFAULT_MAX_AGE == 86400
assert parse('h3=":443"; ma=' + "9" * 6000)[0].ma == DELTA_SECONDS_MAX == 2**31
assert parse(['h3=":443"', "clear"]) is CLEAR
assert [i.code for i in lint('h3=":0"; persist=2')] == ["authority.port", "persist.ignored"]
assert isinstance(lint("")[0], Issue)
assert encode_protocol_id("x%y") == "x%25y" and decode_protocol_id("x%25y") == b"x%y"
made = Alternative.of("h3", 443, ma=60)
assert build([made]) == 'h3=":443"; ma=60' and parse(build([made]), strict=True) == [made]
assert expires_at(made, 100.0, age=30) == 130.0 and not is_fresh(made, 100.0, 130.0, age=30)
for call in (
    lambda: parse('h3=":443";', strict=True),
    lambda: build([Alternative("h3", ":443", {"x": "a\r\nSet-Cookie: b"})]),
    lambda: Alternative.of("h3", 0),
):
    try:
        call()
    except AltSvcError as error:
        assert isinstance(error, ValueError) and error.code
    else:
        raise AssertionError("expected AltSvcError")
print("e2e ok")
"""


def _run(
    *cmd: str | Path, cwd: Path | None = None, stdin: bytes = b""
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [str(c) for c in cmd], cwd=cwd, input=stdin, capture_output=True, check=False
    )


def _check_artifacts(wheel: Path, sdist: Path) -> None:
    names = zipfile.ZipFile(wheel).namelist()
    assert "altsvc/py.typed" in names and "altsvc/__main__.py" in names
    assert not any(name.startswith(("tests/", "scripts/")) for name in names)
    entry_points = next(name for name in names if name.endswith("entry_points.txt"))
    text = zipfile.ZipFile(wheel).read(entry_points).decode()
    assert "altsvc = altsvc._cli:main" in text
    with tarfile.open(sdist) as archive:
        listing = [name.split("/", 1)[1] for name in archive.getnames() if "/" in name]
    assert not any(name.startswith("IMPROVEMENTS-round") for name in listing)
    assert not any(name.startswith(".github") for name in listing)
    upstream = [name for name in listing if name.startswith("tests/upstream/")]
    assert upstream == ["tests/upstream/MANIFEST.json"], upstream
    assert "tests/test_sources.py" in listing and "scripts/fetch_upstream.py" in listing


def test_installed_wheel_end_to_end(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    built = _run(sys.executable, "-m", "build", "--outdir", dist, ROOT)
    assert built.returncode == 0, built.stderr
    (wheel,) = dist.glob("altsvc-*.whl")
    (sdist,) = dist.glob("altsvc-*.tar.gz")
    _check_artifacts(wheel, sdist)

    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = bindir / "python"
    installed = _run(python, "-m", "pip", "install", "-q", wheel)
    assert installed.returncode == 0, installed.stderr

    # Run from an empty folder so the source tree cannot shadow the install.
    work = tmp_path / "work"
    work.mkdir()
    result = _run(python, "-I", "-c", PROGRAM, cwd=work)
    assert result.returncode == 0, result.stderr
    assert result.stdout.decode().strip() == "e2e ok"

    head = b'HTTP/2 200\r\nalt-svc: h3=":443"; ma=86400, h3-29=":443"\r\n\r\n'
    script = bindir / ("altsvc.exe" if sys.platform == "win32" else "altsvc")
    for command in ([script], [python, "-m", "altsvc"]):
        shown = _run(*command, cwd=work, stdin=head)
        assert shown.returncode == 0, shown.stderr
        report = json.loads(shown.stdout)
        assert report["valid"] is True
        assert [a["alpn"] for a in report["alternatives"]] == ["h3", "h3-29"]
    bad = _run(script, 'h3=":443", clear', cwd=work)
    assert bad.returncode == 1 and json.loads(bad.stdout)["clear"] is True
    usage = _run(script, cwd=work, stdin=b"HTTP/1.1 200 OK\r\n\r\n")
    assert usage.returncode == 2 and b"no Alt-Svc" in usage.stderr
