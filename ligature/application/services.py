"""Everything the UI can ask for, in one place (built by `bootstrap`)."""
from __future__ import annotations

from dataclasses import dataclass

from .editor import Editor
from .updates import AvailableUpdate, UpdateService


@dataclass
class Services:
    editor: Editor
    updates: UpdateService


__all__ = ["AvailableUpdate", "Services"]
