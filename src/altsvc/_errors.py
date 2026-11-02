"""The error type and the finding type shared by the reader, the linter and the builder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Severity = Literal["error", "warning"]


class AltSvcError(ValueError):
    """Raised when a field value cannot be read strictly or a value cannot be built.

    ``code`` names the rule that failed (the same codes as :class:`Issue`), ``offset``
    is the index in the field value, or in the part being checked, where it failed, and
    ``message`` is the text without the offset.

    >>> from altsvc import AltSvcError
    >>> str(AltSvcError('invalid value', code='invalid', offset=2))
    'invalid value (at offset 2)'
    """

    def __init__(self, message: str, *, code: str = "invalid", offset: int | None = None) -> None:
        super().__init__(message if offset is None else f"{message} (at offset {offset})")
        self.message = message
        self.code = code
        self.offset = offset


@dataclass(frozen=True, slots=True)
class Issue:
    """One finding about an Alt-Svc field value.

    An ``error`` breaks RFC 7838 (its grammar or one of its MUSTs); a ``warning`` marks
    something legal that is likely a mistake.

    >>> from altsvc import Issue
    >>> Issue('empty', 'empty value', 'error', 0).severity
    'error'
    """

    code: str
    message: str
    severity: Severity
    offset: int | None = None
