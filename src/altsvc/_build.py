"""Build an Alt-Svc header value from alternatives or the clear token."""

from __future__ import annotations

from collections.abc import Sequence

from ._model import Alternative, AltSvcError, Clear

_TCHAR = frozenset("!#$%&'*+-.^_`|~0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")


def build(alternatives: Sequence[Alternative] | Clear) -> str:
    """Build an Alt-Svc header value.

    Pass :data:`CLEAR` to emit the ``clear`` token. An empty sequence yields an empty
    string. The authority is always quoted; parameter values are left as bare tokens
    when they are valid tokens and quoted otherwise.
    """
    if isinstance(alternatives, Clear):
        return "clear"
    return ", ".join(_build_alternative(alternative) for alternative in alternatives)


def _build_alternative(alternative: Alternative) -> str:
    if not _is_token(alternative.protocol):
        raise AltSvcError(f"invalid protocol id: {alternative.protocol!r}")
    parts = [f"{alternative.protocol}={_quote(alternative.authority)}"]
    for name, value in alternative.params.items():
        if not _is_token(name):
            raise AltSvcError(f"invalid parameter name: {name!r}")
        parts.append(f"{name}={_format_value(value)}")
    return "; ".join(parts)


def _is_token(value: str) -> bool:
    return bool(value) and all(char in _TCHAR for char in value)


def _quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _format_value(value: str) -> str:
    return value if _is_token(value) else _quote(value)
