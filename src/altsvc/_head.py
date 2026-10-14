"""Find the Alt-Svc field lines in a response head such as curl -sI prints."""

from __future__ import annotations

import re

_FIELD = "alt-svc"
_FIELD_LINE = re.compile(r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+:")


def _responses(lines: list[str]) -> list[list[str]]:
    """Split lines into heads: each starts at a status line and ends at a blank line."""
    heads: list[list[str]] = []
    current: list[str] | None = None
    for line in lines:
        if line.startswith("HTTP/"):
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
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    while lines and not lines[0].strip(" \t"):
        lines.pop(0)
    if not lines:
        return None
    if not lines[0].startswith("HTTP/"):
        if not _FIELD_LINE.match(lines[0]):
            return None
        lines.insert(0, "HTTP/")  # pasted fields without a status line
    status_line, *rest = _responses(lines)[-1]
    fields = _unfold(rest)
    parts = status_line.split()
    status = parts[1] if len(parts) > 1 else ""
    values: list[str] = []
    for line in fields:
        name, sep, value = line.partition(":")
        if sep and name.lower() == _FIELD:
            values.append(value.strip(" \t"))
    return status, values
