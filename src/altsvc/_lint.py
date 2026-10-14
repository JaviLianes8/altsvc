"""Check what the scanner read against RFC 7838 and turn it into alternatives and findings."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from ._chars import ascii_lower
from ._codec import HTTP_ALPN_IDS, decode_protocol_id, is_canonical_protocol_id, split_authority
from ._errors import AltSvcError, Issue
from ._model import DELTA_SECONDS_MAX, Alternative, read_delta_seconds
from ._scan import Entry, scan


@dataclass
class Analysis:
    """Everything read from a field value: usable alternatives, ``clear`` and findings."""

    alternatives: list[Alternative] = field(default_factory=list)
    clear: bool = False
    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.severity == "error"]


def field_value(value: str | Sequence[str]) -> str:
    """One field value; several field lines are combined as one list (RFC 9110 5.3)."""
    if isinstance(value, str):
        return value
    if isinstance(value, (bytes, bytearray)):
        raise TypeError("decode the field value to str first (latin-1 keeps every octet)")
    if not isinstance(value, Sequence):
        raise TypeError("a field value is a str or a sequence of str")
    lines = list(value)
    if not all(isinstance(line, str) for line in lines):
        raise TypeError("a field value is a str or a sequence of str")
    return ", ".join(lines)


def _protocol(entry: Entry, issues: list[Issue]) -> None:
    try:
        name = decode_protocol_id(entry.protocol)
    except AltSvcError as error:
        offset = entry.offset + (error.offset or 0)
        issues.append(Issue(error.code, error.message, "error", offset))
        entry.usable = False
        return
    if not is_canonical_protocol_id(entry.protocol):
        message = f"{entry.protocol!r} is not the canonical protocol-id (upper-case %XX only)"
        issues.append(Issue("protocol-id.canonical", message, "error", entry.offset))
        entry.usable = False
    elif name not in HTTP_ALPN_IDS:
        message = f"{entry.protocol!r} is not a registered HTTP ALPN id (IANA ALPN registry)"
        issues.append(Issue("protocol.not-http", message, "warning", entry.offset))


def _authority(entry: Entry, issues: list[Issue]) -> None:
    try:
        split_authority(entry.authority)
    except AltSvcError as error:
        issues.append(Issue(error.code, error.message, "error", entry.authority_offset))
        entry.usable = False


def _params(entry: Entry, issues: list[Issue]) -> dict[str, str]:
    params: dict[str, str] = {}
    seen: set[str] = set()
    last_ma_ok = True  # the last ma wins, so only it decides whether the entry is usable
    for name, value, offset in entry.params:
        key = ascii_lower(name)
        if key in seen:
            message = f"parameter {name!r} repeats; the last value is used"
            issues.append(Issue("parameter.duplicate", message, "warning", offset))
        seen.add(key)
        if key == "ma":
            seconds = read_delta_seconds(value)
            last_ma_ok = seconds is not None
            if seconds is None:
                message = f"ma must be ASCII digits (delta-seconds), got {value!r}"
                issues.append(Issue("ma.invalid", message, "error", offset))
            elif seconds == DELTA_SECONDS_MAX and value.lstrip("0") != str(DELTA_SECONDS_MAX):
                message = f"ma is above {DELTA_SECONDS_MAX} and is read as that"
                issues.append(Issue("ma.capped", message, "warning", offset))
        elif key == "persist" and value != "1":
            message = f"persist={value!r} is ignored; only persist=1 has a meaning"
            issues.append(Issue("persist.ignored", message, "warning", offset))
        params[name] = value
    if not last_ma_ok:
        entry.usable = False
    return params


def analyse(value: str | Sequence[str]) -> Analysis:
    """Read a field value (or several field lines) and report every finding."""
    text = field_value(value)
    result = scan(text)
    analysis = Analysis(clear=bool(result.clears), issues=list(result.issues))
    for entry in result.entries:
        _protocol(entry, analysis.issues)
        _authority(entry, analysis.issues)
        params = _params(entry, analysis.issues)
        if entry.usable:
            analysis.alternatives.append(Alternative(entry.protocol, entry.authority, params))
    elements = len(result.entries) + len(result.clears)
    if result.clears and elements > 1:
        offset = sorted(result.clears + [entry.offset for entry in result.entries])[1]
        message = "'clear' must be the whole value; it still invalidates every alternative"
        analysis.issues.append(Issue("clear.mixed", message, "error", offset))
    elif result.clears and text.strip(" \t") != "clear":
        message = "'clear' is the whole value, not a list member"
        analysis.issues.append(Issue("clear.list", message, "error", result.clears[0]))
    if elements == 0 and not result.issues:
        analysis.issues.append(Issue("empty", "the value holds no alternative", "error", 0))
    analysis.issues.sort(key=lambda issue: issue.offset or 0)
    return analysis


def lint(value: str | Sequence[str]) -> list[Issue]:
    """Every finding about an Alt-Svc field value, in the order they occur."""
    return analyse(value).issues
