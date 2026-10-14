"""Read an Alt-Svc field value into alternatives or the clear token."""

from __future__ import annotations

from collections.abc import Sequence

from ._errors import AltSvcError
from ._lint import analyse
from ._model import CLEAR, Alternative, Clear


def parse(value: str | Sequence[str], *, strict: bool = False) -> list[Alternative] | Clear:
    """Read an Alt-Svc field value, or several field lines combined as one list.

    Returns :data:`CLEAR` when the value holds the ``clear`` token (section 3 of RFC 7838:
    it invalidates every alternative, even those next to it), otherwise the alternatives
    in the server's order of preference.

    With ``strict=True`` the first error raises :class:`AltSvcError` with its code and
    offset. The default tolerant mode keeps every alternative whose protocol-id,
    authority and ``ma`` are sound, and ignores broken parameters of other names; this is
    a robustness choice of this library, see :func:`lint` for what was skipped.
    """
    analysis = analyse(value)
    if strict and analysis.errors:
        first = analysis.errors[0]
        raise AltSvcError(first.message, code=first.code, offset=first.offset)
    return CLEAR if analysis.clear else analysis.alternatives
