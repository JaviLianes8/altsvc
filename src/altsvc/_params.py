"""Read parameter values without unbounded integer conversions."""

from __future__ import annotations

from collections.abc import Mapping

from ._chars import ascii_lower, is_ascii_digits

DELTA_SECONDS_MAX = 2147483648


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
    if not isinstance(params, Mapping):
        raise TypeError("params must be a mapping of str to str")
    found = None
    for key, value in params.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise TypeError("params must be a mapping of str to str")
        if ascii_lower(str.__str__(key)) == name:
            found = str.__str__(value)
    return found
