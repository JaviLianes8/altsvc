"""Find the Alt-Svc field lines in a response head such as curl -sI prints."""

from __future__ import annotations

import re

_FIELD = "alt-svc"
_FIELD_LINE = re.compile(r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+:")
_STATUS_LINE = re.compile(r"HTTP/\d(?:\.\d)? \d{3}(?: |$)")


def _responses(lines: list[str]) -> list[list[str]]:
    """Split lines into heads: each starts at a status line and ends at a blank line."""
    heads: list[list[str]] = []
    current: list[str] | None = None
    for line in lines:
        if _STATUS_LINE.match(line):
            current = [line]
            heads.append(current)
        elif not line.strip(" \t"):
            current = None  # the head is over; a body may follow
        elif current is not None:
            current.append(line)
    return heads


def _unfold(lines: list[str]) -> list[str]:
    """Join obsolete folded lines (starting with SP or HTAB) onto the line before."""
    out: list[str] = []
    for line in lines:
        if line[:1] in (" ", "\t") and out:
            out[-1] += " " + line.strip(" \t")
        else:
            out.append(line)
    return out


def field_lines(text: str) -> tuple[str, list[str]] | None:
    """Return the status code and Alt-Svc values of the last response, or None for a value.

    Input counts as a head when its first non-empty line is a status line or a field
    line (``name: value``); the status code is empty when there is no status line. With
    several responses (``curl -sIL`` follows redirects) the last one is used.
    """
    text = text.removeprefix("\ufeff").removeprefix("\xef\xbb\xbf")  # a BOM, decoded or raw
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    while lines and not lines[0].strip(" \t"):
        lines.pop(0)
    if not lines:
        return None
    lines[0] = lines[0].lstrip(" \t")
    status = ""
    if _STATUS_LINE.match(lines[0]):
        status_line, *rest = _responses(lines)[-1]
        status = status_line.split()[1]
    elif _FIELD_LINE.match(lines[0]):
        rest = _responses(["HTTP/1.1 000", *lines])[-1][1:]  # fields without a status line
    else:
        return None
    fields = _unfold(rest)
    values: list[str] = []
    for line in fields:
        name, sep, value = line.partition(":")
        if sep and name.lower() == _FIELD:
            values.append(value.strip(" \t"))
    return status, values
