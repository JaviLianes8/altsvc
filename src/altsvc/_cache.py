"""Freshness of an advertised alternative (RFC 7838 section 3.1)."""

from __future__ import annotations

from ._errors import AltSvcError
from ._model import Alternative


def expires_at(alternative: Alternative, received_at: float, *, age: int = 0) -> float:
    """The time after which the alternative is no longer fresh.

    ``received_at`` is when the response arrived, on any clock the caller uses, and
    ``age`` the response's age in seconds (its ``Age`` field). The lifetime is ``ma``, or
    86400 seconds without it, counted from when the response was generated.
    """
    if isinstance(age, bool) or not isinstance(age, int):
        raise TypeError("age must be an int number of seconds")
    if isinstance(received_at, bool) or not isinstance(received_at, (int, float)):
        raise TypeError("received_at must be a number")
    if age < 0:
        raise AltSvcError("age must not be negative", code="age.negative")
    return received_at + max(0, alternative.max_age - age)


def is_fresh(alternative: Alternative, received_at: float, now: float, *, age: int = 0) -> bool:
    """Whether a client may still open new connections to the alternative at ``now``."""
    return now < expires_at(alternative, received_at, age=age)
