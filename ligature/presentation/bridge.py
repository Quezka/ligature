"""Relays the editor's change notices to Qt signals, so views refresh on the UI thread."""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from ..application.editor import Change, Editor


class ChangeRelay(QObject):
    diagramChanged = Signal()
    documentChanged = Signal()

    def __init__(self, editor: Editor, parent=None):
        super().__init__(parent)
        editor.subscribe(self._relay)

    def _relay(self, change: Change):
        (self.diagramChanged if change is Change.DIAGRAM else self.documentChanged).emit()
