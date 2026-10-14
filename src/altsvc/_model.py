"""Data model for Alt-Svc alternatives and the clear token."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum

from ._chars import ascii_lower, is_ascii_digits
from ._codec import decode_protocol_id, encode_protocol_id, join_authority, split_authority
from ._errors import AltSvcError

# RFC 7838 section 3.1: without "ma" an alternative is fresh for 24 hours.
DEFAULT_MAX_AGE = 86400

# RFC 9111 section 1.2.2: a delta-seconds value too large to represent is read as 2^31.
DELTA_SECONDS_MAX = 2147483648


class Clear(Enum):
    """The ``clear`` token, which invalidates every previously announced alternative."""

    CLEAR = "clear"


CLEAR = Clear.CLEAR


def read_delta_seconds(text: str) -> int | None:
    """ASCII ``1*DIGIT`` as an int capped at 2^31, or None; long strings are never converted."""
    if not is_ascii_digits(text):
        return None
    digits = text.lstrip("0") or "0"
    if len(digits) > len(str(DELTA_SECONDS_MAX)):
        return DELTA_SECONDS_MAX
    return min(int(digits), DELTA_SECONDS_MAX)


def find_param(params: Mapping[str, str], name: str) -> str | None:
    """The last value of a parameter, names compared with ASCII case folding."""
    found = None
    for key, value in params.items():
        if ascii_lower(key) == name:
            found = value
    return found


@dataclass
class Alternative:
    """One Alt-Svc alternative: a protocol-id, its authority and extra parameters.

    ``protocol`` is the protocol-id as written in the field (percent-encoded), ``authority``
    the content of the quoted alt-authority, ``[host]:port``. The properties read the
    parts; they raise :class:`AltSvcError` when the part they read is not valid.
    """

    protocol: str
    authority: str
    params: dict[str, str] = field(default_factory=dict)

    @classmethod
    def of(
        cls,
        alpn: str | bytes,
        port: int,
        host: str = "",
        *,
        ma: int | None = None,
        persist: bool = False,
        params: Mapping[str, str] | None = None,
    ) -> Alternative:
        """Make an alternative from an ALPN name, a port and an optional host.

        The ALPN name is percent-encoded, an IPv6 host is put in brackets, ``ma`` and
        ``persist`` become parameters, and every part is checked as :func:`build` does.
        """
        if isinstance(port, bool) or not isinstance(port, int):
            raise TypeError("port must be an int")
        extra = dict(params or {})
        if ma is not None:
            if isinstance(ma, bool) or not isinstance(ma, int):
                raise TypeError("ma must be an int number of seconds")
            extra["ma"] = str(ma)
        if not isinstance(persist, bool):
            raise TypeError("persist must be a bool")
        if persist:
            extra["persist"] = "1"
        if not isinstance(host, str):
            raise TypeError("host must be a str")
        if host.startswith("[") and host.endswith("]"):
            host = host[1:-1]
        made = cls(encode_protocol_id(alpn), join_authority(host, port), extra)
        from ._build import build  # the builder imports this module

        build([made])
        return made

    @property
    def alpn(self) -> bytes:
        """The ALPN protocol name, with the percent-encoding of the protocol-id undone."""
        return decode_protocol_id(self.protocol)

    @property
    def host(self) -> str:
        """The alternative host, without IPv6 brackets; empty means the origin's host."""
        return split_authority(self.authority)[0]

    @property
    def port(self) -> int:
        """The alternative port."""
        return split_authority(self.authority)[1]

    @property
    def ma(self) -> int | None:
        """The ``ma`` parameter in seconds, capped at 2^31, or ``None`` when it is absent."""
        value = find_param(self.params, "ma")
        if value is None:
            return None
        seconds = read_delta_seconds(value)
        if seconds is None:
            raise AltSvcError(f"ma must be ASCII digits, got {value!r}", code="ma.invalid")
        return seconds

    @property
    def max_age(self) -> int:
        """The freshness lifetime in seconds: ``ma``, or 86400 when it is absent."""
        ma = self.ma
        return DEFAULT_MAX_AGE if ma is None else ma

    @property
    def persist(self) -> bool:
        """Whether ``persist=1`` asks clients to keep the alternative across network changes."""
        return find_param(self.params, "persist") == "1"
