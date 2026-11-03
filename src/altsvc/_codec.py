"""Protocol-id percent-encoding (RFC 7838 section 3) and alt-authority parts (RFC 3986)."""

from __future__ import annotations

import ipaddress

from ._chars import DIGITS, HEXDIG, REG_NAME, TCHAR
from ._errors import AltSvcError

# RFC 7838 section 3: "%" itself is not left bare, so it is the one tchar that is encoded.
_BARE = frozenset(ord(char) for char in TCHAR if char != "%")

# The HTTP entries of the IANA ALPN Protocol IDs registry.
HTTP_ALPN_IDS = frozenset({b"http/0.9", b"http/1.0", b"http/1.1", b"h2", b"h2c", b"h3"})

MAX_PORT = 65535

_IPV6 = HEXDIG | {":", "."}


def encode_protocol_id(name: str | bytes) -> str:
    """Return the canonical protocol-id for an ALPN protocol name.

    Octets that are token characters stay as they are, every other octet and ``%`` are
    written as ``%XX`` with upper-case hex digits. A ``str`` is taken as UTF-8.

    >>> from altsvc import encode_protocol_id
    >>> encode_protocol_id('x%y')
    'x%25y'
    """
    if isinstance(name, str):
        try:
            name = name.encode("utf-8")
        except UnicodeEncodeError:
            raise AltSvcError("ALPN text must be valid UTF-8", code="protocol-id.unicode") from None
    elif not isinstance(name, bytes):
        raise TypeError("an ALPN name is str or bytes")
    if not name:
        raise AltSvcError("an ALPN protocol name is never empty", code="protocol-id.empty")
    return "".join(chr(octet) if octet in _BARE else f"%{octet:02X}" for octet in name)


def decode_protocol_id(protocol_id: str) -> bytes:
    """Return the ALPN protocol name, as octets, that a protocol-id stands for.

    Lower-case hex digits are decoded too; encoding the result gives the canonical
    form RFC 7838 allows a sender to write. Malformed input raises ``AltSvcError``.

    >>> from altsvc import decode_protocol_id
    >>> decode_protocol_id('x%25y')
    b'x%y'
    """
    if not isinstance(protocol_id, str):
        raise TypeError("a protocol-id is str")
    if not protocol_id or any(char not in TCHAR for char in protocol_id):
        raise AltSvcError("protocol-id is not a token", code="protocol-id.token")
    out = bytearray()
    index = 0
    while index < len(protocol_id):
        char = protocol_id[index]
        if char != "%":
            out.append(ord(char))
            index += 1
            continue
        pair = protocol_id[index + 1 : index + 3]
        if len(pair) != 2 or not set(pair) <= HEXDIG:
            raise AltSvcError(
                "'%' must start a %XX escape",
                code="protocol-id.percent",
                offset=index,
            )
        out.append(int(pair, 16))
        index += 3
    return bytes(out)


def is_canonical_protocol_id(protocol_id: str) -> bool:
    """True when the protocol-id decodes and is written exactly as RFC 7838 requires."""
    try:
        name = decode_protocol_id(protocol_id)
    except AltSvcError:
        return False
    return encode_protocol_id(name) == protocol_id


def split_authority(authority: str) -> tuple[str, int]:
    """Split an alt-authority into its host (empty for the origin's host) and port.

    The host is an RFC 3986 reg-name or IPv4 address in ASCII (section 8 of RFC 7838 asks
    for A-labels), or an IPv6 literal in brackets, returned without them. The port is 1 to
    65535. Library policy beyond RFC 3986: an empty port and port 0 cannot be connected
    to, and IPvFuture literals and zone IDs are refused.
    """
    if not isinstance(authority, str):
        raise TypeError("authority must be a str")
    host, colon, port = authority.rpartition(":")
    if not colon:
        raise AltSvcError("no ':port' in alt-authority", code="authority.port")
    # Leading zeros are allowed (port = *DIGIT); long digit strings are never converted.
    digits = port.lstrip("0")
    if not (set(port) <= DIGITS and 0 < len(digits) <= 5 and int(digits) <= MAX_PORT):
        raise AltSvcError(
            f"port must be 1 to {MAX_PORT}",
            code="authority.port",
            offset=len(host),
        )
    if host.startswith("[") and host.endswith("]"):
        # RFC 3986 IP-literals carry no zone ID, and ipaddress would take any text after "%".
        try:
            if not set(host[1:-1]) <= _IPV6:
                raise ValueError
            ipaddress.IPv6Address(host[1:-1])
        except ValueError:
            raise AltSvcError("bad IPv6 literal", code="authority.host") from None
        return host[1:-1], int(digits)
    if not host.isascii():
        raise AltSvcError("host must be written in A-labels (ASCII)", code="authority.host")
    if not set(host) <= REG_NAME or not _percent_ok(host):
        raise AltSvcError("host is not a valid reg-name", code="authority.host")
    return host, int(digits)


def join_authority(host: str, port: int) -> str:
    """Write an alt-authority, bracketing an IPv6 address."""
    return f"[{host}]:{port}" if ":" in host else f"{host}:{port}"


def _percent_ok(text: str) -> bool:
    parts = text.split("%")
    return all(len(part) >= 2 and set(part[:2]) <= HEXDIG for part in parts[1:])
