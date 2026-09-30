"""The only place that knows which adapters implement which ports."""
from __future__ import annotations

from . import HOMEPAGE, __version__
from .application.editor import Editor
from .application.ports import DiagramFiles, KeyValueStore, ReleaseFeed, UpdateInstaller
from .application.services import Services
from .application.updates import UpdateService
from .infrastructure.files import JsonDiagramFiles
from .infrastructure.settings import JsonSettings
from .infrastructure.updates import GitHubReleaseFeed, platform_installer


def build_services(files: DiagramFiles | None = None, settings: KeyValueStore | None = None,
                   releases: ReleaseFeed | None = None,
                   installer: UpdateInstaller | None = None) -> Services:
    return Services(
        editor=Editor(files or JsonDiagramFiles()),
        updates=UpdateService(
            releases or GitHubReleaseFeed(HOMEPAGE.removeprefix("https://github.com/"),
                                          __version__),
            installer or platform_installer(), settings or JsonSettings(), __version__),
    )
