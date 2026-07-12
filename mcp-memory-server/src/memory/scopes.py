"""Memory scope validation shared by storage and API layers."""

from dataclasses import dataclass
import re
from typing import Literal

_REPOSITORY_ID = re.compile(r"^[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}$")


@dataclass(frozen=True)
class MemoryScope:
    scope_type: Literal["core", "repository"] = "core"
    scope_id: str = "core"

    def __post_init__(self) -> None:
        if self.scope_type == "core" and self.scope_id != "core":
            raise ValueError("Core memories must use the core scope ID.")
        if self.scope_type == "repository":
            parts = self.scope_id.split("/")
            if not _REPOSITORY_ID.fullmatch(self.scope_id) or any(part in {".", ".."} for part in parts):
                raise ValueError("Repository scope IDs must use owner/repository format.")
        if self.scope_type not in {"core", "repository"}:
            raise ValueError("Unsupported memory scope type.")
