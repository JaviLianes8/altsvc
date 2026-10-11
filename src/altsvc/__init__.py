"""Parse and build the HTTP Alt-Svc header (RFC 7838), a typed zero-dep codec."""

from __future__ import annotations

from ._build import build
from ._model import CLEAR, Alternative, AltSvcError, Clear
from ._parse import parse

__version__ = "0.1.0"

__all__ = [
    "CLEAR",
    "AltSvcError",
    "Alternative",
    "Clear",
    "build",
    "parse",
]
