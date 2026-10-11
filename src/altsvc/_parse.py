"""Parse an Alt-Svc header value into alternatives or the clear token."""

from __future__ import annotations

from ._model import CLEAR, Alternative, Clear


def parse(header: str) -> list[Alternative] | Clear:
    """Parse an Alt-Svc header value.

    Returns :data:`CLEAR` for the ``clear`` token, otherwise the list of alternatives
    that could be read. Alternatives that are malformed are skipped, as RFC 7838 asks
    recipients to do, so a single bad entry never discards the valid ones.
    """
    text = header.strip()
    if text == "clear":
        return CLEAR
    result: list[Alternative] = []
    for segment in _split(text, ","):
        alternative = _parse_alternative(segment)
        if alternative is not None:
            result.append(alternative)
    return result


def _parse_alternative(segment: str) -> Alternative | None:
    pieces = [piece.strip() for piece in _split(segment, ";")]
    pieces = [piece for piece in pieces if piece]
    if not pieces:
        return None
    name, sep, raw = pieces[0].partition("=")
    protocol = name.strip()
    authority = _unquote(raw.strip())
    if not sep or not protocol or authority is None:
        return None
    params: dict[str, str] = {}
    for piece in pieces[1:]:
        key, eq, value = piece.partition("=")
        key = key.strip()
        if key:
            params[key] = _value(value.strip()) if eq else ""
    return Alternative(protocol, authority, params)


def _split(text: str, separator: str) -> list[str]:
    """Split on a separator that sits outside a quoted-string."""
    parts: list[str] = []
    current: list[str] = []
    quoted = False
    escaped = False
    for char in text:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\" and quoted:
            current.append(char)
            escaped = True
        elif char == '"':
            quoted = not quoted
            current.append(char)
        elif char == separator and not quoted:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return parts


def _unquote(value: str) -> str | None:
    """Return the content of a quoted-string, or ``None`` when ``value`` is not quoted."""
    if len(value) < 2 or value[0] != '"' or value[-1] != '"':
        return None
    inner = value[1:-1]
    out: list[str] = []
    index = 0
    while index < len(inner):
        char = inner[index]
        if char == "\\" and index + 1 < len(inner):
            out.append(inner[index + 1])
            index += 2
        else:
            out.append(char)
            index += 1
    return "".join(out)


def _value(raw: str) -> str:
    unquoted = _unquote(raw)
    return unquoted if unquoted is not None else raw
