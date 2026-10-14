"""Walk an Alt-Svc field value along the RFC 7838 grammar, recording offsets and syntax errors."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._chars import OWS, TCHAR, is_pair_char, is_qdtext
from ._errors import Issue


@dataclass
class Entry:
    """One alternative as written: parts, their offsets and whether it can be used."""

    offset: int
    protocol: str
    authority: str
    authority_offset: int
    params: list[tuple[str, str, int]] = field(default_factory=list)
    usable: bool = True


@dataclass
class Scan:
    entries: list[Entry] = field(default_factory=list)
    clears: list[int] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)


class _Syntax(Exception):
    def __init__(self, code: str, message: str, offset: int) -> None:
        super().__init__(message)
        self.issue = Issue(code, message, "error", offset)


def _ows(text: str, index: int) -> int:
    while index < len(text) and text[index] in OWS:
        index += 1
    return index


def _token_end(text: str, index: int) -> int:
    while index < len(text) and text[index] in TCHAR:
        index += 1
    return index


def _skip_to(text: str, index: int, stops: str) -> int:
    """The index of the next stop character outside a quoted string, or the end."""
    quoted = False
    while index < len(text):
        char = text[index]
        if quoted and char == "\\":
            index += 1
        elif char == '"':
            quoted = not quoted
        elif not quoted and char in stops:
            return index
        index += 1
    return index


def _quoted(text: str, index: int) -> tuple[str, int]:
    """Read the quoted-string at ``index``; return its content and the index after it."""
    out: list[str] = []
    position = index + 1
    while position < len(text):
        char = text[position]
        if char == '"':
            return "".join(out), position + 1
        if char == "\\" and position + 1 < len(text) and is_pair_char(text[position + 1]):
            out.append(text[position + 1])
            position += 2
        elif is_qdtext(char):  # the backslash is not qdtext
            out.append(char)
            position += 1
        else:
            raise _Syntax("syntax.quoted-string", f"{char!r} is not allowed here", position)
    raise _Syntax("syntax.quoted-string", "the quoted string is not closed", index)


def _equals(text: str, index: int, what: str) -> int:
    if index < len(text) and text[index] == "=":
        return index + 1
    after = _ows(text, index)
    if after > index and after < len(text) and text[after] == "=":
        raise _Syntax("syntax.space", f"no whitespace is allowed before '=' in {what}", index)
    raise _Syntax("syntax.equals", f"'=' expected after the {what} name", index)


def _parameter(text: str, index: int) -> tuple[str, str, int]:
    end = _token_end(text, index)
    if end == index:
        raise _Syntax("syntax.token", "a parameter name (a token) is expected", index)
    value_at = _equals(text, end, "parameter")
    if value_at < len(text) and text[value_at] == '"':
        value, after = _quoted(text, value_at)
        return text[index:end], value, after
    after = _token_end(text, value_at)
    if after == value_at:
        raise _Syntax("syntax.value", "a token or a quoted string is expected", value_at)
    return text[index:end], text[value_at:after], after


def _parameters(text: str, index: int, entry: Entry, scan: Scan) -> int:
    while True:
        semicolon = _ows(text, index)
        if semicolon >= len(text) or text[semicolon] != ";":
            return index
        start = _ows(text, semicolon + 1)
        if start >= len(text) or text[start] in ",;":
            message = "an empty parameter after ';'"
            scan.issues.append(Issue("syntax.empty-parameter", message, "error", semicolon))
            index = start
            continue
        try:
            name, value, index = _parameter(text, start)
        except _Syntax as error:
            scan.issues.append(error.issue)
            if text[start : _token_end(text, start)].lower() == "ma":
                entry.usable = False  # the lifetime the server meant is unknown
            index = _skip_to(text, start, ",;")
            continue
        entry.params.append((name, value, start))


def _element(text: str, index: int, scan: Scan) -> Entry | None:
    end = _token_end(text, index)
    if end == index:
        raise _Syntax("syntax.token", "a protocol-id (a token) is expected", index)
    after = _ows(text, end)
    if text[index:end] == "clear" and (after == len(text) or text[after] == ","):
        scan.clears.append(index)
        return None
    authority_at = _equals(text, end, "alternative")
    if authority_at >= len(text) or text[authority_at] != '"':
        raise _Syntax("syntax.authority", "the alt-authority must be a quoted string", authority_at)
    authority, after = _quoted(text, authority_at)
    entry = Entry(index, text[index:end], authority, authority_at)
    scan.entries.append(entry)
    entry_end = _parameters(text, after, entry, scan)
    next_at = _ows(text, entry_end)
    if next_at < len(text) and text[next_at] != ",":
        entry.usable = False
        raise _Syntax("syntax.comma", "',' or ';' expected after the alternative", next_at)
    return entry


def scan(text: str) -> Scan:
    """Read ``#alt-value`` or ``clear``, with RFC 9110 list rules (empty elements allowed)."""
    result = Scan()
    index = 0
    while True:
        index = _ows(text, index)
        if index >= len(text):
            break
        if text[index] == ",":
            index += 1
            continue
        try:
            _element(text, index, result)
        except _Syntax as error:
            result.issues.append(error.issue)
            offset = error.issue.offset
            # Resume from the failure, or from the element start when a quote may be open.
            start = offset if error.issue.code == "syntax.comma" and offset is not None else index
            index = _skip_to(text, start, ",")
            continue
        index = _skip_to(text, index, ",")
    return result
