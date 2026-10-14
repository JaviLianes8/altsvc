from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path

import pytest

UPSTREAM = Path(__file__).resolve().parent / "upstream"


def read_upstream(name: str) -> str:
    """Return a third-party reference file as text.

    The files are not committed: `python scripts/fetch_upstream.py` fetches them. Their
    tests skip while a file is absent and fail if it differs from the manifest.
    """
    path = UPSTREAM / name
    if not path.is_file():
        pytest.skip(f"{name} is not fetched; run python scripts/fetch_upstream.py")
    entry = json.loads((UPSTREAM / "MANIFEST.json").read_text(encoding="utf-8"))[name]
    body = path.read_bytes()
    if hashlib.sha256(body).hexdigest() != entry["sha256"]:
        if entry.get("living"):
            pytest.skip(f"{name} changed upstream; review it and update MANIFEST.json")
        raise AssertionError(f"{name} differs from MANIFEST")
    return body.decode("utf-8")


@pytest.fixture(scope="session")
def upstream() -> Callable[[str], str]:
    """A reader for the files listed in tests/upstream/MANIFEST.json."""
    return read_upstream
