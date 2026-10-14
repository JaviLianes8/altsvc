"""Parse, check and build the HTTP Alt-Svc header (RFC 7838), typed and zero-dependency."""

from __future__ import annotations

from ._build import build
from ._cache import expires_at, is_fresh
from ._codec import decode_protocol_id, encode_protocol_id
from ._errors import AltSvcError, Issue
from ._lint import lint
from ._model import CLEAR, DEFAULT_MAX_AGE, DELTA_SECONDS_MAX, Alternative, Clear
from ._parse import parse

__version__ = "0.2.0"

__all__ = [
    "CLEAR",
    "DEFAULT_MAX_AGE",
    "DELTA_SECONDS_MAX",
    "AltSvcError",
    "Alternative",
    "Clear",
    "Issue",
    "build",
    "decode_protocol_id",
    "encode_protocol_id",
    "expires_at",
    "is_fresh",
    "lint",
    "parse",
]
