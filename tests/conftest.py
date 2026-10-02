import itertools
import os
from datetime import datetime

import pytest

os.environ.setdefault("QT_SCALE_FACTOR", "1")  # tests measure pixels: no automatic scaling

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


@pytest.fixture(autouse=True)
def full_hd_screen(monkeypatch):
    """The headless test screen is tiny; windows are clamped to the screen, so pretend it is
    a normal one (the clamp itself is tested in test_uiscale)."""
    try:
        from PySide6.QtCore import QRect
        from ligature.presentation import fit
    except ImportError:
        return
    monkeypatch.setattr(fit, "available", lambda widget=None: QRect(0, 0, 1920, 1040))
