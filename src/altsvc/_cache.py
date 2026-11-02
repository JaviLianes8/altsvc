"""Freshness of an advertised alternative (RFC 7838 section 3.1)."""

from __future__ import annotations

import math

from ._errors import AltSvcError
from ._model import Alternative


def expires_at(alternative: Alternative, received_at: float, *, age: int = 0) -> float:
    """The time after which the alternative is no longer fresh.

    ``received_at`` is when the response arrived, on any clock the caller uses, and
    ``age`` the response's age in seconds (its ``Age`` field). The lifetime is ``ma``, or
    86400 seconds without it, counted from when the response was generated.

    >>> from altsvc import Alternative, expires_at
    >>> expires_at(Alternative.of('h3', 443, ma=60), 100.0, age=30)
    130.0
    """
    if not isinstance(alternative, Alternative):
        raise TypeError("alternative must be an Alternative")
    if isinstance(age, bool) or not isinstance(age, int):
        raise TypeError("age must be an int number of seconds")
    received_at = _time(received_at)
    if age < 0:
        raise AltSvcError("age must not be negative", code="age.negative")
    return _time(received_at + max(0, alternative.max_age - age))


def is_fresh(alternative: Alternative, received_at: float, now: float, *, age: int = 0) -> bool:
    """Whether a client may still open new connections to the alternative at ``now``.

    >>> from altsvc import Alternative, is_fresh
    >>> is_fresh(Alternative.of('h3', 443, ma=60), 100.0, 160.0)
    False
    """
    return _time(now) < expires_at(alternative, received_at, age=age)


def _time(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("time must be an int or float")
    try:
        result = float(value)
    except OverflowError:
        raise AltSvcError("time must be finite", code="time.invalid") from None
    if not math.isfinite(result):
        raise AltSvcError("time must be finite", code="time.invalid")
    return result
