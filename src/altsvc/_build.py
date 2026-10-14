"""Build an Alt-Svc field value from alternatives or the clear token."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ._chars import ascii_lower, is_ascii_digits, is_sendable, is_token, quote
from ._codec import is_canonical_protocol_id, split_authority
from ._errors import AltSvcError
from ._model import DELTA_SECONDS_MAX, Alternative, Clear


def build(alternatives: Sequence[Alternative] | Clear) -> str:
    """Build an Alt-Svc field value.

    Pass :data:`CLEAR` to write the ``clear`` token. Every part is checked before it is
    written, so the result always reads back strictly to the same alternatives: a
    canonical protocol-id, an authority with a valid host and a port from 1 to 65535,
    parameter names that are tokens and differ beyond case, values without control
    characters or non-ASCII text, ``ma`` as digits up to 2^31 and ``persist`` only as
    ``1``. The authority is always quoted; parameter values are left as tokens when they
    are tokens and quoted otherwise. Anything else raises :class:`AltSvcError`.
    """
    if isinstance(alternatives, Clear):
        return "clear"
    if isinstance(alternatives, (str, bytes)) or not isinstance(alternatives, Sequence):
        raise TypeError("build takes CLEAR or a sequence of Alternative")
    items = list(alternatives)
    if not items:
        raise AltSvcError("an Alt-Svc value holds at least one alternative", code="empty")
    return ", ".join(_alternative(alternative) for alternative in items)


def _plain(value: object, what: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{what} must be a str, not {type(value).__name__}")
    # A str subclass could render itself as anything; write the characters it holds.
    return str.__str__(value)


def _alternative(alternative: Alternative) -> str:
    if not isinstance(alternative, Alternative):
        raise TypeError(f"expected an Alternative, not {type(alternative).__name__}")
    protocol = _plain(alternative.protocol, "protocol")
    if not is_canonical_protocol_id(protocol):
        raise AltSvcError(
            f"protocol-id {protocol!r} is not canonical; use encode_protocol_id",
            code="protocol-id.canonical",
        )
    authority = _plain(alternative.authority, "authority")
    split_authority(authority)
    if not is_sendable(authority):  # a second guard: nothing but visible ASCII is quoted
        raise AltSvcError(f"authority {authority!r} is not visible ASCII", code="authority.host")
    if not isinstance(alternative.params, Mapping):
        raise TypeError("params must be a mapping of str to str")
    parts = [f"{protocol}={quote(authority)}"]
    seen: set[str] = set()
    for raw_name, raw_value in alternative.params.items():
        name = _plain(raw_name, "a parameter name")
        value = _plain(raw_value, f"parameter {name!r}")
        key = ascii_lower(name)
        if not is_token(name):
            raise AltSvcError(f"invalid parameter name: {name!r}", code="parameter.name")
        if key in seen:
            raise AltSvcError(f"parameter {name!r} is repeated", code="parameter.duplicate")
        seen.add(key)
        _check_value(key, value)
        parts.append(f"{name}={value if is_token(value) else quote(value)}")
    return "; ".join(parts)


def _check_value(key: str, value: str) -> None:
    if not is_sendable(value):
        raise AltSvcError(
            f"parameter value {value!r} holds a control character or non-ASCII text",
            code="parameter.value",
        )
    if key == "ma" and not _in_range(value):
        raise AltSvcError(
            f"ma must be digits from 0 to {DELTA_SECONDS_MAX}, got {value!r}", code="ma.invalid"
        )
    if key == "persist" and value != "1":
        raise AltSvcError("persist has a meaning only as '1'", code="persist.invalid")


def _in_range(value: str) -> bool:
    digits = value.lstrip("0") or "0"
    return is_ascii_digits(value) and len(digits) <= 10 and int(digits) <= DELTA_SECONDS_MAX
