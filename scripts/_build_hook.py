"""Keep version-control configuration out of source distributions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        # Hatchling force-includes these even when the sdist exclusion lists them.
        forced = build_data["force_include"]
        for path in list(forced):
            if Path(path).name in {".gitignore", ".gitattributes"}:
                forced.pop(path)
