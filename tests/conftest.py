import itertools
from datetime import datetime

import pytest

from ligature.application.editor import Editor
from ligature.application.updates import UpdateService
from ligature.infrastructure.files import JsonDiagramFiles
from ligature.infrastructure.settings import MemorySettings

from .fakes import FakeInstaller, FakeReleases


@pytest.fixture
def editor():
    counter = itertools.count(1)
    return Editor(JsonDiagramFiles(), new_id=lambda: f"id{next(counter)}")


class Clock:
    def __init__(self):
        self.now = datetime(2026, 9, 30, 10, 0)

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def releases():
    return FakeReleases()


@pytest.fixture
def installer():
    return FakeInstaller()


@pytest.fixture
def services(editor, releases, installer, clock):
    from ligature.application.services import Services
    return Services(editor, UpdateService(releases, installer, MemorySettings(), "0.2.0", clock))


@pytest.fixture(scope="session", autouse=True)
def empty_clipboard():
    """Qt's headless test platform crashes at exit when the clipboard still holds data a
    test copied (real desktops don't), so empty it before the tests end."""
    yield
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        return
    app = QApplication.instance()
    if app is not None:
        app.clipboard().clear()
