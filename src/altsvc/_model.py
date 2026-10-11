"""Data model for Alt-Svc alternatives and the clear token."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AltSvcError(ValueError):
    """Raised when a value cannot be built into a valid Alt-Svc header."""


class Clear(Enum):
    """The ``clear`` token, which invalidates every previously announced alternative."""

    CLEAR = "clear"


CLEAR = Clear.CLEAR


@dataclass
class Alternative:
    """One Alt-Svc alternative: a protocol id, its authority and extra parameters."""

    protocol: str
    authority: str
    params: dict[str, str] = field(default_factory=dict)

    @property
    def ma(self) -> int | None:
        """The ``ma`` (max-age) parameter in seconds, or ``None`` when it is absent."""
        value = self.params.get("ma")
        return int(value) if value is not None and value.isdigit() else None

    @property
    def persist(self) -> bool:
        """Whether ``persist=1`` asks clients to keep the alternative across network changes."""
        return self.params.get("persist") == "1"
