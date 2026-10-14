"""The error type and the finding type shared by the reader, the linter and the builder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Severity = Literal["error", "warning"]


class AltSvcError(ValueError):
    """Raised when a field value cannot be read strictly or a value cannot be built.

    ``code`` names the rule that failed (the same codes as :class:`Issue`) and ``offset``
    is the index in the field value, or in the part being checked, where it failed.
    """

    def __init__(self, message: str, *, code: str = "invalid", offset: int | None = None) -> None:
        super().__init__(message if offset is None else f"{message} (at offset {offset})")
        self.code = code
        self.offset = offset


@dataclass(frozen=True, slots=True)
class Issue:
    """One finding about an Alt-Svc field value.

    An ``error`` breaks RFC 7838 (its grammar or one of its MUSTs); a ``warning`` marks
    something legal that is likely a mistake.
    """

    code: str
    message: str
    severity: Severity
    offset: int | None = None
