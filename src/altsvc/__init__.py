"""Parse, check and build the HTTP Alt-Svc header (RFC 7838).

>>> from altsvc import CLEAR, DEFAULT_MAX_AGE, DELTA_SECONDS_MAX, build
>>> build(CLEAR), DEFAULT_MAX_AGE, DELTA_SECONDS_MAX
('clear', 86400, 2147483648)
"""

from __future__ import annotations

from ._build import build
from ._cache import expires_at, is_fresh
from ._codec import decode_protocol_id, encode_protocol_id
from ._errors import AltSvcError, Issue
from ._lint import lint
from ._model import CLEAR, DEFAULT_MAX_AGE, Alternative, Clear
from ._params import DELTA_SECONDS_MAX
from ._parse import parse

__version__ = "1.0.0"

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
