"""The only place that knows which adapters implement which ports."""
from __future__ import annotations

from .application.editor import Editor
from .application.ports import DiagramFiles
from .application.services import Services
from .infrastructure.files import JsonDiagramFiles


def build_services(files: DiagramFiles | None = None) -> Services:
    return Services(editor=Editor(files or JsonDiagramFiles()))
